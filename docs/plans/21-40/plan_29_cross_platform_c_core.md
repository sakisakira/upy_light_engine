# Plan 29: Cross-Platform C Graphics Engine Unification

## Background
PC版（CPython）でも32FPSが出ているとのこと、素晴らしいです！しかしご指摘の通り、今後エンジンに機能追加（例：スプライトの回転・半透明など）を行う際、「Cardputer用にはC言語（`.mpy`）を書き、PC用にはPython（`software_renderer.py`）を書く」という二重管理状態は、バグやデグレの温床になります。

そこで、現在のCモジュールを「すべてのプラットフォームで共通して使えるコア」として抽出し、管理を一本化します。Cardputerのパフォーマンスを一切落とさないことが絶対条件です。

## Open Questions
- PC環境でCコードをコンパイルするために、Windows版 `gcc`（MSYS2等）を利用します。事前の確認コマンドでシステムに `gcc` がインストールされていることを確認済みですので問題ない想定です。

## Proposed Architecture

現在の `graphics_engine.c` はMicroPythonのAPI（`py/dynruntime.h`）に強く依存しているため、そのままではPC（CPython）で使えません。これを以下の「3層構造」に分離します。

### 1. Pure C Core (`c_modules/core_graphics/`)
一切のPythonAPIに依存しない、純粋なC言語の関数群を作ります。
- `core_graphics.c` / `core_graphics.h`
- 生のメモリポインタ（`uint8_t *`）を受け取り、ピクセル操作だけを行う関数群（`core_draw_sprite`, `core_draw_text`, `core_convert_palette`）を定義します。

### 2. MicroPython Wrapper (`graphics_engine.c` の改修)
Cardputer（MicroPython）用のラッパーです。
- Pythonオブジェクトから生ポインタを取り出す処理だけを行い、即座に `core_graphics.c` の関数を呼び出します。
- C言語レベルでの単なる関数呼び出しになるため、オーバーヘッドは **ゼロ** です。Cardputerのパフォーマンスは現在の36FPSから一切下がりません。
- Makefileを修正し、これら2つのファイルを結合して1つの `.mpy` にコンパイルします。

### 3. CPython Wrapper (PC向け)
PC版での利用方法です。
- `gcc` を使って `core_graphics.c` をWindows用のダイナミックリンクライブラリ（`core_graphics.dll`）としてコンパイルします。
- PC側の `software_renderer.py` は、Python標準ライブラリの `ctypes` を使ってこのDLLを読み込み、フレームバッファのメモリアドレスを直接C関数に渡します。
- これにより、PC版の描画も完全にC言語で処理されるようになり、コードの完全共有とPC版の圧倒的な高速化が同時に達成されます。

### 4. WASM Wrapper (ブラウザ向け)
WebAssembly環境での利用方法です。
- `emcc` (Emscripten) を使って `core_graphics.c` をWebAssemblyバイナリ（`.wasm`）として単独でコンパイルします。
- `framebuffer_wasm.py` 側から、JavaScriptのTypedArray（WASMの共有メモリ）をポインタとして直接C関数に渡すことで、ブラウザ上でも全く同じC言語コアをネイティブスピードで実行できます。
- Pure C Coreを「PythonのAPIから完全に切り離す」設計にしているため、WASM対応が極めて容易になります（今回の改修の最大のメリットの一つです）。

## Proposed Changes

### [NEW] `c_modules/core_graphics/core_graphics.h`
純粋なCエンジンのヘッダーファイル。

### [NEW] `c_modules/core_graphics/core_graphics.c`
`graphics_engine.c` からループ処理（スプライト描画、テキスト描画、パレット変換）を抽出し、Python非依存の関数に書き直します。

### [MODIFY] `c_modules/graphics_engine/graphics_engine.c`
MicroPython APIの解釈だけを行い、抽出した `core_graphics.c` に処理を丸投げする薄いラッパーに改修します。

### [MODIFY] `c_modules/graphics_engine/Makefile`
`core_graphics.c` も一緒にコンパイルしてリンクするように修正します。

### [NEW] `scripts/build_graphics_dll.ps1`
PC版用に `gcc` を呼び出し、`core_graphics.dll` を生成するビルドスクリプトを作成します。

### [NEW] `scripts/build_graphics_wasm.ps1`
ブラウザ（WASM）用に `emcc` を呼び出し、`core_graphics.wasm` (または `.js` バインディング) を生成するビルドスクリプトを作成します。

### [MODIFY] `engine/hal/framebuffer_cpython.py`
内部で `software_renderer.py` の代わりに `ctypes` で `core_graphics.dll` を呼び出すように改修します。

### [MODIFY] `engine/hal/framebuffer_wasm.py`
内部でJavaScriptのTypedArrayを介して `core_graphics.wasm` を呼び出し、WASM上でのネイティブ描画を行うように改修します。

## Verification Plan
1. `build_graphics_mpy.ps1` を実行し、ビルドエラーが出ないことを確認する。
2. Cardputer上で実行し、FPSが低下していないこと（約36FPSの維持）と描画が乱れていないことを確認する。
3. `build_graphics_dll.ps1` を実行してDLLを生成し、PCで `run_on_pc.ps1` を実行。PC版でも同じCモジュール経由で正しく描画されることを確認する。
4. `build_graphics_wasm.ps1` を実行してWASMバイナリを生成し、ローカルサーバーを立ててブラウザで実行。WASM環境でも同じCコアが動作することを確認する。
