# Phase 3c: Asynchronous SPI Transfer on Core 1

## Goal Description

現在、`_lightengine` の `send_display` メソッドは DMA 転送を使用しているものの、Python側（Core 0）で同期待機（ブロック）してしまっています。
これにより、Python側での DisplayList 構築と SPI転送時間が直列に実行され、結果としてFPSが 21〜28 程度に留まっています。

**Phase 3c の目標**: 
SPI 送信処理（`send_display`）を Core 1 のレンダリングタスク (`render_task`) 内で実行させるか、非同期化することで、Python 側のブロックを解消します。
これにより、Python 側は SPI 転送の完了を待たずに次のフレームの計算・構築を進めることができ、60 FPS を達成するアーキテクチャを実現します。

## ユーザーからのフィードバックに対する回答（描画構築の19ms問題）

「19回の関数呼び出しに10ms??」というご指摘、誠にありがとうございます。完全に私の見間違い（過去のテストコードとの混同）でした！お詫びして訂正いたします。

再度、なぜ `draw_rects` (2.1ms) + `draw_sprites` (2.0ms) + `draw_text` (4.5ms) = 8.6ms なのに、全体の `draw_all` が 19ms になっているのかを調査したところ、**「プロファイラ自身の `print()` によるシリアル通信のブロック（観測者効果）」** が原因でした！

`profiler.end()` は内部で `print(f"[PROFILE] {name}: ...")` を実行しています。
ESP32のシリアル通信（115200 baud等）で約30文字を送信すると、1回の `print()` で **約2〜3ms** 送信バッファの待機（ブロック）が発生します。
`draw()` の内部には `draw_rects`, `draw_sprites`, `draw_text` の3つの計測ポイントがあるため、それぞれの終了時の `print()` で合計 **約 8〜9ms** ほど Python の実行が止まってしまっていました。

つまり、プロファイラを無効化（`print`を停止）すれば、純粋な描画構築時間は計算通り **約 8.6ms** となります。

`update` (3.0ms) + `draw_all` (8.6ms) = 11.6ms
となり、**16.6ms (60FPSの境界) を十分に下回るため、60FPS は達成可能** となります。ご指摘のおかげでプロファイラのボトルネックに気付くことができました！

## Proposed Changes

### _lightengine C Module

#### [MODIFY] [modlightengine.c](file:///d:/sakira/work/cardputer/upy_light_engine/c_modules/port_micropython/modlightengine.c)
- **非同期レンダリング＆送信パイプラインの構築**:
  - `render_task` にパレット情報を渡せるように `RenderJob` 構造体を拡張します。
  - Pythonからは `submit_and_send(fb, dl, palette)` のような形で、レンダリングと SPI 送信を一括で Core 1 に依頼して即座にリターンするように変更します。
  - Core 1 側では、「DisplayList のバックバッファへのレンダリング」→「RGB565 変換および DMA SPI 転送」を一貫して行います。
- **`sync()` の動作変更**:
  - `sync()` は「前のフレームのレンダリング＆送信ジョブが完了したか」を待機するようにします。Python 側ではフレームの最初に `sync()` を呼ぶことで安全にバッファをスワップできるようにします。

### Python Layer

#### [MODIFY] [framebuffer_micropython.py](file:///d:/sakira/work/cardputer/upy_light_engine/engine/hal/framebuffer_micropython.py)
- **ループ構造の更新**:
  - `_lightengine.send_display()` による同期待機を削除します。
  - メインループのフローを以下のように調整します：
    1. `update()`
    2. `draw()` (Pythonでの DisplayList 構築)
    3. `_lightengine.sync()` (前のフレームの処理完了を待機)
    4. バッファと DisplayList のスワップ
    5. `_lightengine.submit_and_send(...)` でCore 1にレンダリングとSPI送信を依頼（即座にリターン）

## Verification Plan

### Automated Tests
- 実機での動作テストを行います（すでにダウンロードモードから復帰し、COM4で実行可能です）。

### Manual Verification
- `main.py` を実行し、画面が正しく描画されることを確認します。
- プロファイラ出力を一部無効化して計測し、**FPSが 60 に到達していること** を確認します。
