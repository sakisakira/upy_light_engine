import sys

class Image:
    """
    Container holding image (sprite) data in INDEX8 format.
    Platform-independent.
    """
    def __init__(self, width, height, buffer=None):
        self.width = width
        self.height = height
        self.format = "INDEX8"
        if buffer is None:
            self.buffer = bytearray(width * height)
        else:
            self.buffer = buffer
            
        # CPython software rendering optimization (1 byte per pixel = B)
        if sys.implementation.name != 'micropython':
            self._mv = memoryview(self.buffer).cast('B')

    _cache = {}

    @classmethod
    def load(cls, filename):
        if filename in cls._cache:
            return cls._cache[filename]
            
        try:
            import struct
        except ImportError:
            import ustruct as struct
        with open(filename, "rb") as f:
            header = f.read(10)
            if header[:4] != b"UIMG":
                raise ValueError("Invalid UIMG magic")
            if header[4] != 2:
                raise ValueError("Unsupported UIMG version (expected v2 INDEX8)")
            width, height = struct.unpack("<HH", header[6:10])
            data = bytearray(width * height)
            f.readinto(data)
            
        img = cls(width, height, data)
        cls._cache[filename] = img
        return img

    def subimage(self, u, v, w, h, colkey=0, tint=None):
        from .sprite import Sprite
        return Sprite(self, u, v, w, h, colkey, tint)
