# [Goal Description]
Cardputer Adv向け バックグラウンドサウンドCモジュールの実装

純粋なMicroPythonのI2S+I2C実装では、バッファサイズの制約（ENOMEM）や、Pythonのメインループからのバッファ供給の遅延によって正常に音が鳴らないことが確認されました。
そこで、ESP-IDFのI2SドライバとFreeRTOSタスクを活用し、Pythonのメインループをブロックすることなくバックグラウンドで音声を非同期生成・再生するCモジュールを作成します。

## User Review Required
> [!IMPORTANT]
> Cモジュール化することで、**Python側から `play_tone(freq, duration)` を呼ぶだけで、裏でC言語（FreeRTOSタスク）が波形を生成し続ける** ため、ゲームの処理落ちに関わらず綺麗な音が鳴るようになります。
>
> 以下のアーキテクチャ案で問題ないか、レビューをお願いします！

## Open Questions
- **[解決済]** ES8311の細かいレジスタ設定やピンアサインについて：
  - I2Sピン: BCLK=41, WS=43, DOUT=42
  - I2Cピン: SDA=8, SCL=9
  - アンプ(NS4150B)の有効化はES8311のレジスタ経由で行われ、専用のGPIOピンは使用しません。
  - これらの設定値をC言語モジュール（`sound_engine.c`）にハードコードしてビルドしました。

## Proposed Changes

### 1. Cモジュールの作成

ESP32 (ESP-IDF v5) 向けのMicroPythonユーザーCモジュールとして実装します。

#### [NEW] [c_modules/sound_engine/micropython.cmake](file:///d:/sakira/work/cardputer/upy_light_engine/c_modules/sound_engine/micropython.cmake)
Cモジュールのビルド設定ファイル。`sound_engine.c` をコンパイル対象として登録します。

#### [NEW] [c_modules/sound_engine/sound_engine.c](file:///d:/sakira/work/cardputer/upy_light_engine/c_modules/sound_engine/sound_engine.c)
C言語による実装本体。以下の機能を提供します：
- **`init()`**: ESP-IDFの `i2c_master` APIを用いてES8311コーデックを初期化し、`i2s_channel` APIを用いてI2Sをセットアップします。
- **`play_tone(freq, duration_ms)`**: 指定された周波数と時間を内部変数にセットします。
- **FreeRTOSタスク (`sound_task`)**: バックグラウンドで常に稼働し、設定された周波数に基づいて矩形波（または正弦波）を生成し、I2SのDMAバッファに連続して書き込みます。指定時間が経過したら無音データを書き込みます。

### 2. ビルドスクリプトの更新

#### [MODIFY] [build_c_module.ps1](file:///d:/sakira/work/cardputer/upy_light_engine/build_c_module.ps1)
Cモジュールを含めてMicroPythonファームウェア全体をビルドするようにコマンドを追記します。
```powershell
make -C micropython/ports/esp32 USER_C_MODULES=/workspace/c_modules/micropython.cmake BOARD=ESP32_S3
```
※ボードの指定は適宜調整します。

### 3. HALの更新

#### [MODIFY] [hal/sound_micropython.py](file:///d:/sakira/work/cardputer/upy_light_engine/hal/sound_micropython.py)
公式のM5モジュールが見つからない場合、新しく作成したCモジュール（`import _sound_engine`）を呼び出すようにフォールバック処理を書き換えます。これにより、Python側でバッファを生成する処理（`update()`での流し込み等）が不要になります。

## Verification Plan

### Automated Tests
Cモジュールを含むため、PC上のpytest等ではモックを使用します。

### Manual Verification (Pending User Test)
1. **[完了]** `build_c_module.ps1` を実行し、Cモジュールが組み込まれた新しいファームウェア（`micropython.bin`）が生成されました。
2. 生成されたファームウェアをCardputer ADVに書き込みます。
3. REPLから `import _sound_engine; _sound_engine.test_sound()` を実行し、スピーカーからクリアな音が鳴ることを確認します。
