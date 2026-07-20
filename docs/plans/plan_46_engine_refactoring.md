# [Engine Plan 46: サウンドエンベロープの復元とアーキテクチャのリファクタリング]

デバッグ過程で判明したサウンドエンジンの課題（音符の繋がり・ノイズの持続）への対応、およびフレームバッファモジュールの責務違反（ゲームループの混入）を解決するためのエンジン側の改修計画です。

## User Review Required

- 以下の変更はデバッグの流れで既に実装・ビルドまで進行していますが、正式な計画としてここに定義し、事後承認をお願いする形となります。
- MML拡張（`E<num>` などでのエンベロープ指定）は本プランには含めず、将来のTODOとして扱います。

## Open Questions

- 特にありません。

## Proposed Changes

### 1. サウンドエンベロープ（ADSR風減衰）の再実装

`decay_samples` バグ修正の副作用として失われた「音の分離」と「減衰（ノコギリ波風のアタック）」を、正しい形でC言語シーケンサー内に再実装します。

#### [MODIFY] [c_modules/core/sound_synth.h](file:///d:/sakira/work/cardputer/upy_light_engine/c_modules/core/sound_synth.h)
- トラック構造体 `sound_synth_ubgm_track_t` に、現在の音符の総サンプル数を保持する `total_samples` を追加します。

#### [MODIFY] [c_modules/core/sound_synth.c](file:///d:/sakira/work/cardputer/upy_light_engine/c_modules/core/sound_synth.c)
- `_ubgm_fetch_next_note` にて、音符の総サンプル数を `total_samples` に記録します。
- `sound_synth_mix_sample` にて、再生開始から0.5秒かけて音量を落とす（アタック〜ディケイ）処理を追加します。
- サスティン（減衰後の維持音量）として、ノイズ（打楽器）は `0.0`（完全に消える）、それ以外のトーンは `0.4` を設定します。
- 音符の終わりの50ミリ秒で強制的に音量をゼロへ向かわせる（リリース）処理を追加し、連続する同音程の音符を分離します。

### 2. ゲームループ構造のリファクタリング（責務の分離）

`framebuffer_*.py` に記述されていたウィンドウ生成やゲームループ処理を抽出し、適切なモジュールへ移動します。

#### [NEW] [engine/hal/engine_micropython.py](file:///d:/sakira/work/cardputer/upy_light_engine/engine/hal/engine_micropython.py)
#### [NEW] [engine/hal/engine_cpython.py](file:///d:/sakira/work/cardputer/upy_light_engine/engine/hal/engine_cpython.py)
#### [NEW] [engine/hal/engine_wasm.py](file:///d:/sakira/work/cardputer/upy_light_engine/engine/hal/engine_wasm.py)
- `framebuffer_*.py` から `init()`, `run()`, `title()`, `_tick()` 等のアプリケーションライフサイクルを司る関数群を移動し、各プラットフォームごとのエンジン挙動を定義します。

#### [MODIFY] [engine/hal/framebuffer_*.py]
- 上記のゲームループ処理を削除し、純粋な `Framebuffer` クラス（とグローバルな `screen` インスタンス）の定義のみを残します。

#### [MODIFY] [engine/__init__.py](file:///d:/sakira/work/cardputer/upy_light_engine/engine/__init__.py)
- `run()` 関数のディスパッチ元を `framebuffer_*.py` から、新設した `engine_*.py` へ変更します。

## Verification Plan

### Automated Tests
- WASM および ESP32 (Cardputer Adv) 用のビルドを実行し、正常にコンパイルが通ることを確認します。

### Manual Verification
- CPython / WASM / ESP32 の全プラットフォームで、BGMのエンベロープ（アタック感と音の分離）が意図通りに機能していることを確認します。
- ゲームループの分離後も、全プラットフォームでゲームが正常に起動し、描画とサウンドが機能することを確認します。
