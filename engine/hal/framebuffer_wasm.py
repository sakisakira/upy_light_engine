# framebuffer_wasm.py
import sys

# WASM environment needs 'js' and 'pyodide'
try:
    import js
    from pyodide.ffi import create_proxy
except ImportError:
    pass

class Framebuffer:
    def __init__(self):
        self.width = 240
        self.height = 135
        self.format = "INDEX8"
        self.buffer = bytearray(self.width * self.height)
        self._mv = memoryview(self.buffer).cast('B')

        js.eval("""
        window.drawFramebufferWasm = function(canvasId, buffer8, palette24) {
            const canvas = document.getElementById(canvasId);
            if (!canvas) return;
            const ctx = canvas.getContext("2d");
            if (!window._wasmImgData) {
                window._wasmImgData = ctx.createImageData(240, 135);
            }
            const imgData = window._wasmImgData;
            const data32 = new Uint32Array(imgData.data.buffer);
            const data8 = buffer8.toJs();
            const pal24 = palette24.toJs();
            for (let i = 0; i < data8.length; i++) {
                const c_idx = data8[i];
                const col24 = pal24[c_idx];
                const r = (col24 >> 16) & 0xFF;
                const g = (col24 >> 8) & 0xFF;
                const b = col24 & 0xFF;
                data32[i] = (255 << 24) | (b << 16) | (g << 8) | r;
            }
            ctx.putImageData(imgData, 0, 0);
        }
        """)

    def clear(self, col=0):
        self.fill(col)

    def fill(self, col):
        for i in range(self.width * self.height):
            self._mv[i] = col

    def rect(self, x, y, w, h, col, is_filled=True):
        start_x = max(0, x)
        start_y = max(0, y)
        end_x = min(self.width, x + w)
        end_y = min(self.height, y + h)
        if start_x >= end_x or start_y >= end_y:
            return
            
        dst_w = self.width
        mv = self._mv
        if is_filled:
            for py in range(start_y, end_y):
                idx = py * dst_w + start_x
                for px in range(end_x - start_x):
                    mv[idx + px] = col
        else:
            for px in range(start_x, end_x):
                mv[start_y * dst_w + px] = col
                mv[(end_y - 1) * dst_w + px] = col
            for py in range(start_y, end_y):
                mv[py * dst_w + start_x] = col
                mv[py * dst_w + end_x - 1] = col

    def pset(self, x, y, col):
        if 0 <= x < self.width and 0 <= y < self.height:
            self._mv[y * self.width + x] = col

    def line(self, x1, y1, x2, y2, col):
        if x1 == x2:
            self.rect(x1, min(y1, y2), 1, abs(y2 - y1) + 1, col)
        elif y1 == y2:
            self.rect(min(x1, x2), y1, abs(x2 - x1) + 1, 1, col)
        else:
            raise NotImplementedError("Diagonal line drawing is not supported yet.")

    def blt(self, x, y, img, u, v, w, h, colkey=0, tint=None):
        from .software_renderer import draw_blt
        draw_blt(self._mv, self.width, self.height, x, y, img._mv, img.width, img.height, u, v, w, h, colkey, tint)

    def sprite(self, cx, cy, spr, rotate=0.0, scale=1.0):
        from .software_renderer import draw_sprite
        draw_sprite(self._mv, self.width, self.height, cx, cy, spr.image._mv, spr.image.width, spr.image.height, spr.u, spr.v, spr.w, spr.h, spr.colkey, rotate, scale, spr.tint)

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
                
                cx = int(x + i * char_w * scale + (char_w * scale * 0.5))
                cy = int(y + (char_h * scale * 0.5))
                
                from .software_renderer import draw_sprite
                draw_sprite(self._mv, dst_w, dst_h, cx, cy, font.image._mv, font.image.width, font.image.height, u, v, char_w, char_h, colkey=0, scale=scale, tint=color)


screen = Framebuffer()

_update_func = None
_draw_func = None
_target_fps = 30
_proxy_tick = None
_last_time = 0
_palette_mv = None

def _tick(time_ms):
    global _last_time, _palette_mv
    
    # Calculate delta time
    if _last_time == 0:
        _last_time = time_ms
        
    dt = time_ms - _last_time
    # Roughly enforce target FPS
    if dt >= (1000 / _target_fps):
        _last_time = time_ms
        
        from engine import time as engine_time
        engine_time.clock.tick()
        
        if _update_func:
            _update_func()
            
        if _draw_func:
            _draw_func()
            
        if _palette_mv is None:
            import array
            from engine import palette
            _palette_array = array.array('I', palette.colors)
            _palette_mv = memoryview(_palette_array)
            
        # Draw the framebuffer to the Canvas via our injected JS function
        js.window.drawFramebufferWasm("gameCanvas", screen._mv, _palette_mv)
        
    # Schedule the next frame
    js.window.requestAnimationFrame(_proxy_tick)

def run(update, draw, fps=30):
    global _update_func, _draw_func, _target_fps, _proxy_tick
    
    _update_func = update
    _draw_func = draw
    _target_fps = fps
    
    from engine.hal import input_wasm
    input_wasm.init()
    
    # create_proxy is required to pass a Python function to JS
    _proxy_tick = create_proxy(_tick)
    js.window.requestAnimationFrame(_proxy_tick)
    
    # Note: run() will exit immediately in WASM, but the loop is kept alive
    # by requestAnimationFrame in the browser!
