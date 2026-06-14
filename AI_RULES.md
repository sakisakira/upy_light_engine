# AI Rules for upy_light_engine

* **レビューの記録**: コードレビューや設計変更が行われた際は、必ずその指摘内容と対応方針を `review_history.md` に追記してください。
* **依存関係の制限**: PC(CPython)環境でのテストにおいて、`pygame` や `numpy` などの巨大なライブラリの使用は避け、標準ライブラリや `Pillow` 程度の軽量なものに留めてください。
* **アーキテクチャ制約**: スプライト(ARGB4444)と画面バッファ(RGB565)はクラスを分離して管理し、実機(MicroPython/Cardputer)でのViperの活用やメモリ節約を常に意識した設計にしてください。
* **命名規則**: HALなどのモジュールは `hal_framebuffer.py`、`hal_framebuffer_cpython.py` のように用途ごとにプレフィックス(`hal_`)を統一して命名してください。
