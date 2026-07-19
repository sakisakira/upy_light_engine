# Software Renderer (blt / sprite) コードの共通化

## Context
Sprite API (plan_19) を実装する過程で、CPython, WASM, MicroPythonの3つのHAL間で `sprite` および `blt` のピュアPython実装のコード重複が顕著になりました。
今後の保守性向上と、バグ修正（縮小時の描画欠け修正など）を1箇所で行えるようにするため、plan_19 の派生タスクとしてこの plan_20 を実施し、描画ロジックの共通化を行いました。

## Goal
3つの `Framebuffer` HALクラスで生じている描画ロジックの重複を解消し、1箇所で保守・最適化できるようにリファクタリングします。
また、**`sprite()` の入力元は `Image` (ARGB4444) に限定できる** という仕様に基づき、不要な分岐を削減してシンプル化します。

## 概要
現在、`blt` メソッドと実装された `sprite` メソッドは、ピクセル単位のクリッピングやアルファブレンド、ニアレストネイバーでの拡縮といった複雑な処理を行っていますが、ほぼ同じコードが3つのHALファイルにコピー＆ペーストされた状態になっています。
唯一の差異は「書き込み先のバッファ形式（CPython/WASMは `_mv` への代入でOK、MicroPythonはビッグエンディアンに変換して `buffer` に直接書き込む）」という点です。
これを解決するため、共通のソフトウェアレンダラー関数を別ファイルに抽出し、各HALはそこへ委譲する形を取ります。

## Proposed Changes

### [NEW] engine/hal/software_renderer.py
* 共通の描画関数を持つモジュールを新設しました。
* `def draw_blt(dst, dst_w, dst_h, x, y, img, u, v, w, h, colkey=-1, byte_swap=False):`
  * `img` は `Image` (ARGB4444) の場合と `Framebuffer` (RGB565) の場合の両方があり得るため、`is_argb` 分岐を残します。
* `def draw_sprite(dst, dst_w, dst_h, cx, cy, spr, rotate=0.0, scale=1.0, byte_swap=False):`
  * `Sprite` クラスは `Image` をソースとしているため、**ソースは常に ARGB4444 であると想定** し、RGB565コピー用の分岐を削除して最適化します。
* 描画の最内ループの中で `byte_swap` の真偽によって処理を分岐しますが、この分岐自体は定数的なif文またはループの外側に記述し、パフォーマンスの低下を防ぎます。

### [MODIFY] engine/hal/framebuffer_cpython.py
### [MODIFY] engine/hal/framebuffer_wasm.py
* `blt` および `sprite` の長大な実装を削除し、`software_renderer.draw_blt` および `draw_sprite` を呼び出すように変更しました。
* 引数として `dst=self._mv`, `byte_swap=False` を渡します。

### [MODIFY] engine/hal/framebuffer_micropython.py
* ピュアPython実装の `sprite` を `software_renderer.draw_sprite` 呼び出しに変更しました。
* 引数として `dst=self.buffer`, `byte_swap=True` を渡します。
* （既存の `_blt_viper_argb` や `_blt_viper_rgb` によるViper最適化はそのまま維持し、MicroPython環境での `blt` の高速化の恩恵を残しました。）

## Verification Plan
### Automated Tests
* エンジン単体での `main.py` を実行し、リファクタリング前と全く同じ描画結果（ブレンドや拡縮・端の欠けがないこと等）になることを確認しました。

### Manual Verification
* `main.py` の動作確認に加え、パフォーマンス面で目立ったコマ落ちや遅延がないかPC上で確認しました。
