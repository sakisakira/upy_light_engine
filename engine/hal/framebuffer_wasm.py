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
        # The framebuffer is 240x135 in 16-bit RGB565 (2 bytes per pixel)
        self.buffer = bytearray(self.width * self.height * 2)
        # Use memoryview with 'H' format (unsigned short) to access pixels easily
        self._mv = memoryview(self.buffer).cast('H')

        # To optimize WASM drawing, we create a JS function that does the
        # RGB565 -> RGBA32 conversion and Canvas update. This is much faster
        # than looping 32400 times per frame in Python.
        js.eval("""
        window.drawFramebufferWasm = function(canvasId, buffer16) {
            const canvas = document.getElementById(canvasId);
            if (!canvas) return;
            const ctx = canvas.getContext("2d");
            if (!window._wasmImgData) {
                window._wasmImgData = ctx.createImageData(240, 135);
            }
            const imgData = window._wasmImgData;
            const data32 = new Uint32Array(imgData.data.buffer);
            // buffer16 is a Uint16Array proxy, we need its data
            const data16 = buffer16.toJs(); 
            for (let i = 0; i < data16.length; i++) {
                const p = data16[i];
                const r = ((p >> 11) & 0x1F) * 255 / 31;
                const g = ((p >> 5) & 0x3F) * 255 / 63;
                const b = (p & 0x1F) * 255 / 31;
                data32[i] = (255 << 24) | (b << 16) | (g << 8) | r;
            }
            ctx.putImageData(imgData, 0, 0);
        }
        """)

    def _col4444_to_565(self, col):
        r = (col >> 8) & 15
        g = (col >> 4) & 15
        b = col & 15
        return (((r << 1) | (r >> 3)) << 11) | (((g << 2) | (g >> 2)) << 5) | ((b << 1) | (b >> 3))

    def clear(self, col=0):
        # Kept for compatibility (RGB565 input)
        self.fill_565(col)

    def fill_565(self, col):
        for i in range(self.width * self.height):
            self._mv[i] = col

    def fill(self, col):
        """Fill the screen with a specific color (ARGB4444)"""
        self.fill_565(self._col4444_to_565(col))

    def rect_565(self, x, y, w, h, col, is_filled=True):
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

    def rect(self, x, y, w, h, col, is_filled=True):
        """Draw a rectangle (ARGB4444)"""
        self.rect_565(x, y, w, h, self._col4444_to_565(col), is_filled)

    def pset(self, x, y, col):
        """Draw a pixel (ARGB4444)"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self._mv[y * self.width + x] = self._col4444_to_565(col)

    def line(self, x1, y1, x2, y2, col):
        """Draw a vertical or horizontal line (ARGB4444)"""
        if x1 == x2:
            self.rect(x1, min(y1, y2), 1, abs(y2 - y1) + 1, col)
        elif y1 == y2:
            self.rect(min(x1, x2), y1, abs(x2 - x1) + 1, 1, col)
        else:
            raise NotImplementedError("Diagonal line drawing is not supported yet.")

    def blt(self, x, y, img, u, v, w, h, colkey=-1):
        from .software_renderer import draw_blt
        is_argb = getattr(img, "format", "") == "ARGB4444"
        draw_blt(self._mv, self.width, self.height, x, y, img._mv, img.width, img.height, u, v, w, h, is_argb, colkey, byte_swap=False)

    def sprite(self, cx, cy, spr, rotate=0.0, scale=1.0):
        from .software_renderer import draw_sprite
        draw_sprite(self._mv, self.width, self.height, cx, cy, spr.image._mv, spr.image.width, spr.image.height, spr.u, spr.v, spr.w, spr.h, spr.colkey, rotate, scale, byte_swap=False)


screen = Framebuffer()

_update_func = None
_draw_func = None
_target_fps = 30
_proxy_tick = None
_last_time = 0

def _tick(time_ms):
    global _last_time
    
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
            
        # Draw the framebuffer to the Canvas via our injected JS function
        js.window.drawFramebufferWasm("gameCanvas", screen._mv)
        
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
