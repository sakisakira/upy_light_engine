# Walkthrough 30 Phase 2: CPython(PC) DLL Bindings

## 概要
このドキュメントは `plan_30_c_cpp_engine_architecture.md` における **Phase 2** の完了報告をまとめたものです。
Phase 1 で構築した純粋なC言語のグラフィックコアエンジンをWindows用のDLLとしてビルドし、PCのCPython環境において `ctypes` 経由で呼び出すバインディングを実装しました。これにより、PC上のエミュレータはPythonでのソフトウェアレンダリングを卒業し、高速なCエンジンでの描画を行うようになりました。

## 実装内容

### 1. C言語エンジンの拡張と DLL ビルド
- ご要望に基づき、将来的な拡張を見据えてCエンジン側に `kCmdPset`, `kCmdLine` コマンドを追加し、合わせて正確な画像転送のための `kCmdBlt` もネイティブ実装しました。
- `dl_create()` と `dl_destroy()` を用意し、ディスプレイリストのメモリ確保・解放の制御をPython側からシンプルに呼び出せるようにしました。
- `scripts/build_engine_dll.ps1` を作成し、`gcc` を用いてCソースをコンパイルし `build/core_engine.dll` を生成できるようにしました。

### 2. CPython バインディング (`engine/hal/engine_cpython.py`)
- `ctypes.Structure` を用いて、`CEngineImage`, `CEngineSprite`, `CEngineFramebuffer`, `CDisplayList` を定義しました。
- `core_engine.dll` をロードし、`dl_push_pset` などの各描画関数の引数型・戻り値型を設定しました。

### 3. オブジェクトのメモリ寿命管理 (`_c_refs`)
- C側の `DisplayList` は各種構造体のポインタを保持します。描画前にPython側でガベージコレクション(GC)が行われてメモリが破棄されないよう、`Image`, `Sprite`, `Font` クラスの初期化時にC構造体も一緒に生成し、Pythonオブジェクト内に保持 (`self._c_image` 等) するアプローチを採用しました。
- テキスト描画時に渡す一時的な文字列バイト列や、`blt` などで内部的に生成する一時オブジェクトは、`Framebuffer` クラス内の `self._c_refs` リストに一時的にスタックし、フレーム描画終了時 (`_flush()`) にリストをクリアすることで安全にメモリ管理を行う設計にしました。

### 4. `Framebuffer` クラスのディスプレイリスト化
- `engine/hal/framebuffer_cpython.py` を大幅に改修し、従来のソフトウェアレンダリング処理をすべて削除しました。
- 各描画メソッド (`clear`, `rect`, `sprite`, `text`, `pset`, `line`, `blt`) が呼ばれると、即座に描画するのではなく `dl_push_*` を使ってディスプレイリストにコマンドを積むように変更しました。
- メインループの毎フレームの最後 (`_tick()` 内) で `screen._flush()` が呼ばれ、ここで初めて `render_display_list` が実行され一括ラスタライズが行われます。

## 動作確認
- PCエミュレータ環境 (`python main.py`) にてエラーなく起動・動作することを確認しました。Cエンジンのディスプレイリストを経由した描画が正しく機能しています。
