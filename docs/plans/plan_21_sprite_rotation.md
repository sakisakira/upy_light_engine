# Sprite API の回転対応 (Rotate)

## Goal
エンジンの `sprite()` メソッドにおいて、引数 `rotate`（ラジアン指定）による画像の回転描画を実装します。アフィン変換（逆マッピング）を用いて、ニアレストネイバー法による回転と拡縮を同時に行えるようにします。

## 概要
現在、`software_renderer.py` の `draw_sprite` メソッドは `scale` (拡縮) のみに対応しています。
引数 `rotate` に対応するためには、以下の2つの処理を変更する必要があります。

1. **バウンディングボックスの計算（描画範囲の決定）**
   元の画像の四隅の座標を中心に沿って `rotate` 回転・ `scale` 拡縮し、スクリーン上での最小・最大X/Y座標を求め、それを描画対象の矩形（バウンディングボックス）とします。

2. **ピクセルの逆マッピング計算**
   描画先の各ピクセル座標 `(dx, dy)` から、元の画像座標 `(sx, sy)` を計算する際に、逆回転 (`-rotate`) と逆スケール (`1.0 / scale`) を適用します。

Pythonのループ内で毎回 `sin`, `cos` を計算すると絶望的に遅くなるため、ループの外で三角関数の計算を済ませ、さらに内側ループで加算される定数部分を外側ループに引き出すことで最適化します。

## Proposed Changes

### [MODIFY] engine/hal/software_renderer.py
* `import math` を追加します。
* `draw_sprite` メソッド内のバウンディングボックス計算を四隅の回転計算に置き換えます。
```python
        cos_f = math.cos(rotate) * scale
        sin_f = math.sin(rotate) * scale
        hw, hh = w * 0.5, h * 0.5
        corners = [(hw, hh), (hw, -hh), (-hw, hh), (-hw, -hh)]
        # これらを回転させて min/max を取り、start_x, end_x 等を求める
```
* 逆マッピング用の定数を事前計算します。
```python
        inv_scale = 1.0 / scale
        cos_inv = math.cos(-rotate) * inv_scale
        sin_inv = math.sin(-rotate) * inv_scale
```
* ピクセル描画ループの中で、以下のように座標を逆算します。最適化のため `dy` に関する項は外側のループで事前計算します。
```python
        for dy in range(min_y, max_y):
            dist_y = dy - cy
            sx_base = -dist_y * sin_inv + w * 0.5
            sy_base =  dist_y * cos_inv + h * 0.5
            # ...
            for dx in range(min_x, max_x):
                dist_x = dx - cx
                sx = int((dist_x * cos_inv + sx_base) // 1)
                sy = int((dist_x * sin_inv + sy_base) // 1)
                # ...
```

### [MODIFY] main.py
* 動作確認のため、エンジン単体テストの `main.py` にあるアニメーション処理で、スプライトが回転するように `rotate` 引数を与えます（例：`rotate=frames * 0.05` など）。
* 回転の様子が視覚的にわかりやすいように、**非対称な図形（例えば各頂点の色がRGBで異なる三角形など）** をテスト用スプライトとして追加し、それを描画して回転させます。

## Verification Plan
### Automated Tests
* エンジン単体テスト `main.py` を実行し、エラーなく動作することを確認します。

### Manual Verification
* `main.py` を表示し、スプライトが中心を軸に綺麗に回転しながら描画されているか、また拡縮と同時に正しく描画されているかを目視で確認します。
* 四隅が欠けずにバウンディングボックスが正しく機能しているか確認します。
