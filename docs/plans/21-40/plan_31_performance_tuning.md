# Plan 31: Phase 3.5 Pythonロジックの最適化とC文字描画の導入 (Performance Tuning)

Phase 4 (Motorcycle移植) へ進む前に、現在のアーキテクチャ（描画・音響はC、ロジックはPython）で 60FPS を安定して達成できることを `main.py` を通じて証明し、ゲーム開発におけるベストプラクティスを確立します。

## 背景と課題 (Background)
先のプロファイリングによって、以下のボトルネックが判明しています。
1. **テキスト描画 (4.5ms)**: Pythonの `for` ループで1文字ずつスプライトAPIを呼んでいるため非常に遅い。
2. **浮動小数点演算 (2-4ms)**: 毎フレーム `math.sin` 等の float 演算を行うと、MicroPython環境では致命的な遅延となる。

## 目的 (Goal)
これらのボトルネックを解消し、`main.py` で安定した 60FPS を達成する。

---

## 提案する変更内容 (Proposed Changes)

### 1. C言語エンジン側への `draw_text` の移植
文字列を一括でCエンジン側に渡し、C言語ループ内で高速にディスプレイリストに積む関数 `push_draw_text` を新設します。

#### [MODIFY] `c_modules/core/engine_types.c/h`, `engine_render.c/h`
- 新たなコマンド定義 `kCmdDrawText` を追加。
- `DisplayList` に `push_draw_text(x, y, font_img, char_w, char_h, cols, text_str, color)` を追加。
- `render_task` 内で、受け取った文字列をパースしてスプライト描画と同等の処理を一括で行うロジックを実装。

#### [MODIFY] `c_modules/port_micropython/modlightengine.c`
- `DisplayList` オブジェクトに `push_draw_text` メソッドをバインドし、Python側から文字列（`bytes`）を渡せるようにする。

#### [MODIFY] `engine/hal/font.py`, `engine/hal/framebuffer_micropython.py`
- Pure Pythonの `for` ループ描画処理を削除し、`fb.screen.text` からCモジュールの `push_draw_text` を一発で呼び出すように改修。

---

### 2. `main.py` における浮動小数点演算の削減 (Float Reduction via LUT)
ゲームループ内で `math.sin` を毎フレーム計算するのをやめ、起動時に「ルックアップテーブル (LUT)」を事前生成しておく手法（ベストプラクティス）を導入します。

#### [MODIFY] `main.py`
- 初期化時に `BREATH_SCALE_TABLE` や `ROTATION_TABLE` をリストとして事前計算する。
- `draw_sprites()` 内では `math.sin(frames * 0.1)` の代わりに `scale = BREATH_SCALE_TABLE[frames % len(BREATH_SCALE_TABLE)]` といった「整数インデックスによる配列アクセス」に変更し、計算コストをゼロにする。

---

### 3. `main.py` における `@micropython.viper` の活用実証
Phase 4での物理演算や大量オブジェクト処理を見据え、`main.py` のロジックの一部を `viper` 化して速度を稼ぐサンプルを構築します。

#### [MODIFY] `main.py`
- `draw_rects` や `update` のようなループ処理において、ローカル変数の型ヒント（`int`）や `viper` デコレータを適切に付与し、ネイティブコードへコンパイルさせて高速化する。

---

## 期待される成果
この最適化によって `main.py` 全体が 60FPS (16ms以内) で余裕を持って動作すれば、「描画はC、ロジックはuPy」のアーキテクチャのまま本格的なゲーム開発（Phase 4）に踏み切れる判断材料となります。
