# 時間管理システム (Time & FPS Management)

## Goal
エンジンのプラットフォーム（CPython, WASM, MicroPython）間の時間計測APIの差異を吸収し、将来的なゲームの一時停止（Pause）機能や正確なFPS計測をサポートする、統一された時間管理システム `engine.time` を実装します。

## 概要
先の計画（FPSの表示のみ）からスコープを拡大し、「システム時間の計測」「ゲーム内時間の管理（一時停止可能）」「フレーム数のカウント」「FPSの計測」をすべて担う `Clock` クラスを設けます。
各プラットフォームのメインループ (`fb.run()`) は、毎フレーム1回だけ `time.clock.tick()` を呼び出すことで時間を進め、ゲーム側からはプラットフォームを意識せずにFPSやゲーム内時間 (`game_time_ms`) を取得できるようにします。

## Proposed Changes

### [NEW] engine/time.py
時間管理モジュールを新設します。
* **プラットフォーム互換レイヤー**:
  `time.ticks_ms()` と `time.ticks_diff()` を安全に提供します。MicroPythonでは標準の `time` (utime) を使い、CPython/WASMでは `time.time()` をベースにエミュレートします。
* **`Clock` クラスの実装**:
  * **プロパティ**:
    * `frame_count`: ゲームのフレーム数（一時停止中は増加しない）
    * `game_time_ms`: ゲーム内経過時間（一時停止中は増加しない）
    * `delta_time_ms`: 前フレームからの経過時間（一時停止中は 0）
    * `fps`: 直近1秒間のフレームレート
    * `is_paused`: 一時停止フラグ
  * **メソッド**:
    * `tick()`: システム時間を読み取り、各種パラメーターやFPSを更新する（毎フレーム呼ばれる）
    * `pause()`, `resume()`: 一時停止/再開を制御する
* グローバルインスタンスとして `clock = Clock()` を公開します。

### [MODIFY] engine/hal/framebuffer_cpython.py 等
* 各HALのメインループ（`_tick()` や `while True:` ループ内）の先頭で、`engine.time.clock.tick()` を呼び出すように修正します。

### [MODIFY] main.py (エンジンのテストベッド)
* `TODO.md` の要求に基づき、毎フレームごとに `engine.time.clock.fps` を取得して画面右上にテキスト描画します。
* テストとして、指定したボタン（例えば `Select` や `Start` の代わりとなるキー）を押したときに `clock.pause()` / `resume()` を切り替えられるようにし、一時停止機能が働くか確認します。
* ログ出力も `update()` 等で1秒ごとに（あるいはFPS値が更新されたタイミングで）出力するようにします。

## Verification Plan
### Automated Tests
* 特になし（ハードウェア依存やタイミング依存の処理のため）

### Manual Verification
* `main.py` を実行し、画面上にFPSが安定して表示されることを確認します。
* コンソールに1秒間隔でFPSが出力されることを確認します。
* 一時停止ボタンを押し、アニメーション（ゲーム内時間依存）が正しく停止・再開することを確認します。
