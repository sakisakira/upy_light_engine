# Plan 42: Engine Graceful Exit (PC/CPython)

PC版エンジン（CPython + Tkinter）において、ウィンドウを閉じた際やコンソールから `Ctrl-C` を送信した際にクラッシュしたり、サウンド再生プロセスが裏で残存してしまう問題（ゾンビ化）を解決し、安全に終了（Graceful Exit）させるための実装計画です。

## 概要

### 1. `upy_light_engine/engine/hal/framebuffer_cpython.py`
Tkinterのメインループ周りにおける終了シーケンスを追加・統合します。

**終了処理用の共通関数 `_exit_app` の追加:**
- バックグラウンドで鳴っている可能性のあるBGMやSEを止めるため `sound.stop()` を呼び出します（これにより `winsound` や `afplay` 等のゾンビ化を防ぎます）。
- Tkinterのルートウィンドウ (`_root.destroy()`) を破棄し、Cレイヤーのメインループを停止させます。
- `sys.exit(0)` を用いてPythonプロセス自体をクリーンに終了させます。

**ウィンドウの「×」ボタンへの対応:**
- `init()` 内で、Tkinterのウィンドウ破棄イベント (`WM_DELETE_WINDOW`) を `_exit_app` にバインド（`protocol`）し、×ボタンが押された際に安全な終了フローを通るようにします。

**`Ctrl-C` (KeyboardInterrupt) への対応とシグナル送信スタブの用意:**
- `init()` 内で `signal.signal(signal.SIGINT, ...)` を用い、OSからの割り込みシグナルを捕捉するハンドラを登録します。
- **将来への拡張スタブ**: このハンドラ内や `_tick()` の例外捕捉箇所から呼ばれる処理として、単に即座に終了するだけでなく「ゲーム側へ中断シグナル（例：ポーズやメニューを開くなど）をルーティングするためのスタブ処理」を組み込みます。当面はスタブ内に「強制終了」の動作を記述しておきます。
- Tkinterのメインループが例外を飲み込んでしまうケースに備え、定期実行される `_tick()` 内の処理全体を `try...except KeyboardInterrupt` で囲み、コールバック内でCtrl-Cが発生した場合もこのシグナルスタブ処理を通るようにします。
