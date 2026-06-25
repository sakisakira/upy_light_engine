"# 機能追加: フォントの動的カラーリング

このプランでは、ご要望いただいた機能のうち「フォントの描画色を動的に変更する」機能の実装を行います。
（※ウィンドウのリサイズ対応は、Gitコミットを分けるため次のステップで実施します）

## レビューが必要な項目

- **APIの変更**: `hal.font.text` メソッドにオプション引数 `color=-1` を追加します。指定しない（または `-1`）場合は、AFNT画像が持つ本来の色で描画されます。
- **APIの変更**: `framebuffer.blt` メソッドにもオプション引数 `color=-1` を追加します。指定された場合、透過度（アルファチャンネル）は元の画像のものをそのまま使いつつ、RGB（色）は指定された色で上書き合成するようになります。

## 提案する変更内容

---

### `framebuffer.py`
ユーザー向けのFacadeクラス（窓口）に `color` 引数を追加し、下位モジュールに渡します。
#### [MODIFY] `framebuffer.py`
- `blt` の引数を `def blt(self, x, y, img, u, v, w, h, colkey=-1, color=-1):` に変更します。
- 内部の HAL呼び出し（`self.hal.blt(...)`）に `color` をそのまま渡します。

---

### `hal/font.py`
ユーザーから指定された色を `blt` メソッドに引き渡します。
#### [MODIFY] `hal/font.py`
- `text` の引数を `def text(screen, x, y, text_str, font, color=-1, spacing=1):` に変更します。
- 内部の `screen.blt` 呼び出し時に `color=color` を渡します。

---

### `hal/framebuffer_cpython.py`
PC向けのソフトウェアレンダラーに動的カラーリングのロジックを追加します。
#### [MODIFY] `hal/framebuffer_cpython.py`
- `blt` メソッドの引数に `color=-1` を追加します。
- ARGB画像のアルファブレンド処理（`is_argb`ブロック内）において、`if color != -1:` の判定を追加します。
- 色
<truncated 1281 bytes>