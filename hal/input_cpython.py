from .input import *

_key_mapping = {
    KEY_UP: ['Up'],
    KEY_DOWN: ['Down'],
    KEY_LEFT: ['Left'],
    KEY_RIGHT: ['Right'],
    KEY_A: ['z', 'Z'],
    KEY_B: ['x', 'X'],
    KEY_X: ['a', 'A'],
    KEY_Y: ['s', 'S'],
    KEY_START: ['Return'],
    KEY_SELECT: ['Shift_L', 'Shift_R']
}

_key_state = {}

def set_key_mapping(key_const, key_names):
    """
    Override the default key mapping for a specific button.
    Example: set_key_mapping(KEY_A, ['space', 'z'])
    """
    _key_mapping[key_const] = key_names

def _on_key_press(event):
    _key_state[event.keysym] = True

def _on_key_release(event):
    if event.keysym in _key_state:
        _key_state[event.keysym] = False

def init(root, canvas):
    """Initialize input bindings on the given Tkinter root."""
    root.bind('<KeyPress>', _on_key_press)
    root.bind('<KeyRelease>', _on_key_release)

def button(key_const):
    """Check if the given key is currently pressed."""
    if key_const in _key_mapping:
        for keysym in _key_mapping[key_const]:
            if _key_state.get(keysym, False):
                return True
    return False
