# Phase 2: CPython(PC) DLL バインディング 実装計画

この計画書は `plan_30_c_cpp_engine_architecture.md` における **Phase 2** の実装詳細をカバーしています。純粋なC言語のコアエンジンをWindows用DLLとしてラップし、CPython PCエミュレータで使用するための `ctypes` バインディングを作成します。

## ユーザーレビュー / 確認事項
- **メモリ管理について**: C側の `DisplayList` は各構造体（`EngineSprite*`, `EngineImage*`, テキストのバイト列など）の「ポインタ」を保持します。Pythonのガベージコレクションによって描画（フレーム終端）より前にこれらが解放されてしまうのを防ぐため、Python側の `Framebuffer` ラッパー内に `_c_refs` というリストを設け、次のフレームでリストがクリアされるまで参照を維持（寿命を延ばす）する方針で実装します。このアプローチで問題ないでしょうか？
- **Line & Pset について**: 現在のCエンジンは `line` (直線) と `pset` (点) の描画コマンドをネイティブでサポートしていません。Cエンジン側に `kCmdLine` や `kCmdPset` を追加すべきでしょうか？それとも、現在のPython実装がやっているように「`fill_rect` を使って擬似的に描画する（psetは1x1の矩形、直線は垂直/水平な矩形）」というフォールバック方針を採用してC側の肥大化を防ぐ方が良いでしょうか？ *(提案: Cコアをシンプルに保つため、Python側で `dl_push_fill_rect` に変換する方針)*

## 提案する変更内容

### `scripts/build_engine_dll.ps1`
- **[NEW]**: `gcc` を呼び出して `c_modules/core/engine_types.c` と `c_modules/core/engine_render.c` をコンパイルし、`build/core_engine.dll` を生成するPowerShellスクリプトを作成します。

### `engine/hal/engine_cpython.py`
- **[NEW]**: `EngineImage`, `EngineSprite`, `EngineFramebuffer`, `DisplayList` などに対応する `ctypes.Structure` を定義します。
- **[NEW]**: `core_engine.dll` をロードし、`dl_init`, `dl_clear`, `dl_push_*`, `render_display_list` 等の引数・戻り値の型（`argtypes` / `restype`）を定義します。

### `engine/sprite.py` & `engine/hal/font.py` & `engine/image.py`
- **[MODIFY]**: `Image` や `Sprite` が CPython 環境でインスタンス化される際、対応するC構造体のインスタンス（例: `self._c_image`, `self._c_sprite`）も生成して保持するようにします。これにより、Pythonオブジェクトが存在する限りC構造体のメモリも保証されます。

### `engine/hal/framebuffer_cpython.py`
- **[MODIFY]**: `Framebuffer` クラスを改修し、初期化時にC側の `DisplayList` と `EngineFramebuffer` の構造体を生成するようにします。
- **[MODIFY]**: `clear()`, `fill()`, `rect()`, `sprite()`, `text()` などのメソッドを改修し、Pythonによるソフトウェアレンダリングループの代わりに `dl_push_*` を呼び出すようにします。
- **[MODIFY]**: `text()` に渡された文字列バイト列がレンダリング前にGCで回収されないよう、前述の `self._c_refs` リストに一時的に保持する処理を追加します。
- **[MODIFY]**: `_tick()` ループの最後に `render_display_list` を呼び出してキューに溜まったコマンドを一括描画（ラスタライズ）し、その後 `dl_clear()` を呼ぶようにします。

## 検証計画 (Verification Plan)

### 自動テスト (Automated Tests)
- `scripts/build_engine_dll.ps1` を実行し、DLLがエラーなくコンパイルされることを確認します。

### 手動検証 (Manual Verification)
- PCエミュレータ (`run_on_pc.ps1`) を実行します。クラッシュすることなく描画が正しく行われ、パフォーマンスが安定していることを目視確認します。
