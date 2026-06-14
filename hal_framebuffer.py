import sys

if sys.implementation.name == 'micropython':
    from hal_framebuffer_micropython import *
else:
    from hal_framebuffer_cpython import *

def color(r, g, b, a=255):
    """
    一般的な8bit(0-255)の色指定から、内部フォーマットのARGB4444を生成するユーティリティ。
    例: color(255, 0, 0) -> 0xF00 (不透明な赤)
    """
    return ((a >> 4) << 12) | ((r >> 4) << 8) | ((g >> 4) << 4) | (b >> 4)
