class Sprite:
    """
    High-level logical view of an image (or part of an image) for rendering.
    Holds reference to an Image (texture), clipping region, and color parameters.
    """
    def __init__(self, image, u, v, w, h, colkey=0, tint=None):
        self.image = image
        self.u = int(u)
        self.v = int(v)
        self.w = int(w)
        self.h = int(h)
        self.colkey = colkey
        self.tint = tint
        
        import sys
        if sys.platform == 'esp32':
            import _lightengine
            if hasattr(self.image, '_c_image'):
                self._c_sprite = _lightengine.Sprite(self.image._c_image, self.u, self.v, self.w, self.h, self.colkey)
        else:
            from .hal.engine_ctypes import CEngineSprite
            import ctypes
            self._c_sprite = CEngineSprite()
            if hasattr(self.image, '_c_image'):
                self._c_sprite.image = ctypes.pointer(self.image._c_image)
            self._c_sprite.u = self.u
            self._c_sprite.v = self.v
            self._c_sprite.w = self.w
            self._c_sprite.h = self.h
            self._c_sprite.colkey = self.colkey
