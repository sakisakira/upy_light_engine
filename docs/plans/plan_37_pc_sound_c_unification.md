# Plan 37: PC版サウンド合成のC言語共通化

**日時**: 2026-07-08 20:50:00

## 目標
TODOにある「PC版のみ `sound_synth.py` による合成を行っているが、他のプラットフォームとコード共通化のためにC言語化できないか検討する」という課題を解決します。
現在ESP32とWASM版で使われている純粋なC言語のサウンドコア (`c_modules/core/sound_synth.c`) をPC版のシミュレータからも利用するようにし、波形生成ロジックの二重管理を解消します。

## 実装内容
- `scripts/build_engine_dll.ps1`: `core_engine_win.dll` のビルド対象に `c_modules/core/sound_synth.c` を追加します。
- `engine/hal/engine_ctypes.py`: `sound_synth_init`, `sound_synth_set_channel`, `sound_synth_render_int16`, `sound_synth_stop_all` 等の ctypes バインディングを追加します。
- `engine/hal/sound_synth.py`: 純粋なPythonによる波形合成処理を削除し、ctypes 経由で `sound_synth_render_int16` を呼び出してWAVを生成するように差し替えます。
- `TODO.md`: 対象項目に `(done)` を追記します。

## 検証
- Windows上でDLLをビルドし、シミュレータ実行時に問題なく音が鳴るか確認します（動作確認は一旦Windowsのみで行います）。
