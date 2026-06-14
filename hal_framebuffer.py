import sys

if sys.implementation.name == 'micropython':
    from hal_framebuffer_micropython import *
else:
    from hal_framebuffer_cpython import *
