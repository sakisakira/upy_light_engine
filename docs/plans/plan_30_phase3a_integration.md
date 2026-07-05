# Phase 3A: Python API Integration & Real Device Testing

## 課題
実機でのテストに向けて、Python側の `engine` を新しい `_lightengine` Cモジュールに繋ぎ込む必要があります。
しかし、現在のPhase 3までの実装には以下の課題が残っています。

1. **バッファの確保問題**: 
   現在の `_lightengine.Image` と `_lightengine.Framebuffer` は、Cの内部で独自にメモリを確保する仕様になっています。これではPython側から画像のピクセルデータをロードしたり、SPI経由でディスプレイにデータを転送したりすることができません。
   （Pythonの `bytearray` をそのままC側から触れるようにする必要があります）

2. **同期処理（同期ずれ防止）**:
   `submit_display_list()` は Core 1 に描画を依頼して即座に終了しますが、Python側がその直後に「SPIへのデータ送信（ディスプレイ更新）」を行ってしまうと、Core 1 がまだ描画している途中の「描きかけの画面」がディスプレイに送られてしまい、画面が崩れたりチラついたりします。

## 解決策

### 1. `modlightengine.c` のバッファ連携対応
`Image` と `Framebuffer` の初期化関数（`make_new`）を変更し、Pythonから `bytearray` を渡す仕様に変更します。
これにより、Python側で画像のロード（`f.readinto`）やディスプレイへの送信（SPI DMA転送）がそのまま行えるようになります。

### 2. 同期機構 (`sync`) の追加
`_lightengine.sync()` という関数を新設します。
内部で `pending_render_jobs` をカウントし、Core 1 での描画が完全に終わるのを待ってから処理を戻すようにします。
Python側は `submit_display_list()` を投げたあと、ディスプレイに送信する直前に `_lightengine.sync()` を呼びます。

### 3. Python API (`engine/*.py`) の更新
- `engine/image.py`: `_lightengine.Image(w, h, format, self.data)` を保持。
- `engine/sprite.py`: `_lightengine.Sprite` を保持し、`u, v, w, h` は直接C拡張のプロパティにアクセスするよう委譲。
- `engine/hal/framebuffer_micropython.py`: 描画処理をすべて `DisplayList` の `push_*` メソッド群に置き換え。メインループの最後に `submit_display_list()` と `sync()` を実行するように変更。

### 4. ビルドと実機テスト
- 再度Cモジュールをコンパイル (`scripts/build_c_module.ps1`)。
- 実機へのファームウェアの書き込み。
- 実機での `main.py` の実行とFPS検証。
