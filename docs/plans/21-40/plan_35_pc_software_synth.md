# PC版ソフトウェアシンセサイザー (WAVレンダラー)

PC版のサウンドモジュール（`sound_cpython_win.py` および `sound_cpython_mac.py`）をアップグレードし、4和音のミキシング、各種波形、エンベロープ（音の減衰）に完全対応させます。PyAudioなどの外部ライブラリへの依存を避けつつ、メモリ上でWAVのバイト列を直接生成することで、Cardputer実機と全く同じ音質を実現します。

## 提案する変更

### `engine/hal/sound_synth.py` [新規]
マルチトラックの `notes` リストを受け取り、ミキシング済みの生のPCM 16-bit 44.1kHzオーディオを含む `bytearray` (WAVデータ) を生成する純粋なPythonシンセサイザーモジュールを作成します。
- `square`（矩形波）、`sawtooth`（ノコギリ波）、`triangle`（三角波）、`noise`（ノイズ）の波形を実装します。
- 線形減衰（リニアディケイ）エンベロープを実装します。
- 4つのチャンネルをミキシングし、音割れを防ぐためのソフトクリッピングを適用します。

### `engine/hal/sound_cpython_win.py` [変更]
- `play_sequence` メソッドを変更し、完成したWAVファイルのバイト列を返す `sound_synth.render_wav(tracks)` を呼び出すようにします。
- このバイト列を一時ファイルに保存し、`winsound.PlaySound` 経由で再生します。
- 古い単音の矩形波生成ロジックを削除します。

### `engine/hal/sound_cpython_mac.py` [変更]
- Windows版と同様に、`sound_synth.render_wav(tracks)` を使用してWAVデータを取得します。
- 一時ファイルに保存し、`afplay` 経由で再生します。
- 古い単音の矩形波ロジックを削除します。

## 確認計画
### 自動テスト
- PC上で `python main.py` を実行します。

### 手動確認
- PCシミュレータが、追加のライブラリ（pip install）を必要とせずに、4和音のMMLコード進行やBGMを正しい波形とエンベロープで完璧に再生できることを確認します。
