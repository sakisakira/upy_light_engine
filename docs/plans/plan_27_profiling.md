# パフォーマンス・プロファイリング計画

FPSが9から改善しない真のボトルネックを特定するため、MicroPython実機環境（Cardputer）での精密なプロファイリングを実施する計画です。

## 1. 目的と背景
- SPI通信のチャンク化（135回→5回）やViper内部ループの最適化を行ってもFPSが全く変動しなかったため、「別の箇所で決定的な処理落ち（ハードブロック）」が発生している可能性が極めて高い。
- 「推測するな、計測せよ」の原則に基づき、MicroPythonの `utime.ticks_us()` を用いたミリ秒/マイクロ秒単位の計測器（プロファイラ）をエンジンに組み込み、各処理の所要時間を可視化します。

## 2. プロファイリング対象（仮説）
現在のテストスクリプト（`main.py`）において、以下のどれが真のボトルネックなのかを特定します。

1. **描画（draw）ループ全体**
   - `fb.screen.sprite`（スプライトの回転・スケーリング描画）
   - `font_lib.text_shadowed`（フォントの透過描画・重ね描き）
   - `fb.screen.rect`（矩形塗りつぶし）
2. **転送処理**
   - `display.show(screen.buffer)` の実行時間（SPIが本当に速くなっているかの裏付け）
3. **ガベージコレクション（GC）**
   - 毎フレームごとに一時オブジェクト（TupleやFloatなど）が大量生成され、MicroPythonのヒープが枯渇して強制GCが走っている可能性。
4. **その他のオーバーヘッド**
   - Python関数呼び出しのオーバーヘッド、Viperとのコンテキストスイッチなど。

## 3. 実装計画

### Step 1: プロファイラユーティリティの作成
`engine/time.py` または新規モジュール `engine/profiler.py` に、以下のような軽量な計測用コンテキストマネージャを作成します。
```python
import utime

class Profiler:
    def __init__(self):
        self.stats = {}
    
    def start(self, name):
        self.stats[name] = utime.ticks_us()
        
    def end(self, name):
        if name in self.stats:
            duration = utime.ticks_diff(utime.ticks_us(), self.stats[name])
            print(f"[PROFILE] {name}: {duration / 1000.0:.2f} ms")
```

### Step 2: `main.py` への計測ポイントの埋め込み
テストスクリプトの `while True:` ループ内に計測ポイントを仕込みます。
```python
profiler.start("update")
update()
profiler.end("update")

profiler.start("draw_all")
# さらに内部で sprite, text, rect を細かく計測
draw()
profiler.end("draw_all")

profiler.start("display_show")
display.show(screen.buffer)
profiler.end("display_show")

profiler.start("gc")
import gc
gc.collect()
profiler.end("gc")
```

### Step 3: GC（メモリ）の監視
- 毎フレーム `gc.mem_free()` の推移をログ出力し、メモリリークや急速なメモリ消費（メモリチャーン）が起きていないかを監視します。
- Viper内でTuple等のオブジェクト確保が頻発していると、一瞬でヒープが枯渇してガベージコレクションによる数ミリ秒〜数十ミリ秒のフリーズが発生します。

## 4. 確認手順（次回作業）
1. 本プロファイリング用のコードを実装・実機へ転送。
2. REPL（またはシリアルモニタ）のコンソールログを確認し、各ブロックの消費ミリ秒（ms）を記録。
3. 最も時間のかかっている箇所（ボトルネック）を特定した上で、次なる最適化アプローチ（Cモジュール化の対象にするか、Pythonの書き方を変えるか等）を再検討します。
