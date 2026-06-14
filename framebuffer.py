import sys

if sys.implementation.name == 'micropython':
    from hal.framebuffer_micropython import Framebuffer, screen, run
else:
    from hal.framebuffer_cpython import Framebuffer, screen, run

def color(r, g, b, a=255):
    """
    Utility to generate the internal format ARGB4444 from common 8-bit (0-255) color specifications.
    Example: color(255, 0, 0) -> 0xF00 (Opaque Red)
    """
    return ((a >> 4) << 12) | ((r >> 4) << 8) | ((g >> 4) << 4) | (b >> 4)
