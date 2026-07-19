# サウンドシステム（単音ビープ・MML再生）実装プラン

ユーザーフィードバックを反映し、Cardputer ADV実機（ES8311コーデック＋NS4150Bアンプ）およびPC環境（Windows/macOS）で、外部ライブラリ（pygame等）に依存せずに効果音やBGMを鳴らすサウンドシステムを実装します。

## 概要
ゲームエンジンにおいて、サウンドは非常に重要です。まずは効果音のための「単音ビープ」と、BGMのための「MML (Music Macro Language) 再生機能」を実装します。

## Proposed Changes

### 1. サウンドAPIの抽象化 (`sound.py`)
ゲーム側から呼び出すための共通インターフェースを定義し、プラットフォーム（`sys.platform`）に応じて適切なHALを動的に読み込みます。

#### [NEW] `sound.py`
- `play_tone(freq, duration_ms)`: 指定した周波数と時間で単音を鳴らす。
- `play_mml(mml_string)`: 指定されたMML文字列（例: `"T120 O4 C4 D4 E4"`) をバックグラウンドで再生開始する。
- `update()`: エンジンのメインループから毎フレーム呼ばれ、MMLの再生状態（次の音符への切り替え等）を非同期に管理する。

### 2. PC向け軽量HALの実装 (`hal/sound_cpython_mac.py`, `hal/sound_cpython_win.py`)
`pygame` などの重い外部ライブラリを避け、OS標準の機能を用いて **非同期（ゲームループを止めない）** サウンド再生を実現します。

両OS共通の工夫として、指定された周波数と長さから「正弦波（または矩形波）のWAVバイナリデータ」をPython標準ライブラリ（`struct`, `wave`等）でメモリ上に動的生成します。

#### [NEW] `hal/sound_cpython_mac.py`
- macOS専用のHAL。
- 動的生成したWAVデータを一時ファイル（`/tmp/upy_light_engine_beep.wav` など）に保存し、Mac標準コマンドである `afplay` を `subprocess.Popen` で非同期に呼び出して再生します。

#### [NEW] `hal/sound_cpython_win.py`
- Windows専用のHAL。
- Windows標準の `winsound` モジュールを使用します。（`winsound.Beep` は処理をブロックしてしまうため、動的生成したWAVデータを `winsound.PlaySound(data, winsound.SND_MEMORY | winsound.SND_ASYNC)` に渡すことで非同期再生を実現します）

### 3. Cardputer向け実装 (`hal/sound_micropython.py` & カスタムCモジュール)
Cardputer（ESP32-S3）向けには、開発者の目的に応じて選べる**「2つの選択肢」**を提供する設計とします。これにより、ゲーム配布時の手軽さ（公式ファームウェアのまま）と、ゲームプレイ時の快適さ（ノイズレス）を天秤にかけて最適な戦略をとることができます。

#### [NEW] `c_modules/sound_engine` (Native Module: 本命)
- C言語のFreeRTOSタスクを用いて、バックグラウンドでI2Sのオーディオバッファ（BGMや効果音）を合成・転送し続けるネイティブモジュール。
- GCの停止時間（10〜30ms）の影響を受けず、60FPSのゲームループを邪魔せずにノイズレスな音声を再生します。
- **特定完了したハードウェア仕様**:
  - I2Sピン: BCLK=41, WS=43, DOUT=42
  - I2Cピン: SDA=8, SCL=9 (ES8311初期化用)
  - アンプの専用ENピンは存在せず、ES8311経由で内部的に制御されます。

#### [NEW] `hal/sound_micropython.py` (uPy I2C: HAL層・選択肢)
- デフォルトでは起動時に `import _sound_engine` を試行し、存在すればCモジュール版を使用します。
- **公式ファームウェアでの配布オプション**: Cモジュールが存在しない場合、あるいは明示的に `force_mode="bare_i2s"` を指定された場合は、**純粋な `machine.I2S` と `machine.I2C` を用いたPython単体での再生（Bare I2S）** を実行します。
- ES8311のMCLK生成（BCLKから生成）やアンプ有効化などの厳密な初期化レジスタ送信をPython側から行います。

### 4. 【検証済】Web (WASM) 向け実装の将来的な展望 (`hal/sound_web.py`)
今回実装は行いませんが、このアーキテクチャが将来的にWeb環境（PyScriptやMicroPython WASM等）でも成立するかを検証しました。
- **成立の可否**: 全く問題なく成立します。
- **理由**:
  1. `sound.py` のインターフェース（`play_tone`, `play_mml`）は完全にプラットフォーム非依存です。
  2. MML文字列を解析して `(周波数, ミリ秒)` に変換する `mml_parser.py` は純粋なPythonコードなので、WASM上でもそのまま動きます。
  3. 将来的に追加する `sound_web.py` の中では、WASMのJavaScript相互運用機能（例: `import js` や `pyodide.ffi`）を用いて、Web標準の **Web Audio API (`OscillatorNode` 等)** を呼び出すだけで済みます。OSのプロセス依存やファイルIO依存がないため、最も親和性が高いです。

### 5. MMLパーサー (`mml_parser.py`)
MML文字列を解析し、周波数と発音時間のリストに変換する軽量なパーサーを実装します。

#### [NEW] `mml_parser.py`
- サポートするコマンド:
  - `CDEFGAB` (+ `#` `-`): 音階（シャープ、フラット対応）
  - `O`: オクターブ変更 (0-8)
  - `T`: テンポ変更 (BPM)
  - `L`: デフォルトの音符の長さ
  - `R`: 休符
- 正規表現またはシンプルな文字列スキャンで解析し、`(freq, duration_ms)` のリストを返す設計とします。

### 6. エンジンへの組み込み (`engine.py`)
- エンジンのメインループ（`run()`内）で `sound.update()` を毎フレーム呼び出し、MMLの自動演奏（次の音符への切り替え）が処理されるようにします。

---

## User Review Required

ご要望通り、PC環境では外部ライブラリを一切使わず、Windows標準の `winsound` と macOS標準の `afplay` コマンドを活用する軽量な実装設計に修正し、HALもOSごとに切り離しました。この方針で問題ないかご確認をお願いします！

## Verification Plan

### 自動/単体テスト
- `tests/test_mml.py` を作成し、MML文字列が正しい周波数・時間にパースされるかを検証します。

### 手動テスト (Manual Verification)
1. **PC環境**: `tests/test_sound.py` をMacあるいはWindowsで実行し、エラーなく音が鳴る（またはMMLが再生される）ことを確認します。
2. **実機環境**: 同様のスクリプトをCardputer ADV上で実行し、ES8311の初期化が成功し、スピーカーから音が鳴ることを確認します。Native Module版とuPy I2C版の両方を確認します。
