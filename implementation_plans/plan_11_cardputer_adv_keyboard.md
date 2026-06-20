# Cardputer ADVキーボード（TCA8418）実装プラン

M5Stack Cardputer ADVに搭載されている TCA8418（I2C接続のキーパッドスキャナ）を利用して、キーボード入力をゲーム機のボタン操作として取得できるように実装します。

## 概要
- テストスクリプトの結果から、キー行列は「左の列から右へ、上の行から下へ」と連番（1〜56）でマッピングされていることが完全に判明しました。
- この規則を利用して物理キーを抽象化し、PC環境（CPython）と実機環境（MicroPython）で共通のゲーム入力インターフェースを提供します。

## マッピング規則の解明結果
テスト結果から以下の規則が導き出せました：
`Keycode = (Col * 4) + Row + 1` (※ Col: 0~13, Row: 0~3)

主要キーのKeycodeは以下のようになります：
- `W`: Col 2, Row 1 -> **10**
- `A`: Col 2, Row 2 -> **11**
- `S`: Col 3, Row 2 -> **15**
- `D`: Col 4, Row 2 -> **19**
- `Space`: Col 13, Row 3 -> **56**
- `Enter`: Col 13, Row 2 -> **55**
- `N`: Col 8, Row 3 -> **36**
- `M`: Col 9, Row 3 -> **40**

## Proposed Changes

### constants.py (新規作成/修正)

プラットフォームに依存しない「物理キー」のIDと、ゲームの「論理ボタン」のIDを定義します。

#### [MODIFY] [constants.py](file:///Users/sakira/work/Cardputer/upy_light_engine/constants.py)
- `KEY_A` ~ `KEY_Z`, `KEY_SPACE`, `KEY_ENTER`, `KEY_ESC`, `KEY_N`, `KEY_M` などの物理キー定数（整数値など）を定義
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
- 実機の `Keycode` (1〜56) から `constants.py` の `KEY_*` へ変換する辞書（マッピングテーブル）の追加
- イベントを監視し、現在のキー状態（押されているかどうか）を管理する `button()` 関数の実装

### hal/input_cpython.py および main.py の追従

#### [MODIFY] [input_cpython.py](file:///Users/sakira/work/Cardputer/upy_light_engine/hal/input_cpython.py)
- Tkinterのキーイベント文字列（'w', 'space' 等）から `constants.py` の `KEY_*` へ変換するマッピングの追加
- `button()` 呼び出し時に論理ボタンから物理キー状態を引けるように修正

#### [MODIFY] [main.py](file:///Users/sakira/work/Cardputer/upy_light_engine/main.py)
- ゲームループ内の入力判定を `inp.KEY_LEFT` から `inp.BUTTON_LEFT` などに修正します。

## Verification Plan

- 実装後、CPython（PC環境）で `main.py` を実行し、`W, A, S, D` で移動、`N, M` で色が変わることを確認。
- MicroPython（Cardputer ADV）に転送し、`W, A, S, D` で移動、`Space, Enter` で色が変わることを確認。
