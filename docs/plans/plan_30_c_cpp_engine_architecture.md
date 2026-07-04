# Plan 30: C/C++ Engine Architecture & Cross-Platform Bindings

TODO.mdの目標である「Core 1でのエンジン駆動」や「ファームウェアへの実装」を見据え、エンジンのコア（状態管理と描画）をすべてC言語（オブジェクト指向ライクな設計）で再構築し、Python側を薄いラッパーとする抜本的なアーキテクチャ変更の計画です。これにより `plan_29` は本計画に統合・発展的解消されます。

## Architectural Decisions (Based on User Feedback)
- **言語選択**: **C言語**。Palm OSアプリやGLibのような、構造体と関数ポインタを組み合わせた「オブジェクト指向風のC言語」で実装します。
- **MicroPythonへの統合**: **カスタムファームウェア（User C Module）**としてビルドします。過去の `scripts/build_c_module.ps1` と Docker環境を活用します。
- **機能スコープ**: まずは **グラフィック周り（Sprite, FramebufferのAPI）** のC言語化に注力し、入力（Input）処理などは後回しにします。
- **Display List（ディスプレイリスト）とは**:
  - 描画コマンド（「この位置にこの画像を書いてね」という指示）を一時的にストックしておくリスト（バッファ）のことです。
  - 將来的に Core 0（Python）と Core 1（描画エンジン）を分離した際、Python側が直接フレームバッファをいじるとCore 1の描画と衝突（ちらつきやクラッシュ）してしまいます。そのため、Pythonは「ディスプレイリスト」に指示だけを書き込み、Core 1がそれを一気にフレームバッファに焼き付ける、という安全な分業システムのために必要な概念です。

## Proposed Changes (Phased Approach)

コードのレビューを細切れに行えるよう、Phaseを細かく分割して進めます。各Phaseが終わるごとに報告し、レビューをお願いします。

### Phase 1: Core Engine の基礎構造 (Pure C)
Pythonから完全に独立したC言語のコアロジックを作成します。
- [NEW] `c_modules/core/engine_types.h` / `.c`: `Image`, `Sprite`, `Framebuffer`, `DisplayList` の構造体定義とメモリ確保/解放処理。
- [NEW] `c_modules/core/engine_render.h` / `.c`: 構造体を受け取って実際にピクセルを塗る処理（`blt`, `fill_rect` 等）。`plan_28`の高速化ロジックを移植。

### Phase 2: CPython(PC) バインディングとテスト実装
構築したCore EngineがPC環境で正しく動作するか検証します。
- [NEW] `scripts/build_engine_dll.ps1`: `gcc`を用いたWindows用DLLビルドスクリプト。
- [NEW] `engine/hal/engine_cpython.py`: `ctypes`を使ってDLLをロードし、`Sprite`や`Framebuffer`クラスのAPIをPythonに提供するラッパー。
- 動作確認: 既存のPC版エミュレータ上で描画が正しく行われるかテスト。

### Phase 3: MicroPython ファームウェア組み込み (Cardputer)
Core EngineをMicroPythonの「User C Module」としてファームウェアに統合します。
- [NEW] `c_modules/port_micropython/micropython.mk`: ファームウェアビルドにエンジンを組み込むためのMake設定。
- [NEW] `c_modules/port_micropython/modlightengine.c`: MicroPythonのC API（`mp_obj_type_t`）を利用し、C言語の構造体をPythonクラスとして実機に公開するバインディング。
- 動作確認: Dockerを用いたファームウェアビルドの実行と、実機へのフラッシュ・動作テスト。

### Phase 4: WASM バインディング (Web)
Core EngineをWebブラウザ上で動作させます。
- [NEW] `scripts/build_engine_wasm.ps1`: `emcc`を用いたWASMビルドスクリプト。
- [NEW] `engine/hal/engine_wasm.js`: WASMモジュールをラップするJS側インターフェース。
- 動作確認: ブラウザ上での描画テスト。

## Verification Plan
各Phaseの完了時に、それぞれの環境（C言語単体 / PC / Cardputer実機 / WASM）でグラフィック（矩形、スプライト、テキスト）が正しく描画されることを確認します。
