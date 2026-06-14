import sys

class Image:
    """
    Container holding image (sprite) data in ARGB4444 format.
    Platform-independent.
    """
    def __init__(self, width, height, buffer=None):
        self.width = width
        self.height = height
        self.format = "ARGB4444"
        if buffer is None:
            self.buffer = bytearray(width * height * 2)
        else:
            self.buffer = buffer
            
        # CPython software rendering optimization
        if sys.implementation.name != 'micropython':
            self._mv = memoryview(self.buffer).cast('H')

    @classmethod
    def load(cls, filename):
        try:
            import struct
        except ImportError:
            import ustruct as struct
        with open(filename, "rb") as f:
            header = f.read(10)
            if header[:4] != b"UIMG":
                raise ValueError("Invalid UIMG magic")
            width, height = struct.unpack("<HH", header[6:10])
            data = bytearray(f.read(width * height * 2))
        return cls(width, height, data)
