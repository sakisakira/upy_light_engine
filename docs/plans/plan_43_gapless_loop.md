# Plan 43: Engine-side Gapless Loop Support

MML内にループマーカー `$` を導入し、エンジン側でBGMのシームレスなループ（Gapless Loop）を実現するための実装計画です。
PC版では、ご提案いただいた通り「イントロ用WAV」と「ループ用WAV」の2つを生成・繋ぎ合わせるアプローチを採用し、依存ライブラリ（pyaudio等）なしで極力動的なループに近づけます。

## 概要

### 1. `engine/mml_parser.py` (MMLパーサーの拡張)
- ループ開始を示す `$` マーカーをサポートします。
- これまでの `parse_mml(mml)` は1つのリストを返していましたが、これを `(intro_tracks, loop_tracks)` の2つのリスト（イントロ部の音符配列とループ部の音符配列）を返すように修正します。
- `$` が無い場合は全体が `intro_tracks` に入り（1回のみ再生）、先頭に `$` がある場合は全体が `loop_tracks` に入る（全体ループ）仕様とします。

### 2. `engine/hal/sound_synth.py` の改名と機能拡張
- PC専用（CPython用）の機能であることが明確になるよう、ファイル名を `sound_synth.py` から **`sound_synth_cpython.py`** へとリネームします。それに伴い、呼び出し元（`sound_cpython.py` など）の `import` も修正します。
- 既存の `render_wav(tracks)` を `render_wavs(intro_tracks, loop_tracks)` へ拡張します。
- Cのオシレータ状態（位相など）を維持したまま、まず `intro_tracks` 分をレンダリングして `intro.wav` のバイナリを作成し、そのまま状態をリセットせずに連続して `loop_tracks` 分をレンダリングして `loop.wav` のバイナリを作成します。
- これにより、2つのWAVファイル間での波形の「プツッ」というノイズ（位相ズレ）を完全に防ぐことができます。

### 3. 各HALの `play_sequence` / `update` の修正

#### `engine/hal/sound_cpython.py` (PC版)
- `play_sequence(intro_tracks, loop_tracks)` を受け取り、`sound_synth_cpython` で2つのWAVファイルを生成してテンポラリに保存します。
- まずイントロ部分を非同期再生し、`update()` の中で再生完了時間を監視します。
- イントロが終了したら即座にループ部分の再生を開始します。
  - Windowsの場合は `winsound.SND_LOOP` フラグを使ってネイティブに無限ループさせます。
  - macOS/Linuxの場合は `update()` で終了を監視し、終了するたびに再度サブプロセスで再生コマンドを呼び出します（PC版としての妥協点）。

#### `engine/hal/sound_wasm.py` & `sound_micropython.py` (WASM / 実機)
- 動的解釈の仕組みを活用し、`intro_tracks` の再生が終了したトラックから順次 `loop_tracks` に移行してインデックスを 0 にリセットし、無限にループを繰り返すように `update()` のロジックを修正します。

### 4. `tools/convert_bgm.py` (ゲーム側のMML生成ツール)
- ゲーム側のBGMは基本的にすべてループ再生させたいため、変換時にMMLの先頭に `$` を自動挿入するようにスクリプトを修正します。
