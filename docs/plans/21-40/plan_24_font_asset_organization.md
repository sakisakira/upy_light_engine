# アセットディレクトリの整理（フォント）

## 背景と目的
現在 `assets/fonts/` ディレクトリ内に、手描きのソース画像 (PNG)、自動生成されたプレビュー画像 (PNG)、ゲームエンジンで実際に読み込まれるアセット (AFNT) が混在しています。
これにより、ソース画像とプレビュー画像のファイル名が衝突して上書きされる危険性があるほか、現在使われていない古いテスト用アセットが散乱しており、ファイル構成の把握が困難になっています。
これらを整理し、明確に分離します。

## Proposed Changes

### 1. `tools/font_converter.py` の修正
変換スクリプトが生成する確認用のプレビュー画像を、元のAFNTと同じディレクトリではなく、専用の `previews/` サブディレクトリに自動で出力するように変更します。
* 対象関数: `convert_png` および `convert_font`
* 変更内容: `preview_path` を生成する際、`out_path` の親ディレクトリの下に `previews/` フォルダを作成（存在しなければ）し、そこに保存するように修正。

### 2. ディレクトリ構造の再編
`assets/fonts/` 以下のファイルを適切にフォルダ分け・整理します。

#### [NEW] `assets/fonts/src/`
フォントの元データ（ソース）となるPNGファイルやBDFファイルなどを格納します。
* 移動対象:
  * `test_input_6px_font.png`
  * `test_16px_font.png` (※現在16pxフォントのソースとして機能しているもの)

#### [NEW] `assets/fonts/previews/`
プレビュー用の画像（自動生成されるもの）を格納します。
* 既存のプレビューPNG（`score_font_preview.png`, `test_6px_font.png` 等）は、再度自動生成されるため今回はすべて削除し、ディレクトリをクリーンな状態にします。

#### [DELETE] 不要なレガシーファイルの削除
現在どこからも参照されていない、過去のテスト段階で生成された不要な `.afnt` や `.png` ファイルを一掃します。
* 削除対象の例:
  * `score_font.afnt`
  * `score_font_half.afnt`, `score_font_quarter.afnt` およびその関連PNG群
  * `test_16px_custom.afnt`, `test_16px_custom.png`
  * その他 `_noshadow.png` 等の一時ファイル

### 3. エンジンでロードされる最終成果物
実際のゲームエンジンでロードされる `.afnt` ファイルは、パス指定の簡略化のため現状通り `assets/fonts/` の直下に配置します。
* 維持対象:
  * `test_6px_font.afnt`
  * `test_16px_font.afnt`

## Verification Plan
1. クリーンアップ後、`assets/fonts/` ディレクトリに `.afnt` と `src/`, `previews/` ディレクトリ以外が存在しないことを確認する。
2. `font_converter.py` を実行し、プレビュー画像が正しく `previews/` 内に生成されることを確認する。
3. `main.py` を実行し、フォントファイルが正しくロードされ、エラーなく描画されることを確認する。
