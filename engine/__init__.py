from .palette import colors_api as colors
from . import framebuffer
from . import sound

import sys

if sys.platform == 'esp32':
    from engine.hal.engine_micropython import run as _hal_run
elif sys.platform == 'emscripten':
    from engine.hal.engine_wasm import run as _hal_run
else:
    from engine.hal.engine_cpython import run as _hal_run

def update():
    sound.update()

def run(user_update, user_draw, fps=30):
    def wrapped_update():
        user_update()
        update() # calls sound.update()
        
    _hal_run(wrapped_update, user_draw, fps=fps)