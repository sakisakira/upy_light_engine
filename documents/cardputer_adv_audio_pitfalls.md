# Cardputer Adv サウンド実装における「ハマりポイント」まとめ

本プロジェクトにおいて、Cardputer Adv のスピーカーから音を鳴らすまでに直面した技術的な問題と、その解決に至るまでのハマりポイントを列挙します。将来的な同種デバイスの対応やデバッグの際の知見として記録します。

## ハマりポイント1: 無印版とAdv版でオーディオICが全く違う
一番最初の調査で最も大きな罠となったのが、初代（無印）CardputerとCardputer-Advにおけるハードウェアの劇的な変更でした。

* **無印版 Cardputer**: スピーカー駆動に I2Sデジタルアンプ `NS4168` を直接使用。(BCLK=41, LRCK=43, DATA=42)
* **Cardputer-Adv**: I2S/I2Cオーディオコーデック `ES8311` を経由してアナログアンプ `NS4150B` を駆動。

「Cardputerの音の鳴らし方」で検索して出てくる過去の情報の多くは `NS4168` を前提としており、I2Sのピンアサインと初期化不要という仕様に引きずられ、I2C経由でのコーデック初期化を見落とす原因となりました。

## ハマりポイント2: ネット上の不正確なピンアサイン情報
ES8311を使用していることに気付いた後、ピンアサインを調査した際、ネット上の一部コミュニティやまとめ記事に以下のような誤った情報が記載されていました。

* **誤情報**: `I2S DAC_SDIN (DATA) = GPIO 46`, `Amp Enable (AMP_EN) = GPIO 42`

これに基づき、GPIO 42 をアンプのON/OFFピンとしてHIGHにし、GPIO 46 にI2Sデータを出力するプログラムを書いた結果、**「実行直後に『ぷつっ』と鳴り、その後は完全に無音になる」**という現象が発生しました。

* **真相**: 実際には `I2S_DATA = GPIO 42` であり、`AMP_EN` ピンは存在しませんでした。
これは M5Stack 公式ライブラリである `M5Unified` のソースコード (`M5Unified/src/M5Unified.cpp` L2403-L2409付近) を直接確認したことで判明しました。

> **[引用] M5Unified.cpp (スピーカー設定部分)**
> ```cpp
>       case board_t::board_M5Cardputer:
>       case board_t::board_M5CardputerADV:
>         if (cfg.internal_spk)
>         {
>           spk_cfg.pin_bck = GPIO_NUM_41;
>           spk_cfg.pin_ws = GPIO_NUM_43;
>           spk_cfg.pin_data_out = GPIO_NUM_42; // ここで42番ピンがI2S_DATAであることが確定
> ```

GPIO 42を `AMP_EN` だと思い込んでDC 3.3V（HIGH）に固定してしまったため、ES8311のデータピンに「1が連続するデータ（巨大な直流オフセット）」が流れ込み、それがアナログアンプで増幅されて一瞬だけ「ぷつっ」というポップノイズ（DCポップ）として聞こえていました。データピンがHIGHに固定されていたため、その後ろで何を送信しても無音になるという最悪のコンボでした。

## ハマりポイント3: MCLK（マスタークロック）の欠如
ES8311は内部のPLLをロックさせるためにマスタークロック（MCLK）を必要としますが、ESP32-S3のデフォルトのI2S構成ではMCLKを出力するピンが配線されていませんでした。

* **解決策**: MCLKが外部から供給されない場合、ES8311のレジスタ `0x01` に `0xB5` (または `0xBF`) を書き込み、「**BCLKからMCLKを内部生成する（MCLK=BCLKモード）**」設定を有効にする必要がありました。これを怠ると、チップは正常に起動しているように見えてもDACが一切動作しません。

## ハマりポイント4: ES8311の複雑なレジスタ構成
`MCLK=BCLK` モードを有効にしただけでは音は鳴りませんでした。ES8311は初期状態ではクロックのマルチプライヤ（倍率）が適切に設定されておらず、またDAC出力ルーティングもミュート状態に近い設定になっています。

* **解決策**: M5Stack公式の `M5Unified` ソースコード (`M5Unified/src/M5Unified.cpp` の `_speaker_enabled_cb_cardputer_adv` メソッド, L788-L801付近) にハードコードされている**門外不出の初期化配列**（以下）を完全にトレースする必要がありました。

> **[引用] M5Unified.cpp (_speaker_enabled_cb_cardputer_adv メソッド)**
> ```cpp
>   bool M5Unified::_speaker_enabled_cb_cardputer_adv(void* args, bool enabled)
>   {
>     // ... (略) ...
>     static constexpr const uint8_t enabled_bulk_data[] = {
>       2, 0x00, 0x80,  // 0x00 RESET/  CSM POWER ON
>       2, 0x01, 0xB5,  // 0x01 CLOCK_MANAGER/ MCLK=BCLK (ハマりポイント3の解決)
>       2, 0x02, 0x18,  // 0x02 CLOCK_MANAGER/ MULT_PRE=3
>       2, 0x0D, 0x01,  // 0x0D SYSTEM/ Power up analog circuitry
>       2, 0x12, 0x00,  // 0x12 SYSTEM/ power-up DAC - NOT default
>       2, 0x13, 0x10,  // 0x13 SYSTEM/ Enable output to HP drive - NOT default
>       2, 0x32, 0xBF,  // 0x32 DAC/ DAC volume (0xBF == ±0 dB )
>       2, 0x37, 0x08,  // 0x37 DAC/ Bypass DAC equalizer - NOT default
>       0
>     };
> ```

ここで `0x01, 0xB5` (MCLK=BCLK) が設定されていることや、データシートのデフォルト値とは異なる `0x02, 0x18` (MULT_PRE=3) や `0x13, 0x10` (HPドライブ有効化) が必須であることが確定しました。

これらをすべて組み合わせることで、初めて「PythonからI2S経由でピーッというサイン波を鳴らす」ことに成功しました。

## 教訓
* デバイスの「無印版」と「Pro/Adv版」では、内部アーキテクチャが根本から変更されている可能性を常に疑う。
* ピンアサインの情報は、第三者の記事ではなく、最終的には公式のハードウェアライブラリ（`M5Unified` 等）のソースコードを直接読んで一次ソースを確認するべきである。
* 「ぷつっ」というポップノイズが出た時は、アンプがONになった証拠であると同時に、「オーディオデータラインに予期せぬDCオフセット（直流）がかかっている」可能性を強く疑うべきである。
