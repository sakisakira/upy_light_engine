import framebuf
try:
    import micropython
except ImportError:
    pass

class Framebuffer(framebuf.FrameBuffer):
    """
    Screen buffer in GS8 format (used as INDEX8)
    Inherits standard framebuf.
    """
    def __init__(self, width, height, buffer=None):
        self.width = width
        self.height = height
        self.format = "INDEX8"
        if buffer is None:
            self.buffer = bytearray(width * height)
        else:
            self.buffer = buffer
        # Initialize parent class as GS8 (8-bit grayscale, we treat it as palette index)
        super().__init__(self.buffer, self.width, self.height, framebuf.GS8)

    def clear(self, col=0):
        self.fill(col)

    def pset(self, x, y, col):
        super().pixel(x, y, col)

    def sprite(self, cx, cy, spr, rotate=0.0, scale=1.0):
        from .software_renderer import draw_sprite
        draw_sprite(self.buffer, self.width, self.height, cx, cy, spr.image.buffer, spr.image.width, spr.image.height, spr.u, spr.v, spr.w, spr.h, spr.colkey, rotate, scale, spr.tint)

    def blt(self, x, y, img, u, v, w, h, colkey=0, tint=None):
        self._blt_viper_index8(x, y, img.buffer, img.width, u, v, w, h, colkey, -1 if tint is None else tint)

    @micropython.viper
    def _blt_viper_index8(self, x: int, y: int, src_buf, src_w: int, u: int, v: int, w: int, h: int, colkey: int, tint: int):
        dst = ptr8(self.buffer)
        src = ptr8(src_buf)
        
        dst_w = int(self.width)
        dst_h = int(self.height)
        
        start_x = 0
        start_y = 0
        end_x = w
        end_y = h
        
        if x < 0:
            start_x = -x
        if y < 0:
            start_y = -y
        if x + w > dst_w:
            end_x = dst_w - x
        if y + h > dst_h:
            end_y = dst_h - y
            
        if start_x >= end_x or start_y >= end_y:
            return

        for i in range(start_y, end_y):
            dst_idx_base = (y + i) * dst_w + x
            src_idx_base = (v + i) * src_w + u
            
            for j in range(start_x, end_x):
                src_val = src[src_idx_base + j]
                if src_val != colkey:
                    if tint != -1:
                        dst[dst_idx_base + j] = tint
                    else:
                        dst[dst_idx_base + j] = src_val

    def text(self, font, text, x, y, color=1, scale=1.0):
        if font.format == "INDEX8":
            dst_w = self.width
            dst_h = self.height
            char_w = 8
            char_h = 12
            
            for i, char in enumerate(text):
                code = ord(char)
                if code < 32 or code > 126:
                    code = 32
                idx = code - 32
                u = (idx % 16) * char_w
                v = (idx // 16) * char_h
                
                cx = x + i * char_w * scale + (char_w * scale * 0.5)
                cy = y + (char_h * scale * 0.5)
                
                from .software_renderer import draw_sprite
                draw_sprite(self.buffer, dst_w, dst_h, cx, cy, font.buffer, 128, 72, u, v, char_w, char_h, colkey=0, scale=scale, tint=color)
