# Walkthrough 42: Engine Graceful Exit (PC/CPython)

## 概要
PC版エンジン（CPython + Tkinter）において、ウィンドウのクローズボタン（×ボタン）による終了や、ターミナルからの `Ctrl-C` (KeyboardInterrupt) による強制終了が行われた際に、クラッシュしたりバックグラウンドのプロセス（BGM等）がゾンビ化して残存する問題を解決し、安全に終了（Graceful Exit）させるための実装を行いました。

## 実装内容

### 1. `_exit_app()` による安全な終了フローの確立
`upy_light_engine/engine/hal/framebuffer_cpython.py` 内に、終了処理を担う `_exit_app()` 関数を新設しました。
- アプリケーションが終了する直前に、必ず `sound._hal.stop()` を呼び出し、OSレイヤー（`winsound` や `afplay` 等）で再生中の非同期サウンドプロセスを確実にキルする処理を追加しました。
- Tkinterのルートウィンドウ (`_root`) が存在する場合は破棄し、最後に `sys.exit(0)` を用いてPythonプロセスをクリーンに終了させています。

### 2. Tkinterのウィンドウ破棄イベントへのバインド
`init()` メソッド内において、Tkinterのウィンドウマネージャーのプロトコルである `WM_DELETE_WINDOW`（×ボタンが押された際のイベント）を上記の `_exit_app()` に直接バインドしました。これにより、ウィンドウが閉じられた際に `_tkinter.TclError` によるクラッシュを引き起こすことなく、音が止まって即座にプロセスが終了します。

### 3. `Ctrl-C` シグナルのスタブ化と捕捉
- `signal.signal(signal.SIGINT, _handle_interrupt_signal)` を用いて、OSレベルからの割り込みシグナルを捕捉するハンドラを登録しました。
- 定期実行される `_tick()` 内のメイン処理全体を `try...except KeyboardInterrupt` で囲み、Tkinterのコールバック内部でシグナルが発生した場合も適切にキャッチできるようにしました。
- 将来的な拡張機能（Ctrl-Cでゲーム内メニューやポーズを開くなどのルーティング）を見据え、直接 `_exit_app()` を呼ぶのではなく、**`_handle_interrupt_signal()` というスタブ関数**を介由して終了フローへ流れるように設計しています。

## 今後の課題（TODO）
- スタブ化された `_handle_interrupt_signal()` を拡張し、強制終了の代わりに「ポーズ画面を開く」「ゲームオーバー扱いにする」など、ゲームロジック側へのイベントルーティングを実装するかどうかは今後の仕様検討によります。
