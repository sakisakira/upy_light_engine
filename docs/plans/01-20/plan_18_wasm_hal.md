# Web (WASM) HAL 実装計画

TODOリストにある「Web (WASM) HAL」の実装計画です。
ゲームエンジン（`upy_light_engine`）で作ったゲームを、ブラウザ上でそのまま動かせるようにするためのハードウェア抽象化レイヤー（HAL）を追加します。

## Goal
`engine/hal/` の下にWASM（WebAssembly）向けのバックエンドを実装し、ブラウザ（HTML5）上でフレームバッファ描画、キー入力、サウンド再生を実現する。

## 実装アプローチ：Pyodide / PyScript
ブラウザ上でPythonを動かす環境として、標準的で扱いやすい **Pyodide (PyScript)** をターゲットとします。（MicroPythonのWASMポートよりもDOM操作やHTMLとの連携が容易なため）
`sys.platform == 'emscripten'` を検知してWASM HALをロードします。

### 1. Framebuffer (`framebuffer_wasm.py`)
- HTML5の `<canvas>` 要素を使用します。
- 内部バッファ（16bitカラー）はPC/デバイス版と同じように扱い、画面更新（`update` / `draw` の最後）のタイミングで、JS側の `ImageData` (32bit RGBA) に変換してCanvasに転送（`putImageData`）します。
- **ゲームループの非同期化**: ブラウザでは無限ループ（`while True:`）を回すとフリーズするため、JavaScriptの `window.requestAnimationFrame` または `asyncio` を利用して `update` と `draw` を定期的に呼び出す仕組みに変更します。

### 2. Input (`input_wasm.py`)
- JSの `window.addEventListener('keydown')` および `keyup` をフックします。
- 押されたキー（ArrowKeys, Z, Xなど）をエンジンのボタン定義（`Button_A`, `Button_B`, `Button_UP` など）にマッピングし、状態を保持します。

### 3. Sound (`sound_wasm.py`)
- 既存のMMLパーサーをそのまま利用します。
- 音の再生にはブラウザの **Web Audio API** (`AudioContext`) を使用します。
- MMLの各ノート（周波数と長さ）をJSの `OscillatorNode` に変換して非同期（またはスケジュールして）鳴らします。

### 4. 実行環境 (`index.html`)
- エンジンとゲームスクリプトをブラウザにロードするためのテンプレートとなる `index.html` を `scripts/` または `tools/` フォルダ等に用意します。
- ユーザーはローカルサーバー（`python -m http.server`）を立ち上げるだけで、PC版と同じ `main.py` をブラウザで遊べるようになります。

## Proposed Changes
```markdown
#### [MODIFY] engine/framebuffer.py
- `sys.platform == 'emscripten'` の分岐を追加し、`framebuffer_wasm` をロード。

#### [MODIFY] engine/input.py
- 同様に `input_wasm` をロード。

#### [MODIFY] engine/sound.py
- 同様に `sound_wasm` をロード。

#### [NEW] engine/hal/framebuffer_wasm.py
- Canvas描画ロジックと `requestAnimationFrame` を用いたメインループ実装。

#### [NEW] engine/hal/input_wasm.py
- JSイベントリスナーを使ったキーボード入力管理。

#### [NEW] engine/hal/sound_wasm.py
- Web Audio API (js.AudioContext) を使ったMMLおよびトーン再生機能。

#### [NEW] tools/web_runner/index.html (ディレクトリ構成は要相談)
- PyScriptを利用して `main.py` と `engine/` をブラウザにマウントし、実行するHTMLテンプレート。
```

## User Review Required
> [!IMPORTANT]
> 1. **実行環境について**: PythonのWASM実装には「Pyodide/PyScript」と「MicroPython WASMポート」がありますが、DOMやWeb Audio APIとの連携が非常に簡単でモダンな **Pyodide (PyScript)** をターゲットとする方針でよろしいでしょうか？
> 2. **ファイル配置**: ブラウザでテストするためのテンプレートHTML（`index.html` など）は、`scripts/web/` や `tools/web/` などのディレクトリに置く形でよろしいでしょうか？

## Verification Plan
1. WASM HALの各モジュールを実装。
2. `tools/web/index.html` を作成し、ローカルWebサーバーでホストする。
3. ブラウザからアクセスし、PC版/ESP32版と全く同じ `main.py` がCanvas上に描画され、キーボード操作ができ、MMLが再生されることを確認する。
