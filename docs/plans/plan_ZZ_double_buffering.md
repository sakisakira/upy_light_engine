# Plan ZZ: Double Buffering & Multi-Core Rendering Architecture

現時点では「実装計画候補」扱いとする。将来的に実装計画を作るときの参照元とする。

## Background
現在、ゲームループの1フレームは以下の直列処理になっています。
1. `update()`: ゲームロジック（約3ms）
2. `draw()`: フレームバッファへの描画（約24ms）
3. `display.show()`: SPI経由での画面転送（約20ms）

合計で約47msかかっており、これが21FPSの限界の主な原因です。
特に `display.show()`（20ms）は単にデータをSPIに流し込んでいるだけの時間であるため、この待機時間を隠蔽（オーバーラップ）できれば、大幅なFPS向上が見込めます。

## Proposed Architecture (Dual-Core Double Buffering)

このプランは、ESP32の「Core 0」と「Core 1」を利用した完全分業制アーキテクチャの構想です。

### 1. ダブルバッファの導入
現在の単一の `screen.buffer` を2つに分けます。
- `buffer_A`
- `buffer_B`

### 2. コアの役割分担 (スレッド分離)
- **Core 0 (Logic & Render Thread)**
  - `update()` を実行し、裏画面（例：`buffer_A`）に対して `draw()` を実行します。
- **Core 1 (Display Thread)**
  - 表画面（例：`buffer_B`）の内容を `display.show()` でSPIに転送し続けます。

### 3. フリップ（画面切り替え）
- Core 0 が描画を終え、かつ Core 1 が転送を終えたタイミングで、`buffer_A` と `buffer_B` の役割をスワップ（ポインタの入れ替え）します。
- これにより、「描画（24ms）」の裏で同時に「画面転送（20ms）」が並列実行されるため、実質的なフレーム処理時間は長い方（24ms）に隠蔽されます。

## Open Questions & Challenges
- **メモリ消費**: INDEX8のフレームバッファ（240x135 = 32.4KB）を2つ持つことになります。Cardputerの空きメモリ（現在約90KB）には収まりますが、余裕は減ります。
- **スレッド同期**: MicroPythonの `_thread` モジュールを使用し、Core 0とCore 1の間で「描画完了」と「転送完了」のシグナル（EventやLock）をやり取りする仕組みが必要です。

## 結論
この計画は、将来的に「エンジンをCore 1に封じ込める」という究極の目標と密接に関連しています。
Cモジュールの全プラットフォーム共通化が完了した後、このダブルバッファリング＋マルチスレッドアーキテクチャに本格的に取り組むための備忘録として本ドキュメントを残します。
