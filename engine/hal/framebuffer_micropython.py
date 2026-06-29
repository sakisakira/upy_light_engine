import framebuf
try:
    import micropython
except ImportError:
    pass

try:
    import graphics_engine
except ImportError:
    graphics_engine = None

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
            
        import array
        self._sprite_args = array.array('i', [0] * 16)
        self._blt_args = array.array('i', [0] * 11)
        self._fast_text = True
        
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
        
        if rotate == 0.0 and scale == 1.0:
            x = int(cx - w * 0.5)
            y = int(cy - h * 0.5)
            self.blt(x, y, spr.image, spr.u, spr.v, w, h, colkey=spr.colkey, tint=spr.tint)
            return
            
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
        
        if graphics_engine:
            graphics_engine.draw_sprite(
                self.buffer, self.width, self.height,
                spr.image.buffer, spr.image.width, spr.image.height,
                spr.u, spr.v, w, h, cx_fp, cy_fp, min_x, max_x, min_y, max_y,
                cos_inv_fp, sin_inv_fp, spr.colkey, tint
            )
        else:
            a = self._sprite_args
            a[0] = self.width
            a[1] = spr.image.width
            a[2] = spr.u
            a[3] = spr.v
            a[4] = w
            a[5] = h
            a[6] = min_x
            a[7] = max_x
            a[8] = min_y
            a[9] = max_y
            a[10] = cx_fp
            a[11] = cy_fp
            a[12] = cos_inv_fp
            a[13] = sin_inv_fp
            a[14] = spr.colkey
            a[15] = tint
            
            self._sprite_viper_fast(self.buffer, spr.image.buffer, a)

    @micropython.viper
    def _sprite_viper_fast(self, dst_buf, src_buf, args_buf):
        dst = ptr8(dst_buf)
        src = ptr8(src_buf)
        args = ptr32(args_buf)
        
        dst_w = args[0]
        src_w = args[1]
        u = args[2]
        v = args[3]
        w = args[4]
        h = args[5]
        min_x = args[6]
        max_x = args[7]
        min_y = args[8]
        max_y = args[9]
        cx_fp = args[10]
        cy_fp = args[11]
        cos_inv_fp = args[12]
        sin_inv_fp = args[13]
        colkey = args[14]
        tint = args[15]
        
        w_half_fp = w << 7
        h_half_fp = h << 7
        uv_base = v * src_w + u
        
        if tint != -1:
            for dy in range(min_y, max_y):
                dist_y_fp = (dy << 8) - cy_fp
                sx_base_fp = -((dist_y_fp * sin_inv_fp) >> 8) + w_half_fp
                sy_base_fp = ((dist_y_fp * cos_inv_fp) >> 8) + h_half_fp
                dst_idx_base = dy * dst_w
                
                dist_x_fp_start = (min_x << 8) - cx_fp
                sx_fp = ((dist_x_fp_start * cos_inv_fp) >> 8) + sx_base_fp
                sy_fp = ((dist_x_fp_start * sin_inv_fp) >> 8) + sy_base_fp
                
                for dx in range(min_x, max_x):
                    sx = sx_fp >> 8
                    sy = sy_fp >> 8
                    
                    sx_fp += cos_inv_fp
                    sy_fp += sin_inv_fp
                    
                    if uint(sx) < uint(w):
                        if uint(sy) < uint(h):
                            src_idx = sy * src_w + uv_base + sx
                            src_val = src[src_idx]
                            
                            if src_val != colkey:
                                dst[dst_idx_base + dx] = tint
        else:
            for dy in range(min_y, max_y):
                dist_y_fp = (dy << 8) - cy_fp
                sx_base_fp = -((dist_y_fp * sin_inv_fp) >> 8) + w_half_fp
                sy_base_fp = ((dist_y_fp * cos_inv_fp) >> 8) + h_half_fp
                dst_idx_base = dy * dst_w
                
                dist_x_fp_start = (min_x << 8) - cx_fp
                sx_fp = ((dist_x_fp_start * cos_inv_fp) >> 8) + sx_base_fp
                sy_fp = ((dist_x_fp_start * sin_inv_fp) >> 8) + sy_base_fp
                
                for dx in range(min_x, max_x):
                    sx = sx_fp >> 8
                    sy = sy_fp >> 8
                    
                    sx_fp += cos_inv_fp
                    sy_fp += sin_inv_fp
                    
                    if uint(sx) < uint(w):
                        if uint(sy) < uint(h):
                            src_idx = sy * src_w + uv_base + sx
                            src_val = src[src_idx]
                            
                            if src_val != colkey:
                                dst[dst_idx_base + dx] = src_val

    def blt(self, x, y, img, u, v, w, h, colkey=0, tint=None):
        tint_val = -1 if tint is None else tint
        
        if graphics_engine:
            cx_fp = int((x + w * 0.5) * 256)
            cy_fp = int((y + h * 0.5) * 256)
            min_x = max(0, int(x))
            min_y = max(0, int(y))
            max_x = min(self.width, int(x + w))
            max_y = min(self.height, int(y + h))
            
            if min_x >= max_x or min_y >= max_y:
                return
                
            graphics_engine.draw_sprite(
                self.buffer, self.width, self.height,
                img.buffer, img.width, img.height,
                u, v, w, h, cx_fp, cy_fp, min_x, max_x, min_y, max_y,
                256, 0, colkey, tint_val
            )
        else:
            a = self._blt_args
            a[0] = int(x)
            a[1] = int(y)
            a[2] = img.width
            a[3] = u
            a[4] = v
            a[5] = w
            a[6] = h
            a[7] = colkey
            a[8] = tint_val
            a[9] = self.width
            a[10] = self.height
            self._blt_viper_index8(self.buffer, img.buffer, a)

    @micropython.viper
    def _blt_viper_index8(self, dst_buf, src_buf, args_buf):
        dst = ptr8(dst_buf)
        src = ptr8(src_buf)
        args = ptr32(args_buf)
        
        x = args[0]
        y = args[1]
        src_w = args[2]
        u = args[3]
        v = args[4]
        w = args[5]
        h = args[6]
        colkey = args[7]
        tint = args[8]
        dst_w = args[9]
        dst_h = args[10]
        
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

        if tint != -1:
            for i in range(start_y, end_y):
                dst_idx_base = (y + i) * dst_w + x
                src_idx_base = (v + i) * src_w + u
                
                for j in range(start_x, end_x):
                    src_val = src[src_idx_base + j]
                    if src_val != colkey:
                        dst[dst_idx_base + j] = tint
        else:
            for i in range(start_y, end_y):
                dst_idx_base = (y + i) * dst_w + x
                src_idx_base = (v + i) * src_w + u
                
                for j in range(start_x, end_x):
                    src_val = src[src_idx_base + j]
                    if src_val != colkey:
                        dst[dst_idx_base + j] = src_val

    def text(self, font, text, x, y, color=1, scale=1.0):
        if hasattr(font, 'image') and font.image.format == "INDEX8":
            dst_w = self.width
            dst_h = self.height
            char_w = font.char_w
            char_h = font.char_h
            cols = font.cols
            tint_val = -1 if color is None else color
            
            if scale == 1.0 and graphics_engine:
                if not hasattr(font, 'lookup_table'):
                    if font.char_map is not None:
                        import array
                        font.lookup_table = array.array('h', [-1] * 256)
                        for code, idx in font.char_map.items():
                            if code < 256:
                                font.lookup_table[code] = idx
                    else:
                        font.lookup_table = None
                        
                text_bytes = text.encode('ascii', 'ignore')
                
                graphics_engine.draw_text_fast(
                    self.buffer, dst_w, dst_h,
                    font.image.buffer, font.image.width,
                    char_w, char_h, cols,
                    text_bytes, len(text_bytes),
                    font.lookup_table,
                    int(x), int(y), tint_val
                )
                return
            
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
                    
                    a = self._blt_args
                    a[0] = px
                    a[1] = py
                    a[2] = font.image.width
                    a[3] = u
                    a[4] = v
                    a[5] = char_w
                    a[6] = char_h
                    a[7] = 0
                    a[8] = tint_val
                    a[9] = dst_w
                    a[10] = dst_h
                    
                    self._blt_viper_index8(self.buffer, font.image.buffer, a)
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
        from engine.profiler import profiler
        import gc
        while True:
            t0 = time.ticks_ms()
            engine_time.clock.tick()
            
            profiler.start("update")
            update()
            profiler.end("update")
            
            profiler.start("draw_all")
            draw()
            profiler.end("draw_all")
            
            profiler.start("display_show")
            display.show(screen.buffer)
            profiler.end("display_show")
            
            # Print free memory every 60 frames to monitor leaks
            if engine_time.clock.frame_count % 60 == 0:
                print(f"FPS: {engine_time.clock.fps} | Free Mem: {gc.mem_free()} bytes")
            
            t1 = time.ticks_ms()
            dt = time.ticks_diff(t1, t0)
            sleep_ms = target_ms - dt
            if sleep_ms > 0:
                time.sleep_ms(sleep_ms)
    except Exception as e:
        with open('error.log', 'w') as f:
            sys.print_exception(e, f)
        raise
