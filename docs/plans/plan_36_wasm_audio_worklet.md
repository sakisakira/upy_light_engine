# WASM版のサウンドエンジン統一 (AudioWorklet化) 実装計画

WASM環境（Webブラウザ）におけるサウンド再生を、PC・ESP32と同じC言語ベースのシンセサイザーロジック（`sound_engine.c`）に統一し、すべてのプラットフォームでバイトレベルで完全に同一の音を鳴らすための実装計画です。
（本計画は [Plan 30 Phase 4: WASM バインディング (Web)](file:///d:/sakira/work/cardputer/upy_light_engine/docs/plans/plan_30_phase4_wasm.md) および [Walkthrough 30 Phase 4](file:///d:/sakira/work/cardputer/upy_light_engine/docs/walkthroughs/walkthrough_30_phase4_wasm.md) の拡張にあたります）

## User Review Required

> [!IMPORTANT]
> - **Cコアの分離**: 現在ESP32専用のハードウェアコードと混在している音波生成ロジックを、プラットフォーム非依存の純粋なC言語ファイル（`c_modules/core/sound_synth.c`）に切り出します。これにより、ESP32とWASMの両方で同じシンセサイザーのソースコードを共有できるようになります。
> - **WASMとJavaScriptの連携**: AudioWorkletの読み込みには非同期処理（Promise）が必要ですが、Pythonのゲームループ（`update`）は同期的に回ります。この問題を解決するため、`index.html` の初期化フェーズで予めAudioWorkletとWASMのセットアップを済ませておき、Python側からは `postMessage` で即座にコマンドを送れる設計にします。

## Open Questions

> [!WARNING]
> - **Cコアの分離について**: `c_modules/core/sound_synth.c` を新設し、ESP32側の `sound_engine.c` からこの関数を呼び出す形にリファクタリングする方針で進めてもよろしいでしょうか？
> - **index.html の変更について**: AudioWorkletの初期化ロジック（JS）を `scripts/web/index.html` の `<script>` タグ内に追加し、Python起動前にセットアップを完了させるアプローチで問題ないでしょうか？

## Proposed Changes

### 1. C Core (音波生成ロジックの抽出)

#### [NEW] `c_modules/core/sound_synth.h`
#### [NEW] `c_modules/core/sound_synth.c`
- `sound_engine.c` から LCGノイズ生成、波形計算（矩形、ノコギリ、三角、ノイズ）、減衰（ディケイ）処理を抽出し、プラットフォーム非依存の関数として実装。
- ESP32向けに `int16_t` 配列を生成する `sound_synth_render_int16()` と、Web Audio API向けに `float` 配列（-1.0〜1.0）を生成する `sound_synth_render_float()` を提供。
- WASMのメモリ確保（malloc）を避けるため、128サンプル用の固定長バッファへのポインタを返す関数を提供。

### 2. ESP32 Sound Engine

#### [MODIFY] `c_modules/sound_engine/sound_engine.c`
- 内部の波形生成ループを削除し、代わりに `#include "core/sound_synth.h"` を用いて `sound_synth_render_int16()` を呼び出すようにリファクタリング。
- I2SやFreeRTOSなどのハードウェア固有の処理はそのまま維持する。

### 3. WASM Build System

#### [MODIFY] `scripts/build_engine_wasm.ps1`
- 既存の `core_engine.so` のビルドに加え、`sound_synth.c` をスタンドアロンのWASM（`build/sound_synth.wasm`）としてコンパイルするコマンドを追記する。
- `-s STANDALONE_WASM=1 --no-entry` と `EXPORTED_FUNCTIONS` を使用。

### 4. AudioWorklet (JavaScript)

#### [NEW] `engine/hal/audio_worklet.js`
- `AudioWorkletProcessor` を継承したクラスを実装。
- メインスレッドから渡されたWASMモジュールをインスタンス化し、`process()` メソッド内でWASMの `render` を呼び出して出力バッファを埋める。
- `port.onmessage` でPythonからの `set_channel` などのコマンドを受け取り、WASMに転送する。

### 5. Web Frontend

#### [MODIFY] `scripts/web/index.html`
- PyScriptの `[[fetch]]` リストに `build/sound_synth.wasm` と `audio_worklet.js` を追加。
- ユーザーのアクション（画面クリックやキー入力）で `AudioContext` を開始し、`audio_worklet.js` と `sound_synth.wasm` をロードして `AudioWorkletNode` をグローバル（`window.soundWorkletNode`）にセットアップするJS初期化コードを追加。

### 6. Python HAL (WASM)

#### [MODIFY] `engine/hal/sound_wasm.py`
- 現在の「`OscillatorNode` で全シーケンスを事前予約する方式」を破棄。
- `sound_micropython.py`（ESP32）と全く同じ「Pythonの `update()` で時間を監視し、タイミングが来たらチャンネル設定を更新するポーリング方式」に書き換える。
- 音符の切り替えタイミングで `window.soundWorkletNode.port.postMessage` を呼び出し、WASMにコマンドを送信する。

## Verification Plan

### Automated Tests
- WASMおよびESP32のビルド（`build_engine_wasm.ps1`）が正常に通ることを確認する。

### Manual Verification
- `scripts/web/index.html` をブラウザで開き、効果音やBGMが鳴るか確認する。
- ブラウザ上の音がPCエミュレータ（`winsound` / `afplay`）のWAV出力と完全に一致し、減衰（ディケイ）やノイズ波形などの表現が同一になっているか耳で聞いて確認する。
- ESP32（Cardputer）にビルドしたファームウェアを書き込み、I2Sスピーカーからの出力がデグレ（音割れやクラッシュ）していないか確認する。
