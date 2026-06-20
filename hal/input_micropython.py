import machine
from constants import *

I2C_ADDR = 0x34
i2c = None

# Hardware keycode to physical key mapping
_hw_to_key = {
    12: Key_W,
    13: Key_A,
    17: Key_S,
    23: Key_D,
    68: Key_Space,
    67: Key_Enter
}

# Cardputer bindings for logical buttons
_button_to_key = {
    Button_Up: Key_W,
    Button_Down: Key_S,
    Button_Left: Key_A,
    Button_Right: Key_D,
    Button_A: Key_Space,
    Button_B: Key_Enter
}

_keys_pressed = set()

def set_key_mapping(key_const, key_names):
    pass

def init(root=None, canvas=None):
    global i2c
    try:
        i2c = machine.I2C(0, scl=machine.Pin(9), sda=machine.Pin(8), freq=400000)
        # Check if device exists
        if I2C_ADDR in i2c.scan():
            # Configure TCA8418
            i2c.writeto_mem(I2C_ADDR, 0x01, b'\x01') # Enable KE_IEN
            i2c.writeto_mem(I2C_ADDR, 0x1D, b'\xFF') # Rows
            i2c.writeto_mem(I2C_ADDR, 0x1E, b'\xFF') # Cols
            i2c.writeto_mem(I2C_ADDR, 0x1F, b'\xFF') # Cols
        else:
            i2c = None
    except Exception:
        i2c = None

def _poll_events():
    if not i2c:
        return
    try:
        ec_data = i2c.readfrom_mem(I2C_ADDR, 0x03, 1)
        event_count = ec_data[0] & 0x0F
        if event_count > 0:
            for _ in range(event_count):
                key_event = i2c.readfrom_mem(I2C_ADDR, 0x04, 1)[0]
                pressed = (key_event & 0x80) != 0
                keycode = key_event & 0x7F
                if keycode in _hw_to_key:
                    k = _hw_to_key[keycode]
                    if pressed:
                        _keys_pressed.add(k)
                    else:
                        if k in _keys_pressed:
                            _keys_pressed.remove(k)
    except Exception:
        pass

def button(btn_const):
    """Check if a logical game button or physical key is pressed."""
    _poll_events()
    key_const = _button_to_key.get(btn_const, btn_const)
    return key_const in _keys_pressed
