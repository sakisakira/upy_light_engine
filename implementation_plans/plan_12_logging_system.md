# ログ出力制御の仕組み (Logging System)

記録日時: 2026-06-21 09:26

デバッグや開発中にコンソールに出力されるログ（例えば「Engine Running... Frame: X」や初期化の通過ログなど）を、一括でオン・オフ（有効化・無効化）できる仕組みを導入します。

## Open Questions / User Review Required
* **モジュール名と配置**: 今回はエンジンのルートディレクトリに `logger.py` を新設する案にしていますが、`config.py` などに全体の設定フラグとして持たせる方式や、`debug.py` といった名前にする方式など、お好みの形はありますか？

## Proposed Changes

MicroPythonのメモリ制限を考慮し、標準の `logging` モジュールのような重い仕組みは避け、自前で極めて軽量な仕組みを用意します。

### [NEW] `logger.py`
シンプルなフラグで出力を切り替えられるモジュールを作成します。

```python
# logger.py
DEBUG_ENABLED = True

def debug(*args, **kwargs):
    """デバッグ用ログ。DEBUG_ENABLED が True のときだけ出力される"""
    if DEBUG_ENABLED:
        print(*args, **kwargs)

def info(*args, **kwargs):
    """情報ログ。常に表示される"""
    print(*args, **kwargs)

def error(*args, **kwargs):
    """エラーログ"""
    print("ERROR:", *args, **kwargs)
```

### [MODIFY] `hal/framebuffer_micropython.py`
先日追加したデバッグ用の `print` 文を `logger.debug` に置き換えます。
これにより、ログ出力をオフにしたい時は `logger.DEBUG_ENABLED = False` にするだけで、毎フレームの処理負荷を最小限に抑えられます。

```python
import logger

# ...
def run(update, draw, fps=30):
    logger.debug("Entering run() function...")
    # ...
    while True:
        # ...
        if frame_count % 60 == 0:
            logger.debug(f"Engine Running... Frame: {frame_count}")
```

### [MODIFY] `main.py`
デバッグ用に追加した `print("test X: ...")` なども `logger.debug` に変更します。
ゲームの初期化部分で `logger.DEBUG_ENABLED = True` （本番リリース時は `False`）に設定するサンプルコードを追加します。

## Verification Plan
1. `main.py` にて `logger.DEBUG_ENABLED = True` と `False` の両方を設定し、実機（Cardputer）上で `mpremote run main.py` を実行する。
2. `True` の時は今まで通りログが出力され、`False` の時はログが完全に非表示になる（無駄な通信が発生しない）ことを確認する。
