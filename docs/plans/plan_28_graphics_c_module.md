# [Goal Description]
Cardputer Adv向け グラフィックエンジンのネイティブモジュール化（`.mpy`）

プロファイリングの結果、テキスト描画（52ms）とパレット変換（37ms）におけるPythonのループとコンテキストスイッチが限界であることが証明されました。
ファームウェアの書き換えをユーザーに要求することなく、この限界を突破して30FPS（1フレーム33ms以内）を達成するため、**MicroPythonのダイナミック・ネイティブモジュール機能（dynruntime）** を用いて C言語で高速化した `graphics_engine.mpy` を実装します。

## User Review Required
> [!IMPORTANT]
> - ファームウェアを書き換えることなく、ゲームのフォルダに `graphics_engine.mpy` を置くだけで超高速化が有効になります！
> - `dynruntime.h` の制約を回避するため、文字列のフォントインデックス変換はPython側で行い、Cモジュールには「インデックスの配列」を渡す設計に変更しました（これでGCアロケーションゼロを維持しつつ限界まで高速化できます）。
>
> 以下の新しいアーキテクチャ案で問題ないか、レビューをお願いします！

## Open Questions
- 特になし（事前検討で課題はすべてクリアされました）。

## Proposed Changes

### 1. ダイナミック・ネイティブモジュール（.mpy）の作成

MicroPythonのリポジトリの `py/dynruntime.h` を利用し、Cardputer（ESP32-S3）のアーキテクチャ `xtensawin` 向けにコンパイルします。

#### [NEW] [c_modules/graphics_engine/Makefile](file:///d:/sakira/work/cardputer/upy_light_engine/c_modules/graphics_engine/Makefile)
ダイナミック・ネイティブモジュールのビルド用Makefile。
`ARCH = xtensawin` を指定し、MicroPython公式の `dynruntime.mk` をインクルードします。

#### [NEW] [c_modules/graphics_engine/graphics_engine.c](file:///d:/sakira/work/cardputer/upy_light_engine/c_modules/graphics_engine/graphics_engine.c)
C言語による実装本体。以下の3つの関数をPythonに公開します（引数は全て `mp_obj_t` で受け取り、内部でポインタや整数に変換します）。
1. **`convert_palette_chunk(src_buf, src_offset, dst_chunk, pal_buf, num_pixels)`**
   - 画面バッファ（INDEX8）の一部をRGB565チャンクバッファに変換。ポインタ演算のみのため1ms未満で完了します。
2. **`draw_sprite(dst_buf, dst_w, dst_h, src_buf, src_w, src_h, u, v, w, h, cx, cy, min_x, max_x, min_y, max_y, cos_inv_fp, sin_inv_fp, colkey, tint)`**
   - ViperのDDAスプライト描画のC言語版。回転・拡縮・単なるblt描画を全てカバーします。
3. **`draw_text_indices(dst_buf, dst_w, dst_h, font_buf, font_w, char_w, char_h, cols, indices_buf, text_len, x, y, tint)`**
   - Python側で文字コードから画像インデックス（0〜）に変換された配列（`indices_buf`）を受け取り、一気にバッファへ文字を描き込みます。

### 2. HALの更新（.mpyの利用とZero-Allocation Pythonループ）

#### [MODIFY] [engine/hal/st7789.py](file:///d:/sakira/work/cardputer/upy_light_engine/engine/hal/st7789.py)
ネイティブモジュール `graphics_engine` をインポートし、`convert_palette_chunk` を呼び出すように変更。

#### [MODIFY] [engine/hal/framebuffer_micropython.py](file:///d:/sakira/work/cardputer/upy_light_engine/engine/hal/framebuffer_micropython.py)
Viper関数を廃止し、`draw_sprite` と `draw_text_indices` に委譲します。
テキスト描画においては、**エンジン初期化時に確保した `array.array('h', [-1]*256)` のバッファを使い回し**、Python側で `indices_buf[i] = font.char_map.get(...)` のようにインデックスを詰め込んでからC関数に渡します（GCアロケーションゼロ！）。

### 3. ビルドスクリプトの更新

#### [NEW] [scripts/build_graphics_mpy.ps1](file:///d:/sakira/work/cardputer/upy_light_engine/scripts/build_graphics_mpy.ps1)
Windows環境上で（またはDocker等を利用して）`make` を叩き、`graphics_engine.mpy` を生成するスクリプトを作成します。

## Verification Plan

### Automated Tests
実機環境向けバイナリ（`xtensawin`）となるため、PC上のテストはモックに切り替えます。

### Manual Verification
1. `build_graphics_mpy.ps1` を実行し、`graphics_engine.mpy` を生成。
2. `graphics_engine.mpy` と関連ファイルをCardputer ADVにコピー（ファームウェア更新は不要）。
3. エンジンのプロファイリング用 `main.py` を実行し、`draw_text` と `display_show` の時間が劇的に短縮され、ついに **30 FPS** が安定して出ること（約33ms/フレーム）を確認します！
