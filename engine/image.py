import sys

class ImageBufferManager:
    def __init__(self, size_or_buffer):
        if type(size_or_buffer) is int:
            self.buffer = bytearray(size_or_buffer)
        else:
            self.buffer = size_or_buffer
        self.offset = 0
        
    def alloc(self, size):
        if self.offset + size > len(self.buffer):
            return None
        mv = memoryview(self.buffer)[self.offset : self.offset + size]
        self.offset += size
        return mv
        
    def reset(self):
        self.offset = 0

_global_buffer_manager = None

def set_global_buffer_manager(manager):
    global _global_buffer_manager
    _global_buffer_manager = manager


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
        else:
            from .hal.engine_ctypes import CEngineImage
            import ctypes
            self._c_image = CEngineImage()
            self._c_image.width = self.width
            self._c_image.height = self.height
            self._c_image.format = 2 # kFormatIndex8
            self._c_data = (ctypes.c_uint8 * len(self.data)).from_buffer(self.data)
            self._c_image.data = ctypes.addressof(self._c_data)

    _cache = {}

    @classmethod
    def clear_cache(cls):
        cls._cache.clear()
        if _global_buffer_manager is not None:
            _global_buffer_manager.reset()
        
    @classmethod
    def load(cls, filename, buffer=None):
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
            
            if buffer is None and _global_buffer_manager is not None:
                buffer = _global_buffer_manager.alloc(width * height)

            if buffer is None:
                data = bytearray(width * height)
            else:
                if len(buffer) < width * height:
                    raise ValueError("Buffer too small for image")
                data = buffer[:width*height]
                
            f.readinto(data)
            
        img = cls(width, height, data)
        cls._cache[filename] = img
        return img

    def subimage(self, u, v, w, h, colkey=0, tint=None):
        from .sprite import Sprite
        return Sprite(self, u, v, w, h, colkey, tint)
