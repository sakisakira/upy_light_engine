# Implementation Plan: scriptsディレクトリの整理 (Plan 38)
Date & Time: 2026-07-09T21:58:00+09:00

## Goal Description
`TODO.md` に記載されている「`scripts` ディレクトリ以下の煩雑さの解消」を行います。
具体的には、不要なスクリプトの整理、プラットフォーム名を明記した一貫性のあるファイル名への変更、各スクリプトへの英語コメントの追加、そして `README.md` の更新を実施します。

## User Review Required
スクリプトの新しい命名規則（プレフィックス `mpy_`, `pc_`, `wasm_`, `cardputer_` を付与）について、これで問題ないか確認をお願いします。

## Proposed Changes

### 1. `scripts` ディレクトリ内のファイル名変更 (Renaming)
プラットフォームや用途がひと目で分かるように、以下のようにリネームを行います。

* **MicroPython/Firmware 関連 (`mpy_`)**
  * [DELETE] `apply_patches.ps1` -> [NEW] `mpy_apply_patches.ps1`
  * [DELETE] `build_c_module.ps1` -> [NEW] `mpy_build_firmware.ps1`
  * [DELETE] `build_graphics_mpy.ps1` -> [NEW] `mpy_build_graphics.ps1`
  * [DELETE] `Dockerfile` -> [NEW] `mpy_build.Dockerfile`
* **PC環境 関連 (`pc_`)**
  * [DELETE] `build_engine_dll.ps1` -> [NEW] `pc_build_dll.ps1`
* **WASM/Web環境 関連 (`wasm_`)**
  * [DELETE] `build_engine_wasm.ps1` -> [NEW] `wasm_build.ps1`
  * [DELETE] `install_emsdk.ps1` -> [NEW] `wasm_install_emsdk.ps1`
  * [DELETE] `serve.py` -> [NEW] `wasm_serve.py`
* **実機(Cardputer)操作 関連 (`cardputer_`)**
  * [DELETE] `clean_cardputer.ps1` -> [NEW] `cardputer_clean.ps1`
  * [DELETE] `flash_firmware.ps1` -> [NEW] `cardputer_flash.ps1` (※ファームウェア書き込み)
  * [DELETE] `install_to_cardputer.ps1` -> [NEW] `cardputer_install.ps1` (※ファイル転送)
  * [DELETE] `run_on_cardputer.ps1` -> [NEW] `cardputer_run.ps1`

### 2. 英語コメントの追加
すべてのスクリプトの冒頭（1行目〜数行）に、「このスクリプトがどこで、何のために使われるものなのか」を英語で記述したコメント（ブロックコメントまたは行コメント）を追記します。

### 3. README.md の更新
#### [MODIFY] README.md
変更したスクリプト名に合わせて、`README.md` 内の実行コマンド例（`.\scripts\apply_patches.ps1` など）を新しいファイル名に更新し、ドキュメントの整合性を保ちます。

## Verification Plan
1. すべてのスクリプトのリネームとコメント追加が完了していること。
2. `README.md` 内の記述が新スクリプト名と一致していること。
3. リネームによって他のスクリプトからの呼び出し（スクリプト内部から別のスクリプトを呼んでいる箇所など）が壊れていないか、内容を確認・修正すること。
