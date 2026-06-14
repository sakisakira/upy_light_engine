import framebuf
try:
    import micropython
except ImportError:
    pass

class Image:
    """
    Lightweight container holding image (sprite) data in ARGB4444 format
    In MicroPython, it does not inherit from FrameBuffer to minimize overhead
    """
    def __init__(self, width, height, buffer=None):
        self.width = width
        self.height = height
        self.format = "ARGB4444"
        if buffer is None:
            self.buffer = bytearray(width * height * 2)
        else:
            self.buffer = buffer

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

class Framebuffer(framebuf.FrameBuffer):
    """
    Screen buffer in RGB565 format
    Inherits standard framebuf, allowing direct use of fill, rect, text, etc.
    """
    def __init__(self, width, height, buffer=None):
        self.width = width
        self.height = height
        self.format = "RGB565"
        if buffer is None:
            self.buffer = bytearray(width * height * 2)
        else:
            self.buffer = buffer
        # Initialize parent class as RGB565 format
        super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)

    def _col4444_to_565(self, col):
        r = (col >> 8) & 15
        g = (col >> 4) & 15
        b = col & 15
        return (((r << 1) | (r >> 3)) << 11) | (((g << 2) | (g >> 2)) << 5) | ((b << 1) | (b >> 3))

    def clear(self, col=0):
        self.fill_565(col)

    def fill_565(self, col):
        super().fill(col)
        
    def fill(self, col):
        self.fill_565(self._col4444_to_565(col))

    def rect_565(self, x, y, w, h, col, is_filled=True):
        if is_filled:
            self.fill_rect(x, y, w, h, col)
        else:
            super().rect(x, y, w, h, col)

    def rect(self, x, y, w, h, col, is_filled=True):
        self.rect_565(x, y, w, h, self._col4444_to_565(col), is_filled)

    def pset(self, x, y, col):
        super().pixel(x, y, self._col4444_to_565(col))

    def line(self, x1, y1, x2, y2, col):
        if x1 == x2:
            super().vline(x1, min(y1, y2), abs(y2 - y1) + 1, self._col4444_to_565(col))
        elif y1 == y2:
            super().hline(min(x1, x2), y1, abs(x2 - x1) + 1, self._col4444_to_565(col))
        else:
            return

    def blt(self, x, y, img, u, v, w, h, colkey=-1):
        """
        Switch blending process based on img format
        """
        is_argb = getattr(img, "format", "") == "ARGB4444"
        if is_argb:
            self._blt_viper_argb(x, y, img.buffer, img.width, u, v, w, h)
        else:
            self._blt_viper_rgb(x, y, img.buffer, img.width, u, v, w, h, colkey)

    @micropython.viper
    def _blt_viper_argb(self, x: int, y: int, src_buf, src_w: int, u: int, v: int, w: int, h: int):
        # Fast access with 16-bit pointer
        dst = ptr16(self.buffer)
        src = ptr16(src_buf)
        
        dst_w = int(self.width)
        dst_h = int(self.height)
        
        # Clipping (prevent out-of-bounds)
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
                
                # Decompose ARGB4444
                a = (src_val >> 12) & 15
                if a == 0:
                    continue
                    
                r = (src_val >> 8) & 15
                g = (src_val >> 4) & 15
                b = src_val & 15
                
                # Expand to RGB565
                sr = (r << 1) | (r >> 3)
                sg = (g << 2) | (g >> 2)
                sb = (b << 1) | (b >> 3)
                
                dst_idx = dst_idx_base + j
                if a == 15:
                    dst[dst_idx] = (sr << 11) | (sg << 5) | sb
                    continue
                    
                dst_val = dst[dst_idx]
                dr = (dst_val >> 11) & 31
                dg = (dst_val >> 5) & 63
                db = dst_val & 31
                
                # Blending (Speed up using 16-a and >> 4 instead of division // 15)
                inv_a = 16 - a
                out_r = (sr * a + dr * inv_a) >> 4
                out_g = (sg * a + dg * inv_a) >> 4
                out_b = (sb * a + db * inv_a) >> 4
                
                dst[dst_idx] = (out_r << 11) | (out_g << 5) | out_b

    @micropython.viper
    def _blt_viper_rgb(self, x: int, y: int, src_buf, src_w: int, u: int, v: int, w: int, h: int, colkey: int):
        dst = ptr16(self.buffer)
        src = ptr16(src_buf)
        
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
                    dst[dst_idx_base + j] = src_val

screen = Framebuffer(240, 135)

def run(update, draw, fps=30):
    """
    Game loop for MicroPython environment
    * Separate process required to reflect drawn content to ST7789 on Cardputer, etc.
    """
    import time
    import machine
    
    # [Implementation Note]
    # SPI driver like ST7789 needs to be initialized here
    # 例: display = st7789.ST7789(...)
    
    while True:
        start = time.ticks_ms()
        
        update()
        draw()
        
        # Dummy screen reflection via SPI transfer
        # 例: display.show(screen.buffer)
        
        elapsed = time.ticks_diff(time.ticks_ms(), start)
        wait_ms = (1000 // fps) - elapsed
        if wait_ms > 0:
            time.sleep_ms(wait_ms)
