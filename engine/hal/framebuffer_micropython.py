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
        super().pixel(int(x), int(y), col)

    def rect(self, x, y, w, h, col, is_filled=True):
        x, y, w, h = int(x), int(y), int(w), int(h)
        if is_filled:
            super().fill_rect(x, y, w, h, col)
        else:
            super().rect(x, y, w, h, col)

    def sprite(self, cx, cy, spr, rotate=0.0, scale=1.0):
        import math
        w = spr.w
        h = spr.h
        
        if rotate == 0.0:
            half_w = w * scale * 0.5
            half_h = h * scale * 0.5
            start_x = int(cx - half_w)
            start_y = int(cy - half_h)
            end_x = int(cx + half_w) + 1
            end_y = int(cy + half_h) + 1
            
            min_x = max(0, start_x)
            min_y = max(0, start_y)
            max_x = min(self.width, end_x)
            max_y = min(self.height, end_y)
            
            if min_x >= max_x or min_y >= max_y:
                return
                
            inv_scale = 1.0 / scale
            cos_inv = inv_scale
            sin_inv = 0.0
        else:
            cos_f = math.cos(rotate) * scale
            sin_f = math.sin(rotate) * scale
            hw = w * 0.5
            hh = h * 0.5
            corners = [
                ( hw,  hh),
                ( hw, -hh),
                (-hw,  hh),
                (-hw, -hh),
            ]
            min_cx = max_cx = min_cy = max_cy = 0
            first = True
            for (px, py) in corners:
                rx = px * cos_f - py * sin_f
                ry = px * sin_f + py * cos_f
                if first:
                    min_cx, max_cx = rx, rx
                    min_cy, max_cy = ry, ry
                    first = False
                else:
                    if rx < min_cx: min_cx = rx
                    elif rx > max_cx: max_cx = rx
                    if ry < min_cy: min_cy = ry
                    elif ry > max_cy: max_cy = ry
                    
            start_x = int(cx + min_cx)
            start_y = int(cy + min_cy)
            end_x = int(cx + max_cx) + 1
            end_y = int(cy + max_cy) + 1
            
            min_x = max(0, start_x)
            min_y = max(0, start_y)
            max_x = min(self.width, end_x)
            max_y = min(self.height, end_y)
            
            if min_x >= max_x or min_y >= max_y:
                return
                
            inv_scale = 1.0 / scale
            cos_inv = math.cos(-rotate) * inv_scale
            sin_inv = math.sin(-rotate) * inv_scale

        # Convert to fixed point (1.0 = 256)
        cx_fp = int(cx * 256)
        cy_fp = int(cy * 256)
        cos_inv_fp = int(cos_inv * 256)
        sin_inv_fp = int(sin_inv * 256)
        
        tint = -1 if spr.tint is None else spr.tint
        
        args = (
            self.width, spr.image.width, spr.u, spr.v, w, h,
            min_x, max_x, min_y, max_y,
            cx_fp, cy_fp, cos_inv_fp, sin_inv_fp, spr.colkey, tint
        )
        
        self._sprite_viper_fast(self.buffer, spr.image.buffer, args)

    @micropython.viper
    def _sprite_viper_fast(self, dst_buf, src_buf, args):
        dst = ptr8(dst_buf)
        src = ptr8(src_buf)
        
        dst_w = int(args[0])
        src_w = int(args[1])
        u = int(args[2])
        v = int(args[3])
        w = int(args[4])
        h = int(args[5])
        min_x = int(args[6])
        max_x = int(args[7])
        min_y = int(args[8])
        max_y = int(args[9])
        cx_fp = int(args[10])
        cy_fp = int(args[11])
        cos_inv_fp = int(args[12])
        sin_inv_fp = int(args[13])
        colkey = int(args[14])
        tint = int(args[15])
        
        w_half_fp = w << 7
        h_half_fp = h << 7
        
        for dy in range(min_y, max_y):
            dist_y_fp = (dy << 8) - cy_fp
            # -dist_y_fp * sin_inv_fp + w * 0.5
            sx_base_fp = -((dist_y_fp * sin_inv_fp) >> 8) + w_half_fp
            sy_base_fp = ((dist_y_fp * cos_inv_fp) >> 8) + h_half_fp
            dst_idx_base = dy * dst_w
            
            for dx in range(min_x, max_x):
                dist_x_fp = (dx << 8) - cx_fp
                sx = ((dist_x_fp * cos_inv_fp) >> 8) + sx_base_fp
                sx = sx >> 8
                
                if sx >= 0 and sx < w:
                    sy = ((dist_x_fp * sin_inv_fp) >> 8) + sy_base_fp
                    sy = sy >> 8
                    
                    if sy >= 0 and sy < h:
                        src_idx_base = (v + sy) * src_w + u
                        src_val = src[src_idx_base + sx]
                        
                        if src_val != colkey:
                            if tint != -1:
                                dst[dst_idx_base + dx] = tint
                            else:
                                dst[dst_idx_base + dx] = src_val

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
        if hasattr(font, 'image') and font.image.format == "INDEX8":
            dst_w = self.width
            dst_h = self.height
            char_w = font.char_w
            char_h = font.char_h
            cols = font.cols
            
            for i, char in enumerate(text):
                code = ord(char)
                idx = -1
                if font.char_map is not None:
                    if code in font.char_map:
                        idx = font.char_map[code]
                else:
                    if 32 <= code <= 126:
                        idx = code - 32
                
                if idx < 0: continue
                
                u = (idx % cols) * char_w
                v = (idx // cols) * char_h
                
                if scale == 1.0:
                    px = int(x + i * char_w)
                    py = int(y)
                    tint_val = -1 if color is None else color
                    self._blt_viper_index8(px, py, font.image.buffer, font.image.width, u, v, char_w, char_h, 0, tint_val)
                else:
                    cx = int(x + i * char_w * scale + (char_w * scale * 0.5))
                    cy = int(y + (char_h * scale * 0.5))
                    from .software_renderer import draw_sprite
                    draw_sprite(self.buffer, dst_w, dst_h, cx, cy, font.image.buffer, font.image.width, font.image.height, u, v, char_w, char_h, colkey=0, scale=scale, tint=color)

# ---- Window and Game Loop Management ----
screen = Framebuffer(240, 135)

def run(update, draw, fps=30):
    import engine.hal.st7789 as st7789
    from engine import time as engine_time
    import engine.input as input
    import utime as time
    
    display = st7789.ST7789()
    
    # Inject screen into fb module explicitly
    import engine.framebuffer as fb
    fb.screen = screen
    
    input.init()
    
    target_ms = 1000 // fps
    
    import sys
    try:
        while True:
            t0 = time.ticks_ms()
            engine_time.clock.tick()
            
            update()
            draw()
            
            display.show(screen.buffer)
            
            t1 = time.ticks_ms()
            dt = time.ticks_diff(t1, t0)
            sleep_ms = target_ms - dt
            if sleep_ms > 0:
                time.sleep_ms(sleep_ms)
    except Exception as e:
        with open('error.log', 'w') as f:
            sys.print_exception(e, f)
        raise
