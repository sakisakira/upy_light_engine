# [Goal Description]
Cモジュールビルド用のDocker環境構築

MicroPythonのCモジュール（サウンドIC制御などを想定）をビルドするため、環境に依存しないビルド環境を構築します。
公式のDev Containers拡張機能に依存せず、「Dockerfile」と「ビルド用スクリプト」を組み合わせる方式を採用し、手軽にビルドを実行・可視化できるようにします。

## Design Decisions
- **ベースイメージ**: ESP32-S3の開発ツールが揃っている `espressif/idf` をベースイメージとして使用します。
- **Cモジュールディレクトリ**: ソースコード格納用に `c_modules/` ディレクトリを新設します。
- **ビルドスクリプト**: Windows向けに `build_c_module.ps1` を作成します。
- **MicroPythonソースコード**: IDEでの自動補完（IntelliSense）を有効にし、ビルドバージョンを固定するため、ビルド時のcloneではなく `git submodule` としてローカルに取り込みます。

## Proposed Changes

### Docker環境とビルドスクリプト

Cモジュールビルドのための設定ファイルとディレクトリ、スクリプトを追加します。

#### [NEW] [c_modules/](file:///d:/sakira/work/cardputer/upy_light_engine/c_modules/)
Cモジュールのソースコードやビルド設定（`micropython.mk` 等）を格納する専用ディレクトリ。

#### [NEW] [Dockerfile](file:///d:/sakira/work/cardputer/upy_light_engine/Dockerfile)
MicroPythonの `mpy-cross` やCコンパイラ（gcc, build-essential等）をインストールした環境を構築する定義ファイル。

#### [NEW] [build_c_module.ps1](file:///d:/sakira/work/cardputer/upy_light_engine/build_c_module.ps1)
Windows向けのPowerShellスクリプト。内部でコンテナイメージのビルド（存在しない場合）と `docker run -v $PWD:/workspace ...` を実行し、Cモジュールをビルドします。

## Verification Plan

### Manual Verification
1. Docker Desktop等が起動していることを確認。
2. ターミナルから `.\build_c_module.ps1` を実行し、コンテナ内でビルドが成功してホスト側にコンパイル済みファイルが生成されることを確認。
