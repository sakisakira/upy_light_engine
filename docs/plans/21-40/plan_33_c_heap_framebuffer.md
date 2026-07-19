# PSRAMおよびMemoryError問題の修正

Cardputer（ESP32-S3FN8）にはPSRAMが搭載されていません。最近のダブルバッファリング対応により、ピクセルバッファの必要量が約65KB（32.4KBのバッファ2面）に増加しました。これをMicroPythonの `bytearray` で確保しようとした結果、（PSRAMがない場合の約130KBという制限により）Python側のヒープを使い果たし、起動時に `MemoryError` が発生していました。

本プランでは、フレームバッファのメモリ確保をMicroPythonのヒープから、ESP-IDFのC言語ヒープ（FreeRTOSのヒープ）へ移行します。C側のヒープにはまだ約300KBほどの十分なDMA対応SRAMが残っているため、この問題を根本的に解決できます。

## ユーザーレビューのお願い

以下の変更内容をご確認ください。問題なければ実行を許可してください。承認後、ファームウェアの修正・再ビルドを行い、Cardputerへの書き込みまで行います。

## 変更内容

### _lightengine Cモジュール

#### [MODIFY] [modlightengine.c](file:///d:/sakira/work/cardputer/upy_light_engine/c_modules/port_micropython/modlightengine.c)
- `framebuffer_make_new` 関数を修正し、`bytearray` 引数を省略（`None` を渡す）できるようにします。
- バッファ引数が `None`（`mp_const_none`）の場合、`heap_caps_malloc(size, MALLOC_CAP_DMA | MALLOC_CAP_8BIT)` を使用してC言語ヒープ上に直接ピクセルバッファを確保します。
- ESP-IDFのメモリ確保APIを使用するため `esp_heap_caps.h` をインクルードします。

### Pythonレイヤー

#### [MODIFY] [framebuffer_micropython.py](file:///d:/sakira/work/cardputer/upy_light_engine/engine/hal/framebuffer_micropython.py)
- `Framebuffer.__init__` で `bytearray(width * height)` を作成しないように変更します。
- `buffer` 引数が `None` の場合、`_lightengine.Framebuffer` の初期化時に `None` を渡し、Cモジュール内部でメモリを自動確保させます。

### ビルドスクリプト

#### [MODIFY] [build_c_module.ps1](file:///d:/sakira/work/cardputer/upy_light_engine/scripts/build_c_module.ps1)
- ESP32-S3FN8（PSRAMなし）向けの正しいビルドとなるよう、`BOARD_VARIANT=SPIRAM_OCT` を削除します。*(この変更は既に直前のステップで完了しています)*

## 検証計画

### 自動テスト
- `build_c_module.ps1` を実行し、PSRAMなしの環境で正常にビルドできることを確認します。
- ファームウェアをデバイスに書き込みます。

### 手動テスト
- `run_on_cardputer.ps1` を実行します。
- `MemoryError` が発生せず、60 FPSで安定して描画ループが実行されることを確認します。
