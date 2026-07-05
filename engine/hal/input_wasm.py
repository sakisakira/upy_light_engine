# input_wasm.py
from engine.constants import *

try:
    import js
    from pyodide.ffi import create_proxy
except ImportError:
    pass

# JS KeyboardEvent.code mapping
_js_to_key = {
    "KeyW": Button_Up,
    "KeyA": Button_Left,
    "KeyS": Button_Down,
    "KeyD": Button_Right,
    "KeyN": Button_A,
    "KeyM": Button_B,
    "Comma": Button_X,
    "Period": Button_Y,
    "Space": Button_Select,
    "Enter": Button_Start,
    
    # Arrow keys as aliases for convenience
    "ArrowLeft": Button_Left,
    "ArrowRight": Button_Right,
    "ArrowUp": Button_Up,
    "ArrowDown": Button_Down
}

_key_state = {k: False for k in range(10)}

def _on_keydown(e):
    if e.code in _js_to_key:
        _key_state[_js_to_key[e.code]] = True
        # Prevent default scrolling for game keys
        e.preventDefault()

def _on_keyup(e):
    if e.code in _js_to_key:
        _key_state[_js_to_key[e.code]] = False
        e.preventDefault()

_proxy_keydown = None
_proxy_keyup = None

def init():
    global _proxy_keydown, _proxy_keyup
    _proxy_keydown = create_proxy(_on_keydown)
    _proxy_keyup = create_proxy(_on_keyup)
    js.window.addEventListener("keydown", _proxy_keydown)
    js.window.addEventListener("keyup", _proxy_keyup)

def set_key_mapping(mapping):
    global _js_to_key
    # User can pass a mapping like {"KeyW": Button_UP}
    for js_code, btn in mapping.items():
        _js_to_key[js_code] = btn

def button(btn):
    return _key_state.get(btn, False)
