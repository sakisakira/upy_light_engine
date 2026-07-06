# Walkthrough 30 Phase 4: WASM 移植とCPythonアーキテクチャの統合

このドキュメントでは、`upy_light_engine` の WASM/Pyodide への移植（Phase 4）の成功、および CPython（Windows/Mac）と Web（WASM）の HAL（ハードウェア抽象化レイヤー）を統一する上で必要だった重要なクロスプラットフォーム対応・バグ修正についてまとめます。

## 1. `ctypes` バインディングレイヤーの統合

DRY（Don't Repeat Yourself）の原則に従い、これまで `framebuffer_cpython.py` にベタ書きされていた生の `ctypes` マッピングを、統合された [engine_ctypes.py](file:///d:/sakira/work/cardputer/upy_light_engine/engine/hal/engine_ctypes.py) に分離しました。現在、`framebuffer_wasm.py` と `framebuffer_cpython.py` の両方が、ここで定義されたベースクラスを継承して動作しています。

### 32ビット/64ビットのポインタ切り捨てバグの解決

移植の過程で、64ビット版 Windows においてディスプレイリストのポインタを使用する際、致命的な `Access Violation`（アクセス違反）によるクラッシュが発生しました。
- **問題:** Pyodide（WASM）の `ctypes` 実装において、`POINTER(X)` オブジェクトを JS/WASM 境界でやり取りする際の既知のバグを避けるため、ポインタを一時的に `ctypes.c_uint32` として型付けしていました。しかし、64ビット Windows 環境では `dl_create()` は64ビットのメモリアドレスを返します。これを `c_uint32` にキャストすることで上位32ビットが切り捨てられ、結果として C言語側が無効なメモリ領域に書き込みを行っていました。
- **解決策:** `c_uint32` となっていたすべてのポインタ参照を `ctypes.c_void_p` に置き換えました。`c_void_p` は、実行環境のアーキテクチャ（WASMでは32ビット、Windows x64では64ビット）に動的に適合する「不透明な整数/ポインタのハイブリッド」として機能し、かつ Pyodide の構造体ポインタバグを回避できます。
- **可読性の確保:** `argtypes` や `_fields_` における型情報をドキュメントとして残すため、型エイリアス（例: `CDisplayList_p = ctypes.c_void_p`）を定義し、実行時のメモリ安全性とコードの可読性の両立を達成しました。

## 2. 動的な解像度変更と古いポインタの修正

`engine.init(120, 120)` のように解像度を動的に変更した際、Web環境とPC環境の両方でクラッシュするか、画像が激しく歪むという大きなバグが発見されました。
- **問題:** `framebuffer_wasm.py` と `framebuffer_cpython.py` は、解像度が変更されると `_c_fb.buffer` の裏にある `bytearray` を再作成していましたが、ディスプレイリスト（描画コマンドのバッファ）は**古い**フレームバッファのメモリを指したままになっていました。
- **解決策:** `engine_ctypes.py` 内に `reinit(width, height)` メソッドを導入しました。解像度が変更された場合、新しいメモリアドレスで `_c_fb.buffer` を更新し、**明示的に `core.dl_clear()` を呼び出す** ことで、古いメモリを対象としていた保留中の描画コマンドを安全に破棄するようにしました。
- さらに、`framebuffer_wasm.py` 側の JavaScript における `ImageData` の割り当てが `240x135` にハードコードされていた問題を修正し、幅と高さを動的に読み取るようにしたことで、「画像が歪んで二重に表示される」グリッチが解消されました。

## 3. Emscripten による WASM ビルド

Emscripten を使用して `c_modules/core/*.c` を WebAssembly のサイドモジュール（`build/core_engine.so`）としてコンパイルする `scripts/build_engine_wasm.ps1` を実装しました。
- Pyodide が `ctypes.CDLL()` 経由で Cライブラリを動的にロードできるように、`SIDE_MODULE=1` オプションを使用しています。
- エクスポートする関数は `EXPORTED_FUNCTIONS` で明示的に指定しています。

## 4. 機能のパリティ（同等性）に関する修正

### Web環境でのフォント描画
Web上でテキストが表示されていませんでした。原因は、`engine.font` が Emscripten 環境で文字ルックアップテーブル（`_c_lookup`）の構築を明示的にスキップしていたためです（MicroPythonと同じ挙動を想定していたため）。Emscripten でも `_c_lookup` の生成を有効にし、C言語エンジンが文字コードをフォントグリフにマッピングできるように修正しました。

### Web Audio API によるサウンドの減衰（エンベロープ）
WASM版のサウンドバックエンド（`sound_wasm.py`）は、C言語のソフトウェアシンセサイザー（`sound_engine.c`）に比べ、減衰がなく単調なオルガンのような音が鳴っていました。
- `sound_engine.c` を確認したところ、`0.5` 秒かけて線形に音量が減衰する処理が入っていることがわかりました。
- そこで、Web Audio API の `linearRampToValueAtTime` を用いてこの挙動を再現し、Web上でも全く同じ減衰特性（ベルやピアノのような余韻）を持たせました。

### キー入力の割り当て
`input_wasm.py` を更新し、`コンマ (,)` と `ピリオド (.)` キーをそれぞれ `X` ボタンと `Y` ボタンにマッピングし、PC版のキーバインドと完全に一致させました。

## 検証結果
- `core_engine.dll` は Windows x64 上で正常にビルド・実行されます。
- `core_engine.so` はローカルのWebサーバー（Pyodide）上で正常にビルド・実行されます。
- サウンド、フォント、コントローラーの操作感は、両プラットフォームで完全に同一に動作します。

## 関連計画
* サウンドのC言語化およびAudioWorkletを用いた同期・統一については、[Plan 36: WASM版のサウンドエンジン統一 (AudioWorklet化)](file:///d:/sakira/work/cardputer/upy_light_engine/docs/plans/plan_36_wasm_audio_worklet.md) にて後続開発として実施します。
