# Walkthrough 36: WASM版のサウンドエンジン統一 (AudioWorklet化)

**日時**: 2026-07-06 22:15:00
**関連計画**: [Plan 36: WASM版のサウンドエンジン統一 (AudioWorklet化)](file:///d:/sakira/work/cardputer/upy_light_engine/docs/plans/plan_36_wasm_audio_worklet.md)

このドキュメントでは、PC・ESP32と同じC言語ベースのシンセサイザーロジック（`sound_engine.c`）をWASM環境（Webブラウザ）へ移植し、全プラットフォームでバイトレベルで同一のサウンドを鳴らすための変更について報告します。

## 1. C言語サウンドコアの抽出
これまでESP32専用のハードウェアコード（`sound_engine.c`）内に混在していた「音波生成ループ」「減衰（ディケイ）計算」「ノイズ波形用の擬似乱数（LCG）」を切り出し、プラットフォーム非依存の純粋なCコードとして以下のファイルに分離しました。

- **`c_modules/core/sound_synth.h`**
- **`c_modules/core/sound_synth.c`**

これにより、ESP32側の `sound_engine.c` はハードウェアミキシングとI2Sの初期化に専念し、実際の波形計算は `sound_synth_render_int16()` に委譲するすっきりとした設計にリファクタリングされました。

## 2. WASM スタンドアロンビルドの追加
`scripts/build_engine_wasm.ps1` を更新し、Pyodide用の共有ライブラリ（`core_engine.so`）に加えて、AudioWorklet専用のスタンドアロンWASMモジュール（`sound_synth.wasm`）をビルドするようにしました。
- `emcc` の `-s STANDALONE_WASM=1 --no-entry` オプションを使用。
- `malloc` を使わずに済むよう、WASM内に128サンプルの固定長バッファを持たせ、そのポインタを取得する `_sound_synth_get_wasm_buf_l` 等をExportしています。

## 3. AudioWorklet の実装
JavaScriptで動作する `engine/hal/audio_worklet.js` を新規作成しました。
- `process()` 内で `wasm.exports.sound_synth_render_wasm()` を毎フレーム呼び出し、128サンプルのFloat32ArrayをAudioContextへ直接渡します。
- Python（メインスレッド）から `postMessage` で送信された `set_channel` や `stop_all` コマンドを受け取り、WASM関数へルーティングする役割を持ちます。

## 4. Webフロントエンド (index.html) の改良
PyScriptの同期的なゲームループ（`update`）から非同期のAudioWorkletモジュールを扱う複雑さを避けるため、`scripts/web/index.html` にセットアップ用のJavaScriptを埋め込みました。
- ユーザーのアクション（キー入力やマウスクリック）を検知すると、ゲームループの裏側で `audioCtx.resume()` を呼び出し、`audio_worklet.js` と `sound_synth.wasm` をロードして `AudioWorkletNode` を初期化します。
- これにより、Python側は単純に `js.window.soundWorkletNode` へメッセージを投げるだけで済むようになりました。

## 5. WASM用 Python HAL の改修
`engine/hal/sound_wasm.py` を全面的に書き換えました。
- 以前はWeb Audio APIの `OscillatorNode` と `setValueAtTime` を用いて、シーケンス全体をブラウザに一括で事前予約していました。
- 改修後は ESP32版（`sound_micropython.py`）と全く同じ「Pythonの `update()` で時間を監視し、タイミングが来たらチャンネル設定を更新するポーリング方式」を採用。
- 音符の切り替えタイミングで `window.soundWorkletNode.port.postMessage` を呼び出します。

## 検証結果
- ビルドスクリプトはエラーなく完了し、`sound_synth.wasm` と `core_engine.so` の両方が生成されました。
- これにより、今後の波形エディタ開発などにおいて「PC版とブラウザ版で鳴り方が違う」という致命的な問題を回避できるベースが整いました。
- ユーザーにブラウザでのローカルテスト (`python -m http.server`) およびESP32での実機テストを依頼します。
