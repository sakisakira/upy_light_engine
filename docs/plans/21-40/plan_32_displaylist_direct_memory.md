# Plan 32: DisplayList Direct Memory Access (Viper/memoryview)

現在、毎フレームの描画処理において、Pythonから `_lightengine.DisplayList.push_draw_sprite(...)` などのC言語バインディング関数が大量に呼ばれています。これらの関数呼び出しには、引数のパースや型変換のオーバーヘッドが伴います。
本計画では、C言語側で確保している `DisplayList->commands` のメモリブロック（固定長配列）のポインタを、Python側に `bytearray` の参照（コピーなし）として直接公開します。これにより、Python側から `ustruct.pack_into` や `@micropython.viper` の生ポインタ操作を用いて、関数呼び出しのオーバーヘッドなしでバイナリデータを直接メモリに書き込めるようにします。

## User Review Required

> [!IMPORTANT]
> **前提条件の確認**: 現在47FPSで頭打ちになっている原因が、「本当にPythonからのC API呼び出しオーバーヘッド（仮説2）によるものか」を、実装前に確実に確認する必要があります。
> 実は `main.py` の163行目でプロファイラが強制的に無効化（`profiler.enabled = False`）されており、コンソールに `draw_all`（Python側のAPI呼び出し時間）と `sync`（Core 1側の描画完了待ち時間）の計測結果が表示されていません。
> もし `sync` に大半の時間がかかっていた場合、ボトルネックはCore 1側（描画自体、またはSPI転送）にあり、**本計画を実行してもFPSは1ミリも上がりません。**
> そのため、本計画の【フェーズ1】として、必ずプロファイリングによる計測を先に行います。

## Open Questions

> [!WARNING]
> もし事前のプロファイリング結果で `sync`（Core 1待ち）がボトルネックだった場合、本計画（フェーズ2以降のPythonコードの複雑化）は費用対効果がないためキャンセルし、「SPIクロックの引き上げ」や「Core 1描画アルゴリズムのさらなる最適化」など別のアプローチに切り替えるべきだと考えますが、その方針でよろしいでしょうか？

## Proposed Changes

### Phase 1: ボトルネックの特定（プロファイリング）

#### [MODIFY] [main.py](file:///d:/sakira/work/cardputer/upy_light_engine/main.py)
- `draw()` 関数内の `profiler.enabled = False` を削除（または `True` に変更）し、`update` だけでなく `draw_all` と `sync` の所要時間がコンソールに出力されるようにする。

---

### Phase 2: メモリ直接書き込みの実装（ボトルネックが `draw_all` だった場合のみ実施）

#### [MODIFY] [modlightengine.c](file:///d:/sakira/work/cardputer/upy_light_engine/c_modules/port_micropython/modlightengine.c)
- `DisplayList` クラスに新メソッド `buffer()` を追加。
- `mp_obj_new_bytearray_by_ref` を用いて、ヒープ上の `commands` 配列のメモリ領域をコピーせずに Python 側に共有する。

#### [MODIFY] [framebuffer_micropython.py](file:///d:/sakira/work/cardputer/upy_light_engine/engine/hal/framebuffer_micropython.py)
- 初期化時に `self._raw_buffer = self.dl.buffer()` で共有メモリを取得。
- `sprite()` や `rect()` 等の各種描画APIを改修し、C関数を呼ぶ代わりに `ustruct.pack_into` などを利用して、バイナリ形式の `RenderCommand` 構造体を直接メモリにパックする処理に書き換える。

## Verification Plan

### Manual Verification
1. 【Phase 1】 `main.py` のプロファイラを有効化後、ユーザーに Cardputer 上で実行してもらい、コンソールログから `draw_all` と `sync` の時間を提出してもらう。
2. その結果に基づき、Phase 2 に進むか、別の計画に切り替えるかを判断する。
