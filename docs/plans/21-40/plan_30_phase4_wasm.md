# Plan 30 Phase 4: WASM バインディング (Web) 実装計画

## 背景・要件
`plan_30_c_cpp_engine_architecture.md` に基づき、C言語で実装したCore EngineをWebブラウザ上で動作させる「Phase 4: WASM バインディング」を実施します。
PyScript + Pyodide 環境で C言語モジュールをロードし、Web上でゲームを描画・実行できるようにします。

## 設計判断とアーキテクチャ

### 1. `ctypes` による WASM 共有モジュール (.so) のロード
Emscriptenの機能（`SIDE_MODULE=1`）を用いると、CコードをWASMベースの「共有ライブラリ (.so)」としてコンパイルできます。PyodideはPythonの標準ライブラリである `ctypes` を通じて、この `.so` ファイルをロードし、C関数の呼び出しやメモリ操作を行うことを公式にサポートしています。
これにより、**PC版（Windows/Mac）向けに作った `ctypes` ベースのバインディングコードを、Web版でもほぼそのまま再利用（DRY化）** できます！

### 2. コアロジックの共通化 (`engine/hal/engine_ctypes.py`)
現在、Windows/Mac向けのラッパークラス（`Image`, `Sprite`, `Framebuffer`等）は `framebuffer_cpython.py` 内にべた書きされています。
これを新設する `engine_ctypes.py` に抽出し、PC版とWeb版の両方から継承して利用できるようにします。

- **PC版 (`framebuffer_cpython.py`)**: `engine_ctypes.py` のクラス群を継承し、OSのウィンドウ表示（Tkinter）と画像転送（PIL）のみを担当。
- **Web版 (`framebuffer_wasm.py`)**: 同様に継承し、ブラウザのCanvas表示（JS）とメインループ（`requestAnimationFrame`）のみを担当。

## Proposed Changes

### [NEW] `scripts/build_engine_wasm.ps1`
Emscripten (`emcc`) を用いて、`c_modules/core` 以下のCソース群から `core_engine.so` を生成するビルドスクリプトを作成します。

### [MODIFY] `engine/hal/engine_cpython.py` -> `engine_ctypes.py` (リネーム＆拡張)
現在の `engine_cpython.py` をリネームし、OSプラットフォーム（`win32`, `darwin`, `emscripten`）に応じてロードする共有ライブラリのパスを分岐させます。さらに、`framebuffer_cpython.py` から `Image` や `Framebuffer` 等の共通ラッパークラスをこちらへ移動します。

### [MODIFY] `engine/hal/framebuffer_cpython.py`
`engine_ctypes.py` からベースクラスを継承する形にリファクタリングし、Tkinter関連のロジックのみを残すことでコードを大幅に簡略化します。

### [MODIFY] `engine/hal/framebuffer_wasm.py`
現在の「ピュアPythonでの配列操作」を破棄し、`engine_ctypes.py` のCバインディングクラスを継承するように書き換えます。描画結果（C側で確保したピクセルバッファ）をJavaScript側のCanvas APIに転送して描画するロジック (`window.drawFramebufferWasm`) を定義します。メインループはJSの `requestAnimationFrame` に委譲します。

### [MODIFY] `scripts/web/index.html`
- `<py-config>` の `files` リストに `engine_ctypes.py` とビルド済みの `core_engine.so` 等を追加。
- 起動時に `core_engine.so` を自動でフェッチして仮想ファイルシステム上に配置する設定を追記。

## 関連計画
* [Plan 36: WASM版のサウンドエンジン統一 (AudioWorklet化)](file:///d:/sakira/work/cardputer/upy_light_engine/docs/plans/plan_36_wasm_audio_worklet.md) は、このPhase 4のサウンド機能拡張にあたります。
