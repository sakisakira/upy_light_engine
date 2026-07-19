# Sprite最適化（Viper）とパフォーマンスの現状分析

本作業では、Cardputer（MicroPython）環境における描画の最大のボトルネックと目されていた `sprite()` メソッドのViper実装に対し、大幅なアルゴリズムの改善を行いました。同時に、テストスクリプトや実際のゲーム画面のFPS計測結果から、エンジンの限界とPythonコード側の新たなボトルネックを特定しました。

## 1. 変更内容

### `_sprite_viper_fast` の DDA化
回転・拡縮を含むスプライト描画において、最も実行回数の多い内側ループから乗算を排除する **DDA (Digital Differential Analyzer)** 手法を導入しました。
```python
# dxのループに入る前に、開始点でのテクスチャ座標を計算
dist_x_fp_start = (min_x << 8) - cx_fp
sx_fp = ((dist_x_fp_start * cos_inv_fp) >> 8) + sx_base_fp
sy_fp = ((dist_x_fp_start * sin_inv_fp) >> 8) + sy_base_fp

for dx in range(min_x, max_x):
    # 以降は加算とシフト演算のみでテクスチャ座標をトラッキング
    sx = sx_fp >> 8
    sy = sy_fp >> 8
    sx_fp += cos_inv_fp
    sy_fp += sin_inv_fp
```
これにより、エンジン側の限界負荷テストスクリプト (`upy_light_engine/main.py`) にて、画面全体にまたがる巨大な回転スプライトを3つ描画する処理が **8〜9 FPS** を達成し、Viperによる算術演算の劇的な高速化を証明しました。

### Fast-Path の導入と `_blt_viper_index8` の引数オーバーヘッド解消
回転 (`rotate=0.0`) や拡縮 (`scale=1.0`) を伴わないスプライト描画やテキスト描画は、Viperの複雑なアフィン変換を完全にバイパスして直接 `_blt_viper_index8` に逃がす Fast-Path を導入しました。

さらに、`_blt_viper_index8` が10個の引数を受け取っていたことにより、MicroPythonのViper関数呼び出しにおける「4引数以上はスタック渡し（またはタプル/Dict構築）になる」という強烈なオーバーヘッドが発生していたため、引数を1つの `args` タプルにパックして渡す仕様に変更しました。
これにより、文字描画を多用するゲームの **タイトル画面（最適化前 11〜12 FPS）** のさらなるフレームレート向上が見込まれます。
