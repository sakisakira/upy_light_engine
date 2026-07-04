# MicroPython Firmware Integration (plan_30 Phase 3)

このフェーズでは、Phase 1 で構築したPure Cのコアエンジン（`core`）を、Cardputer実機上で動くMicroPythonファームウェアに「User C Module」として組み込みます。

## Core 0 (Python) / Core 1 (Engine) の分離と使い勝手

現在のPhase 3の計画を、ゲーム側の使いやすさとCore分離の想定に合わせてアップデートします。

1. **エンジンの初期化とCore 1常駐タスク**
   - `_lightengine.init()` が呼ばれると、FreeRTOSの `xTaskCreatePinnedToCore` を使って**Core 1** に描画専用タスクを立ち上げます。
2. **描画リクエストの送信 (`_lightengine.submit_display_list`)**
   - Python（Core 0）は、ディスプレイリストに描画コマンドを詰め込んだ後、この関数を呼びます。
   - 関数は FreeRTOS のキュー等を使ってCore 1へシグナルを送り、すぐに処理をPythonに返します。これにより完全な並行処理が実現します。

### Pythonからの構造体アクセス（使い勝手の向上）と堅牢性の担保

ゲーム制作時の使い勝手を最優先し、Pythonから直接プロパティを読み書きできるようにします。

- **`Sprite` クラス**: 
  - `sprite.u = 16` のように、Pythonから直接 `u, v, w, h` を書き換えられるよう、MicroPythonの `attr` ハンドラを用いて**プロパティ（アクセサ）をフルサポート**します。
- **マルチスレッドでのレースコンディション対策（重要）**:
  - 現在のC言語コア（`engine_types.h`）の `dl_push_draw_sprite` は、コマンド内に `EngineSprite *`（ポインタ）を保存する仕様になっています。このままでは、Pythonが `sprite.u` を書き換えた瞬間に、裏側で描画中だったCore 1が古いフレームで新しい `u` の値を読み取ってしまう「値の書き換わり（レースコンディション）」が発生します。
  - **対策:** 今回のフェーズでC言語コア側にも手を入れて、`dl_push_draw_sprite` が呼ばれた瞬間に、ポインタを保存するのではなく**スプライトの持つ `image, u, v, w, h, colkey` をコマンド構造体の中に「値として（By Value）」コピーしてスナップショット化**するように変更します。
  - 値のコピー自体はただの数個の整数のコピーなので、パフォーマンスには全く悪影響を与えずに完全な堅牢性を確保できます。

## Proposed Changes

### [NEW] `c_modules/port_micropython/micropython.cmake`
- `modlightengine.c` と `core/*.c` をビルド対象とするCMake設定。

### [NEW] `c_modules/port_micropython/modlightengine.c`
- MicroPython C APIを用いて各構造体をラップ。
- `Sprite` の `u, v, w, h` にアクセスするためのプロパティ機構（`attr`）を実装。
- `DisplayList` 用の `push_*` メソッド群を提供。
- Core 1 に `render_task` を立ち上げる `init()` メソッドと、描画キューを送信する `submit_display_list()` の実装。

### [MODIFY] `c_modules/core/engine_types.h` / `.c`
- `RenderCommand` の `draw_sprite` 共用体から `EngineSprite *sprite` を外し、代わりに `EngineImage *img`, `int16_t u, v, w, h` 等を直接保持するように変更。
- `dl_push_draw_sprite` の実装を変更し、引数で渡された `Sprite` ポインタからその時点の値をコピーして DisplayList に積むように修正。

### [NEW] `c_modules/micropython.cmake`
- `sound_engine` と `port_micropython` の両方のモジュールを読み込む親CMake。

### [MODIFY] `scripts/build_c_module.ps1`
- `USER_C_MODULES` の指定を上記の親CMakeに向くように変更。

## Verification Plan

### Automated Tests
- 今回は実機ファームウェアのビルドがメインとなるため、自動テストはありません。

### Manual Verification
- `scripts/build_c_module.ps1` を実行し、Docker環境でビルドが成功（エラーが出ないこと）を確認します。
