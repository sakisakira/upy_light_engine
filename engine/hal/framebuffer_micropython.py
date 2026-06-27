import framebuf
try:
    import micropython
except ImportError:
    pass


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
        rgb565 = (((r << 1) | (r >> 3)) << 11) | (((g << 2) | (g >> 2)) << 5) | ((b << 1) | (b >> 3))
        # Pre-swap for ST7789 Big Endian SPI format
        return ((rgb565 & 0xFF) << 8) | (rgb565 >> 8)

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
    def sprite(self, cx, cy, spr, rotate=0.0, scale=1.0):
        from .software_renderer import draw_sprite
        draw_sprite(self.buffer, self.width, self.height, cx, cy, spr.image.buffer, spr.image.width, spr.image.height, spr.u, spr.v, spr.w, spr.h, spr.colkey, rotate, scale, byte_swap=True)

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
                    out_col = (sr << 11) | (sg << 5) | sb
                    dst[dst_idx] = ((out_col & 0xFF) << 8) | (out_col >> 8)
                    continue
                    
                # Read destination (which is in Big Endian) and unswap it
                dst_val = dst[dst_idx]
                dst_val = ((dst_val & 0xFF) << 8) | (dst_val >> 8)
                dr = (dst_val >> 11) & 31
                dg = (dst_val >> 5) & 63
                db = dst_val & 31
                
                # Blending (Speed up using 16-a and >> 4 instead of division // 15)
                inv_a = 16 - a
                out_r = (sr * a + dr * inv_a) >> 4
                out_g = (sg * a + dg * inv_a) >> 4
                out_b = (sb * a + db * inv_a) >> 4
                
                out_col = (out_r << 11) | (out_g << 5) | out_b
                
                # Re-swap to Big Endian before writing back
                dst[dst_idx] = ((out_col & 0xFF) << 8) | (out_col >> 8)

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

import gc
gc.collect()
screen = Framebuffer(240, 135)
def run(update, draw, fps=30):
    """
    Game loop for MicroPython environment
    * Separate process required to reflect drawn content to ST7789 on Cardputer, etc.
    """
    from engine import logger
    logger.debug("Entering run() function...")
    import time
    import machine
    from . import input_micropython
    logger.debug("Importing modules in run() OK")
    
    # Initialize hardware input
    logger.debug("Initializing input_micropython...")
    input_micropython.init()
    logger.debug("input_micropython initialized.")
    
    # Initialize Display
    from . import st7789
    logger.debug("Initializing ST7789 display...")
    try:
        display = st7789.ST7789()
        logger.debug("ST7789 initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize ST7789: {e}")
        display = None
    
    frame_count = 0
    
    while True:
        from engine import time as engine_time
        engine_time.clock.tick()
        
        if frame_count == 0:
            logger.debug("Entering while True loop (Frame 1)...")
            
        start = time.ticks_ms()
        
        update()
        if frame_count == 0:
            logger.debug("update() OK")
            
        draw()
        if frame_count == 0:
            logger.debug("draw() OK")
        
        # Reflect drawn content to ST7789 display
        if display:
            display.show(screen.buffer)
        
        frame_count += 1
        if frame_count % 60 == 0:
            logger.debug(f"Engine Running... Frame: {frame_count}")

        
        elapsed = time.ticks_diff(time.ticks_ms(), start)
        wait_ms = (1000 // fps) - elapsed
        if wait_ms > 0:
            time.sleep_ms(wait_ms)
