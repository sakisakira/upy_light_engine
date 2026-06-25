try:
    from enum import IntEnum, auto
except ImportError:
    # MicroPython fallback if enum is not available
    class IntEnum:
        pass
    _auto_idx = 0
    def auto():
        global _auto_idx
        _auto_idx += 1
        return _auto_idx

class Key(IntEnum):
    W = auto()
    A = auto()
    S = auto()
    D = auto()
    N = auto()
    M = auto()
    Space = auto()
    Enter = auto()

class Button(IntEnum):
    Up = auto()
    Down = auto()
    Left = auto()
    Right = auto()
    A = auto()
    B = auto()
    X = auto()
    Y = auto()
    Start = auto()
    Select = auto()

# Physical Key Constants
Key_W = Key.W
Key_A = Key.A
Key_S = Key.S
Key_D = Key.D
Key_N = Key.N
Key_M = Key.M
Key_Space = Key.Space
Key_Enter = Key.Enter

# Logical Button Constants
Button_Up = Button.Up
Button_Down = Button.Down
Button_Left = Button.Left
Button_Right = Button.Right
Button_A = Button.A
Button_B = Button.B
Button_X = Button.X
Button_Y = Button.Y
Button_Start = Button.Start
Button_Select = Button.Select

