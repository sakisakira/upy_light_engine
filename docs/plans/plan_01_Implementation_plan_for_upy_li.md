"# `upy_light_engine` 実装計画

本計画は、`TODO.md` の更新内容に基づき、当面の優先目標である `upy_light_engine` ディレクトリの実装方針をまとめたものです。
最終的には `../motorcycle_pyxel/` を `motorcycle_cardputer` として移植するための土台となる機能を提供します。

## User Review Required

実装を進めるにあたり、以下の4つの主要タスクの中から、どれを最初に着手するかを決定したいと考えています。ご意見をお聞かせください。

> [!IMPORTANT]
> どのタスクから着手するか、あるいは別の優先事項があるか教えてください。
> 個人的には、画面の描画基盤となる「2. 画像フォーマットと変換ツール」または「1. Framebuffer拡張」から始めるのがスムーズかと考えています。

## Open Questions

> [!NOTE]
> * **画像フォーマット:** 拡張子は `.uimg` (MicroPython Imageの略) のような独自形式で進めてもよろしいでしょうか？
> * **キーマッピング:** PC側のテスト用に、ゲームパッド（XInputなど）の対応も最初から組み込むべきか、最初はキーボードマッピングのみで進めるべきかご希望はありますか？
> * **サウンド:** `motorcycle_pyxel` では `pyxel.play` や `pyxel.playm` などが使われています。今回は1音の矩形波（PWM）などを想定したシンプルなAPI（例: `hal.sound.play(freq, duration)`）からのスタートでよろしいでしょうか？

---

## Proposed Changes

### 1. Framebuffer の ARGB4444 対応拡張
現在RGB565ベースで実装されている描画処理に対して、`TODO.md`の要件通り、ゲーム側からは ARGB4444 として扱えるように整備します。

#### [MODIFY] `hal/framebuffer_cpython.py`
#### [MODIFY] `hal/framebuffer_micropython.py`
* `fill()` および `rect()` がゲーム側から渡される ARGB4444 フォーマット
<truncated 2559 bytes>