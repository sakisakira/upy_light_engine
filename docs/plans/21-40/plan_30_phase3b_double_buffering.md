# Plan 3B: 回転処理の復旧・最適化およびダブルバッファリングの実装

## 目標 (Goal Description)
スプライトの回転機能が失われている問題の修正と、フレームレートが28 FPSで頭打ちになっているパフォーマンス問題の根本的解決を行います。
具体的には以下の3点を実施します：
1. `framebuffer_micropython.py` に `rotate` 引数を復旧し、C言語コアまで角度情報を伝達できるようにします。
2. `engine_render.c` において、スプライトの2D回転描画処理を再実装します。この際、描画のインナーループ内で高コストな乗算処理を避けるため、DDA (Digital Differential Analyzer) アルゴリズムを用いた高速なピクセルマッピングを実装します。
3. ピクセルバッファ (`bytearray`) のダブルバッファリングを実装し、Core 0 がSPI転送 (`display.show()`) を行っている裏で、Core 1 が同時に次のフレームの描画を実行できるようにアーキテクチャを改良します。

## レビュー事項 (User Review Required)
特に破壊的な変更はありません。空きメモリにはまだ約50KB以上の余裕があり、追加のピクセルバッファ（約32KB）を確保しても問題なく動作します。

## 提案する変更内容 (Proposed Changes)

### C言語エンジンコア (Core Engine)
- `engine_types.h` の `RenderCommand.draw_sprite` に `float angle` を追加します。
- `engine_types.c` および `engine_render.h` の `dl_push_draw_sprite` の引数に `angle` を追加します。
- `modlightengine.c` の `dl_meth_push_draw_sprite` を修正し、Python側から渡される `angle` を解析します。
- `engine_render.c` の `render_draw_sprite` を修正：
  - `cosf` と `sinf` を用いて回転行列の逆行列 (`cos_inv_fp`, `sin_inv_fp`) を計算します。
  - インナーループ内での乗算を排除し、DDAによる加算のみでテクスチャ座標 (`sx_fp`, `sy_fp`) を進めるよう最適化します。

### ハードウェア抽象化レイヤー (HAL / Python)
- `framebuffer_micropython.py` の修正：
  - `sprite` メソッドが `rotate` 引数を受け取り、`push_draw_sprite` に渡すよう修正します。
  - `screen.buffers = [bytearray, bytearray]` と `screen._c_fbs` を定義し、2つの物理フレームバッファを保持します。
  - メインループ内で、`dls[1 - dl_idx]` を `buffers[1 - buf_idx]` に対してレンダリングするよう指示し、その直後に前回のバッファ `buffers[buf_idx]` を `display.show()` でSPI転送するように処理順序を組み替えます。

## 検証計画 (Verification Plan)
1. Cモジュールを再コンパイルします。
2. ファームウェアをCardputerに書き込みます (`flash_firmware.ps1`)。
3. `run_on_cardputer.ps1` を実行します。
4. 画面上で三角形のスプライトが回転していること、およびFPSが60に近い数値を示すことを確認します。
