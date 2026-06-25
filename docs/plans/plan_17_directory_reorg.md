# プロジェクトディレクトリ再構成（リファクタリング）計画

Web機能（ネットワーク周りなど）の実装に入る前に、プロジェクトのディレクトリ構成を一般的なOSS（特にPythonやC拡張を含むゲームエンジン/フレームワーク）の標準的な構成に整理します。

現状はルートディレクトリにエンジンのコア機能（`*.py`）やビルドスクリプトが散乱しているため、これらを役割ごとに明確に分離します。

## Goal
プロジェクトのディレクトリ構成をクリーンアップし、**「エンジンコア」「アセット」「ドキュメント」「スクリプト」「C言語モジュール」** などの責務を分離する。また、不要になったファイルの削除を行います。

## Proposed Changes

以下のような一般的なOSS構成に変更します。

```text
upy_light_engine/
├── engine/             # (NEW) エンジンのコアPythonコード群
│   ├── hal/            # (MOVE) ハードウェア抽象化レイヤー
│   ├── constants.py
│   ├── framebuffer.py
│   ├── image.py
│   ├── input.py
│   ├── logger.py
│   ├── mml_parser.py
│   └── sound.py
├── c_modules/          # (KEEP) MicroPython用 カスタムCモジュール
├── assets/             # (NEW) リソースファイル群
│   ├── fonts/          # (MOVE) フォントデータ
│   └── images/         # (MOVE) 画像データ
├── docs/               # (NEW) ドキュメント群
│   ├── pitfalls/       # (MOVE) 旧 documents/ 
│   └── plans/          # (MOVE) 旧 implementation_plans/
├── scripts/            # (NEW) 開発・ビルド用スクリプト群
│   ├── Dockerfile
│   ├── build_c_module.ps1
│   └── apply_patches.ps1
├── tests/              # (KEEP) テストコード群
├── micropython/        # (KEEP) サブモジュール
├── patches/            # (KEEP) サブモジュール用パッチ
├── main.py             # (KEEP) ユーザーが書くゲームのエントリポイント
├── TODO.md             # (KEEP)
└── AI_RULES.md         # (KEEP)
```

### 具体的な変更内容

1. **`engine/` の新設と移動**:
   - エンジンのコア機能である `.py` ファイル群と `hal/` ディレクトリをすべて `engine/` ディレクトリ配下に移動します。
   - これにより、`main.py` からは `from engine import sound`, `import engine.framebuffer as fb` のようにインポートする形になり、ユーザーコードとエンジンコードが明確に分離されます。

2. **`assets/` の新設と移動**:
   - `fonts/` と `images/` を `assets/` 配下にまとめます。

3. **`docs/` の新設と統合**:
   - `documents/` を `docs/` にリネームします。
   - `implementation_plans/` を `docs/plans/` として中に移動させ、ドキュメント系を1箇所にまとめます。

4. **`scripts/` の新設と移動**:
   - ルートに散らかっている `Dockerfile`, `build_c_module.ps1`, `apply_patches.ps1` などをまとめます。

5. **不要ファイルの削除**:
   - 役目を終えた `Speaker_Class.cpp` を削除します。

6. **コード内のパス・インポート修正**:
   - `main.py` や `tests/*.py` 内のインポート文（`import sound` → `from engine import sound` など）を修正します。
   - `main.py` 内の画像・フォント読み込みパスを `assets/images/...` などに修正します。

## Verification Plan
1. すべてのファイルを新しいディレクトリ構成に移動。
2. インポートパスとファイル読み込みパスを修正。
3. PC版で `python main.py` または `python tests/test_mml_pc.py` を実行し、インポートエラーやファイル参照エラーが起きないことを確認する。
