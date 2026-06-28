# Viper sprite() 高速化計画

MicroPython環境（Cardputer）において、現在の `sprite()` 描画はフレームレート低下の主要因となっています。本計画では、重い演算を削減・回避するアルゴリズム改善を行い、Viper環境下での描画速度を劇的に向上させます。

## 目標
- `_sprite_viper_fast` の実行速度を大幅に向上させ、Cardputer実機でのFPSを改善する（目標: 安定して15FPS以上、可能なら30FPS）。
- エンジン側の修正に集中し、ゲーム側のロジック変更なしにパフォーマンスの恩恵を受けられるようにする。

## 提案する変更内容

### `upy_light_engine/engine/hal/framebuffer_micropython.py`

#### 1. `sprite` (Fast-Path の導入)
回転・拡大縮小が不要なスプライトは、重い座標変換処理（Viperループ）を一切通さずに、より軽量な `blt` メソッド（`_blt_viper_index8`）を直接呼び出すように変更します。
ゲーム内の「文字（テキスト）」「UI」「回転しない背景オブジェクトやキャラクター」の描画が劇的に軽くなります。

```python
    def sprite(self, cx, cy, spr, tint=None):
        # --- Fast Path ---
        # 回転なし・拡縮なしの場合は単純な矩形転送（blt）に逃がす
        if spr.rotate == 0 and spr.scale == 1.0:
            w = spr.w
            h = spr.h
            x = int(cx - w / 2)
            y = int(cy - h / 2)
            self.blt(x, y, spr.image, spr.u, spr.v, w, h, colkey=spr.colkey, tint=tint if tint is not None else spr.tint)
            return

        # 以降は従来の回転・拡縮ロジック...
```

#### 2. `_sprite_viper_fast` (DDAアルゴリズムの導入)
回転や拡縮が必要なスプライト（バイク本体など）の処理において、最も実行回数の多い内側のループ（X軸、1ピクセルごとの処理）の中から「掛け算」を排除し、「足し算」のみでテクスチャ座標を更新する **DDA (Digital Differential Analyzer)** 手法に書き換えます。Viper上では整数加算は1サイクルで完了するため、乗算を排除することで劇的な高速化が期待できます。

```python
    @micropython.viper
    def _sprite_viper_fast(self, dst_buf, src_buf, args):
        # ... 前半の変数準備 ...
        
        for dy in range(min_y, max_y):
            # ... Y座標系の基本計算 ...
            
            # 【変更点】 dxループに入る前に、開始点（dx = min_x）でのテクスチャ座標(sx_fp, sy_fp)を計算しておく
            dist_x_fp_start = (min_x << 8) - cx_fp
            sx_fp = ((dist_x_fp_start * cos_inv_fp) >> 8) + sx_base_fp
            sy_fp = ((dist_x_fp_start * sin_inv_fp) >> 8) + sy_base_fp
            
            for dx in range(min_x, max_x):
                # sx, sy はビットシフトだけで取り出す（ループ内での掛け算なし！）
                sx = sx_fp >> 8
                sy = sy_fp >> 8
                
                # 次のピクセルに向けてコサイン・サイン成分を「足し算」するだけ
                sx_fp += cos_inv_fp
                sy_fp += sin_inv_fp
                
                # 以降は従来のクリッピングとピクセル転送...
```

## 検証計画
1. 実装後、変更内容をエンジン側に適用。
2. （このフェーズではゲーム側の変更は行わない）
3. `run_on_cardputer.ps1` を用いて実機で実行し、ログに出力されるFPSの数値を確認して高速化の度合いを測定する。
4. 回転時の描画に丸め誤差による欠けや歪みが生じていないか、目視で確認する。
