# 実装計画 - PNGからUIMG変換テストの追加

Cardputer ADV実機側の入力実装は一旦保留とし、**PNGからUIMG変換の検証テストのみ**を実装します。

---

## 変更予定内容

### 1. 変換ツールのリファクタリング
#### [tools/png2uimg.py](file:///Users/sakira/work/Cardputer/upy_light_engine/tools/png2uimg.py)
- `main()` 関数内にあった変換ロジックを、引数を受け取って動く `convert_png_to_uimg(png_path, uimg_path)` 関数として外に切り出します。
- `main()` は単に引数のパースを行い、この関数を呼び出すようにします。

### 2. テストの追加
#### [tests/test_png2uimg.py](file:///Users/sakira/work/Cardputer/upy_light_engine/tests/test_png2uimg.py)
PNGからUIMGへの変換、および変換されたファイルの読み込みを検証する単体テストを実装します。
- Pillow (`PIL.Image`) を使用して、テスト用の 8x8 ピクセルのカラーグラデーションPNG画像（透明アルファ値あり）を生成し、`test_png2uimg_input.png` として保存します。
- `tools.png2uimg.convert_png_to_uimg` を呼び出して `test_png2uimg_output.uimg` に変換します。
- [image.py](file:///Users/sakira/work/Cardputer/upy_light_engine/image.py) の `Image.load()` を使って変換後の UIMG ファイルをロードします。
- ロードした `Image` オブジェクトのサイズが 8x8 であること、フォーマットが `ARGB4444` であること、および元のピクセル（8ビットから4ビットへのダウンサンプリング値）が正しくバイナリに格納されているかをアサート検証します。
- **後処理**: 生成された `test_png2uimg_output.uimg` は削除しますが、入力元の `test_png2uimg_input.png` は確認用に残します。

---

## 検証計画

### 自動テスト
- 以下のコマンドで単体テストを実行します：
  ```bash
  python -m unittest discover -s tests
  ```
  新しく追加された `test_png2uimg` を含むすべてのテストが正常にパスすることを確認します。
