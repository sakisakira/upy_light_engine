# パフォーマンス・プロファイリング計画

FPSが9から改善しない真のボトルネックを特定するため、MicroPython実機環境（Cardputer）での精密なプロファイリングを実施する計画です。

## 1. 目的と背景
- SPI通信のチャンク化（135回→5回）やViper内部ループの最適化を行ってもFPSが全く変動しなかったため、「別の箇所で決定的な処理落ち（ハードブロック）」が発生している可能性が極めて高い。
- 「推測するな、計測せよ」の原則に基づき、MicroPythonの `utime.ticks_us()` を用いたミリ秒/マイクロ秒単位の計測器（プロファイラ）をエンジンに組み込み、各処理の所要時間を可視化します。

## 2. プロファイリング対象（仮説）
現在のテストスクリプト（`main.py`）において、以下のどれが真のボトルネックなのかを特定します。

1. **ガベージコレクション（GC）**
   - 毎フレームごとに一時オブジェクト（Tuple等）が大量生成され、MicroPythonのヒープが枯渇して強制GCが走っている可能性（とくに `font_lib.text` 内の `blt` 呼び出しによる `args` タプル生成）。
2. **描画（draw）ループ全体**
   - `fb.screen.sprite`（スプライトの回転・スケーリング描画）
   - `font_lib.text_shadowed`（フォントの透過描画・重ね描き）
   - `fb.screen.rect`（矩形塗りつぶし）
3. **転送処理**
   - `display.show(screen.buffer)` の実行時間（INDEX8からRGB565への変換とSPI転送時間）
4. **その他のオーバーヘッド**
   - Python関数呼び出しのオーバーヘッド、Viperとのコンテキストスイッチなど。

## 3. 実装計画

### Step 1: プロファイラユーティリティの作成
新規モジュール `engine/profiler.py` に、以下のような軽量な計測用マネージャを作成します。
```python
import utime

class Profiler:
    def __init__(self):
        self.stats = {}
        self.enabled = True
    
    def start(self, name):
        if self.enabled:
            self.stats[name] = utime.ticks_us()
        
    def end(self, name):
        if self.enabled and name in self.stats:
            duration = utime.ticks_diff(utime.ticks_us(), self.stats[name])
            print(f"[PROFILE] {name}: {duration / 1000.0:.2f} ms")
            
profiler = Profiler()
```

### Step 2: コアループへの計測ポイントの埋め込み
`engine/hal/framebuffer_micropython.py` の `run()` 関数内の `while True:` ループに計測ポイントを仕込みます。
```python
            from engine.profiler import profiler
            import gc
            
            # ...
            profiler.start("update")
            update()
            profiler.end("update")
            
            profiler.start("draw_all")
            draw()
            profiler.end("draw_all")
            
            profiler.start("display_show")
            display.show(screen.buffer)
            profiler.end("display_show")
            
            profiler.start("gc")
            gc.collect()
            profiler.end("gc")
            print(f"Free Mem: {gc.mem_free()}")
```

### Step 3: `main.py` の `draw()` 関数内の詳細計測
`main.py` の `draw()` 関数内で、どの描画命令が重いのかを個別に計測します。
```python
    from engine.profiler import profiler
    
    profiler.start("draw_rects")
    # 背景と矩形の描画...
    profiler.end("draw_rects")

    profiler.start("draw_sprites")
    # スプライトの描画...
    profiler.end("draw_sprites")

    profiler.start("draw_text")
    # テキスト（とくにシャドウ付き）の描画...
    profiler.end("draw_text")
```

## 4. プロファイリング後の最適化アプローチ（Zero-Allocation Viper）
もしプロファイリングの結果、ボトルネックが「1」のGC（Tuple等の大量生成）であった場合、Cモジュール化に踏み切る前に、**MicroPythonの `array` モジュールを用いた構造体渡し（参照渡し）アプローチ** を試行します。

- **仕組み**: 
  1. エンジンの初期化時に `array.array('i', [0]*16)` のように再利用可能なメモリブロック（C言語の構造体や配列に相当）を一度だけ確保する。
  2. `sprite` や `blt` メソッド呼び出し時は、タプルを生成せず、この配列の中身の値を上書きする。
  3. Viper関数側では引数を `args_buf` として受け取り、`args = ptr32(args_buf)` としてポインタ経由で各数値を高速に読み出す。
- **期待される効果**: この手法により、フレーム毎のメモリ確保（アロケーション）が完全にゼロになり、GCの停止時間を排除できます。PythonのコードのままでありながらC言語に匹敵するパフォーマンス向上が見込まれます。

## 5. 確認手順
1. 本プロファイリング用のコードを実装。
2. Cardputer実機環境で実行し、シリアルコンソールのログ出力から各ブロックの消費ミリ秒（ms）を記録。
3. ボトルネックがGCと判明した場合は、上記4の `array.array` を用いた最適化を先行して実装・検証する。
4. 根本的な演算能力の不足であった場合は、Cモジュール（`_graphics_engine`）の実装に切り替える。
