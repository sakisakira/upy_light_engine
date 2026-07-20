# [Cモジュール内での `.ubgm` シーケンサー実装計画]

現在、BGMの次音符の取得・発音（Fetch & Apply）を Python 側の `sound.update()`（毎フレーム1回）に依存しているため、ゲームのフレームレートのブレやガベージコレクション(GC)の停止時間がそのままBGMのリズム変動（波）として現れてしまっています。

これを解決するため、ユーザー様のご提案通り「ファームウェア側（C言語のオーディオレンダリングスレッド）で直接シーケンス処理を行う」アーキテクチャへの改修を行います。

## User Review Required

- 本改修により、**ファームウェア（ESP32）および WASM の再ビルド** が必要となります。
- これまでは `.ubgm` のパースを Python (`engine.sound.py`) で行っていましたが、その処理を C 言語側 (`sound_synth.c`) へ完全に移管します。
- Python 側のゲームループで呼んでいた `sound.update()` は不要になるため削除します。

## Proposed Changes

### 1. C Core (`c_modules/core/sound_synth.c`, `sound_synth.h`) の改修
- `.ubgm` バイナリフォーマットをC言語側で解釈するための構造体とパーサーを追加します。
- 音声サンプルのレンダリング処理 (`sound_synth_mix_sample`) 内に、シーケンサー（各トラックの残り発音時間をサンプル単位でカウントダウンし、0になれば次の音符を読み込む処理）を組み込みます。
- オーディオレンダリングと同期して音符が切り替わるため、GCやPythonループの影響を受けない**ミリ秒/サンプル単位の完璧なリズム**が実現されます。

### 2. C API (`c_modules/sound_engine/sound_engine.c`) の改修
- Python から `.ubgm` のバイナリデータ（`bytes`）を直接受け取る関数 `play_ubgm(data)` を新規に追加します。
- 受信したバイナリデータを C 側で保持（`malloc` 等でコピー）し、シーケンサーに登録します。

### 3. Python Wrapper (`engine/sound.py`) の改修
- Python 側の `.ubgm` パーサー（`_UBGMTrack`, `load_ubgm` など）を削除し、単にファイルを読み込んで `c_engine.play_ubgm(data)` に渡すだけの薄いラッパーに変更します。
- `engine/hal/framebuffer_micropython.py` に追加した一時的な `sound.update()` の呼び出しを削除します。

## Verification Plan

### Automated Tests
- C側のユニットテストはありませんが、WASMビルドを実行し、エラー無くビルドが通るか確認します。

### Manual Verification
- 実機（ESP32）のファームウェアをコンパイルし直し、ゲームを起動してBGMが**全くリズムの揺れなく**スムーズに再生されるかを確認します。
- WASM版をビルドしてブラウザで起動し、同様に滑らかに再生されるかを確認します。
