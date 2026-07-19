# Cardputer ADVキーボード（TCA8418）実装プラン

M5Stack Cardputer ADVに搭載されている TCA8418（I2C接続のキーパッドスキャナ）を利用して、キーボード入力をゲーム機のボタン操作として取得できるように実装します。

## 概要
- テストスクリプトの結果から、キー行列の配線は単純な連番ではないことが分かりました（SpaceやEnterが想定外のKeycode 67/68に配置されているため）。
- そのため、ゲームで使用する主要なキー（`W`, `A`, `S`, `D`, `Space`, `Enter` 等）について、実測したKeycodeを個別にマッピングテーブルに登録する方式を採用します。
- これにより、物理キーを抽象化し、PC環境（CPython）と実機環境（MicroPython）で共通のゲーム入力インターフェースを提供します。

## Proposed Changes

### constants.py (新規作成/修正)

プラットフォームに依存しない「物理キー」のIDと、ゲームの「論理ボタン」のIDを定義します。

#### [MODIFY] [constants.py](file:///Users/sakira/work/Cardputer/upy_light_engine/constants.py)
- `KEY_W`, `KEY_A`, `KEY_S`, `KEY_D`, `KEY_SPACE`, `KEY_ENTER` などの物理キー定数を定義
- ゲーム操作用の論理ボタンとして `BUTTON_UP`, `BUTTON_DOWN`, `BUTTON_LEFT`, `BUTTON_RIGHT`, `BUTTON_A`, `BUTTON_B` などを定義

### input.py / hal層でのキーマッピング

PC向けとCardputer向けで、物理キーから論理ボタンへのマッピングを出し分けます。

#### [MODIFY] [input.py](file:///Users/sakira/work/Cardputer/upy_light_engine/input.py)
- 環境に応じて以下の初期マッピングを設定します。
- **Cardputer (MicroPython) 向け**:
  - `BUTTON_UP` = `KEY_W`, `BUTTON_LEFT` = `KEY_A`, `BUTTON_DOWN` = `KEY_S`, `BUTTON_RIGHT` = `KEY_D`
  - `BUTTON_A` = `KEY_SPACE`
  - `BUTTON_B` = `KEY_ENTER`
- **PC (CPython) 向け**:
  - `BUTTON_UP` = `KEY_W`, `BUTTON_LEFT` = `KEY_A`, `BUTTON_DOWN` = `KEY_S`, `BUTTON_RIGHT` = `KEY_D`
  - `BUTTON_A` = `KEY_N`
  - `BUTTON_B` = `KEY_M`

### hal/input_micropython.py

MicroPython環境向けの入力処理を実装します。

#### [MODIFY] [input_micropython.py](file:///Users/sakira/work/Cardputer/upy_light_engine/hal/input_micropython.py)
- I2C初期化および TCA8418 設定ルーチンの実装
- 実測した `Keycode` （例: Space=68, Enter=67 等）から `constants.py` の `KEY_*` へ変換する辞書（マッピングテーブル）の追加
- イベントを監視し、現在のキー状態（押されているかどうか）を管理する `button()` 関数の実装

### hal/input_cpython.py および main.py の追従

#### [MODIFY] [input_cpython.py](file:///Users/sakira/work/Cardputer/upy_light_engine/hal/input_cpython.py)
- Tkinterのキーイベント文字列（'w', 'space' 等）から `constants.py` の `KEY_*` へ変換するマッピングの追加
- `button()` 呼び出し時に論理ボタンから物理キー状態を引けるように修正

#### [MODIFY] [main.py](file:///Users/sakira/work/Cardputer/upy_light_engine/main.py)
- ゲームループ内の入力判定を `inp.KEY_LEFT` から `inp.BUTTON_LEFT` などに修正します。

## Verification Plan

### マッピング調査 (現在実行中)
- 実機（Cardputer ADV）で `tools/test_tca8418.py` を実行していただき、ゲームで必要なキー（`W`, `A`, `S`, `D`, `Space`, `Enter`）の正確な Keycode を教えていただきます。

### Manual Verification
- （マッピング判明・実装後）実機（Cardputer ADV）に転送し、実際に `W, A, S, D, Space, Enter` キーを押した際に `main.py` のスプライトが正しく上下左右に移動すること、およびA/Bボタンで背景色が変わることを確認します。
- PC上での実行時に `W, A, S, D, N, M` キーで同様の動作になることを確認します。
