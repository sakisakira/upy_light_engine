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
            self.data = bytearray(width * height)
        else:
            self.data = buffer
        self._mv = memoryview(self.data)
        
        import sys
        if sys.platform == 'esp32':
            import _lightengine
            self._c_image = _lightengine.Image(self.width, self.height, 2, self.data)
        elif sys.platform == 'emscripten':
            pass
        else:
            from .hal.engine_cpython import CEngineImage
            import ctypes
            self._c_image = CEngineImage()
            self._c_image.width = self.width
            self._c_image.height = self.height
            self._c_image.format = 2 # kFormatIndex8
            self._c_data = (ctypes.c_uint8 * len(self.data)).from_buffer(self.data)
            self._c_image.data = ctypes.cast(self._c_data, ctypes.POINTER(ctypes.c_uint8))

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
