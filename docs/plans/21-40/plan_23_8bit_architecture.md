# Cardputer メモリ不足 解消計画 (8-bit パレットアーキテクチャへの移行)

## 関連調査資料
詳細なメモリ計算と8-bit化の正当性の証明については、以下の調査資料を参照してください：
[Cardputer メモリ限界調査と 8-bit アーキテクチャ移行の必要性](../investigation/memory_limitations_and_8bit_arch.md)

## Goal Description
Cardputer Adv での致命的なメモリ不足（`MemoryError`）を解消するため、エンジンの描画系とアセット管理を 16-bit (ARGB4444) から **8-bit パレット方式 (256色 / INDEX8)** へと完全移行します。
これにファームウェア設定の修正を合わせることで、メモリ消費量を劇的に抑え、Cardputer の小さな内部SRAM（約130KB）でも多数のスプライトを快適に処理できる「レトロゲーム特化の軽量エンジン」へと生まれ変わらせます。

## User Review Required
> [!IMPORTANT]
> この計画では画像アセットやフォントのフォーマットが根本から変わるため、既存の `.uimg` / `.afnt` はすべて再生成されます。
> * **ARGB4444とαチャンネルの完全廃止**: 画像(`Image`)やスプライト(`Sprite`)の管理はすべて `INDEX8` (1バイトのパレットインデックス) となり、αチャンネルによる半透明合成機能は廃止されます。
> * **パレットの共通化とカラー操作APIの追加**: すべてのPNG画像から共通の256色パレット（`palette.bin`）が自動生成されます。さらに、Pyxelの `pyxel.colors` のように、**実行中にパレットの任意の色を書き換えられるAPI** を提供します。これにより「画面全体のフェードアウト」や「ダメージ時の点滅」などがパレット操作だけで一瞬で行えるようになります。
> * **透過色**: `Sprite` のコンストラクタ引数で `colkey`（透過色とするインデックス）を指定できるようにします（デフォルトは `0`）。
> * **フォントの描画**: フォントも8-bit形式になります。指定した文字色（インデックス）で描画されるよう、エンジン側の描画ロジックを最適化します。

## Open Questions
* 特になし（ツール側で自動的に最適な共通パレットを抽出する仕様とします）。

## Proposed Changes

### 1. ファームウェアのビルド設定修正 (ヒープ回復)
#### [MODIFY] upy_light_engine/scripts/build_c_module.ps1
* `make` コマンドの引数から `BOARD_VARIANT=SPIRAM_OCT` を削除します。これによりPSRAM用の無駄なメモリ予約が解除され、MicroPythonヒープが **約64KB → 約130KB** へ倍増します。

### 2. 8-bit 用アセット変換ツールの開発
#### [NEW] upy_light_engine/tools/convert_assets.py
* 従来の `png2uimg.py` に代わり、ディレクトリ内の全PNG画像をスキャンするツールを作成します。
* 全画像から使われている色を最大256色抽出し、共通パレット `palette.bin` (24-bit RGB または RGB565形式) を生成します。
* その後、各画像をパレットのインデックス値（1バイト/ピクセル）に変換し、8-bitの `.uimg` フォーマットとして保存します。

#### [MODIFY] upy_light_engine/tools/ttf2afnt.py
* フォントデータも 16-bit (ARGB4444) ではなく 8-bit (INDEX8, 1バイト/ピクセル) で書き出すように修正します。（RAM消費半減）

#### [MODIFY] motorcycle_cardputer/tools/build.ps1
* アセット変換時に新ツール `convert_assets.py` を呼び出し、`palette.bin` と `.uimg` を生成するように書き換えます。

### 3. エンジンの 8-bit 化改修 と カラーAPI
#### [NEW] upy_light_engine/engine/palette.py (または engine.colors)
* `engine.colors` リストを提供します。`engine.colors[1] = 0xFF0000` のように、ユーザーが実行時にパレットの色を書き換えられるようにします。（内部で自動的にRGB565に変換され、ST7789転送時に反映されます）

#### [MODIFY] upy_light_engine/engine/image.py & engine/sprite.py
* `ARGB4444` を完全に廃止し、フォーマットを `INDEX8` に統一します。
* 読み込み時にヘッダフォーマットを認識し、1ピクセル＝1バイトの `bytearray` をロードするようにします。
* エンジン起動時にパレットファイル `palette.bin` を静的にロードし、`engine.colors` の初期値として設定する処理を追加します。

#### [MODIFY] upy_light_engine/engine/hal/software_renderer.py / framebuffer_micropython.py
* フレームバッファのサイズを `width * height` バイト（1ピクセル=1バイト）に変更します（64.8KB → 32.4KB）。
* `blt` や `sprite` の描画処理からαチャンネル合成（ブレンド計算）を完全に削除し、「透過色(colorkey)でなければ 8-bitインデックスを直接コピーする」単純なピクセル置換処理に置き換えます。これによりViper処理が劇的に高速化します。
* フォントの描画用に、指定した色（インデックス）で塗る `blt_tint` 処理を組み込みます。

#### [MODIFY] upy_light_engine/engine/hal/st7789.py
* `display.show()` 呼び出し時に、8-bitのフレームバッファをライン単位で `engine.colors` に基づいて 16-bit (RGB565) に変換しながら SPI 送信する処理を実装します。

## Verification Plan
### Automated Tests
* 特になし

### Manual Verification
1. `motorcycle_cardputer/tools/build.ps1` を実行し、`palette.bin` と 新形式の `.uimg` が生成されることを確認。
2. `upy_light_engine/scripts/build_c_module.ps1` でファームウェアを再ビルドし、Cardputerへ書き込む。
3. `install_to_cardputer.ps1` でアセット類（`palette.bin` 含む）とスクリプトを転送。
4. `run_on_cardputer.ps1` を実行し、メモリ不足で落ちることなくゲームが起動し、正しい色で描画されるか確認する。
5. `engine.colors` を書き換えて、画面の色が即座に反映されるかを検証する。
