from engine.constants import *

# PC Tkinter mapping
_tk_to_key = {
    'w': Key_W,
    'a': Key_A,
    's': Key_S,
    'd': Key_D,
    'n': Key_N,
    'm': Key_M,
    'h': Key_H,
    'j': Key_J,
    'space': Key_Space,
    'Return': Key_Enter
}

# PC bindings for logical buttons
_button_to_key = {
    Button_Up: Key_W,
    Button_Down: Key_S,
    Button_Left: Key_A,
    Button_Right: Key_D,
    Button_A: Key_N,
    Button_B: Key_M,
    Button_X: Key_H,
    Button_Y: Key_J,
    Button_Start: Key_Enter,
    Button_Select: Key_Space
}

# Current state of physical keys
_keys_pressed = set()

def set_key_mapping(key_const, key_names):
    """Not strictly needed since we use fixed physical key mapping, but kept for compatibility."""
    pass

def init(root=None, canvas=None):
    if root is None:
        return

    def on_key_press(event):
        key = _tk_to_key.get(event.keysym.lower() if event.keysym.lower() in _tk_to_key else event.keysym)
        if key is not None:
            _keys_pressed.add(key)
        
    def on_key_release(event):
        key = _tk_to_key.get(event.keysym.lower() if event.keysym.lower() in _tk_to_key else event.keysym)
        if key in _keys_pressed:
            _keys_pressed.remove(key)

    root.bind('<KeyPress>', on_key_press)
    root.bind('<KeyRelease>', on_key_release)

def button(btn_const):
    """Check if a logical game button or physical key is pressed."""
    key_const = _button_to_key.get(btn_const, btn_const)
    return key_const in _keys_pressed
