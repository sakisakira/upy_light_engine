# Sprite APIの導入 (エンジン側実装)

## Goal
エンジンの高レベル描画APIとして `Sprite` クラスと `fb.screen.sprite()` 関数を実装します。

## 概要
Cardputer AdvおよびPC(Windows/WASM)向けゲームエンジンの描画機能拡充として、回転・拡縮の中心座標を基準として描画を行うための機能を追加します。将来的にC拡張モジュールでの実装を見越して、まずはピュアPythonで動作するフォールバック版を作成します。
なお、このステップでは回転(`rotate`)は実装を省略し、0固定(回転なし)として扱います。実際の回転処理は別のステップに分けます。

## Proposed Changes

### [NEW] engine/sprite.py
* `Image` への参照、切り出し領域(`u, v, w, h`)、`colkey`、`tint` を保持する `Sprite` クラスを新設します。
* `tint` はパレット置換や色変換を想定しますが、今回の初期実装では保持するのみ（あるいは未対応）とします。

### [MODIFY] engine/image.py
* `Sprite` クラスを生成しやすくするためのヘルパーメソッド `def subimage(self, u, v, w, h, colkey=-1, tint=None):` を追加します。

### [MODIFY] engine/hal/framebuffer_cpython.py
### [MODIFY] engine/hal/framebuffer_wasm.py
### [MODIFY] engine/hal/framebuffer_micropython.py
* 各フレームバッファクラスに `def sprite(self, cx, cy, spr, rotate=0.0, scale=1.0):` を追加します。
* 引数 `rotate` はこのステップでは無視し、`rotate=0` 相当で処理します（実際の回転対応は別ステップに分割）。
* 引数 `scale` は浮動小数点数での拡縮率（アスペクト比維持）とします。
* `blt` のように左上座標ではなく、**中心座標 (`cx`, `cy`) を基準に描画** します。
* ピュアPython実装によるニアレストネイバー法での単純なスケール計算（逆マッピング）を行い、ピクセル単位で書き込みを行う処理として実装します。

### [MODIFY] main.py
* エンジンのテスト用エントリポイントである `main.py` を修正し、`Image` ではなく `subimage` メソッドを用いて `Sprite` を生成し、`fb.screen.sprite` を使って描画するように変更します。

## Verification Plan
### Automated Tests
* エンジン単体での動作確認用に、適当な画像をロードして回転・拡縮描画を行うテストスクリプト(`tests/tmp/test_sprite.py`)を作成し、実行して結果を確認します。

### Manual Verification
* 作成したテストスクリプトを実行し、画像が正しく中心基準で回転・拡縮されているかをPC上で目視確認します。
