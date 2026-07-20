try:
    from enum import Enum, IntEnum, auto
except ImportError:
    class Enum:
        pass
    class IntEnum:
        pass
    _auto_idx = 0
    def auto():
        global _auto_idx
        _auto_idx += 1
        return _auto_idx

class CharaBodyIndex(Enum):
    Normal = auto()
    Succeeded = auto()
    Failed = auto()

class GameState(Enum):
    GameTitle = auto()
    GamePlay = auto()
    GameResult = auto()

class FaceIndex(IntEnum):
    Empty = -1
    Normal = 0
    Blink = auto()
    Astonish = auto()
    Smile = auto()
    Cry = auto()
