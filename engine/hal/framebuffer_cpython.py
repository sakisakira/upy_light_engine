import time
import tkinter as tk
from PIL import Image as PILImage, ImageTk


from .engine_cpython import core, CEngineFramebuffer, CDisplayList, CEngineSprite
import ctypes

class Framebuffer:
    def __init__(self, width, height, buffer=None):
        self.width = width
        self.height = height
        self.format = "INDEX8"
        if buffer is None:
            self.buffer = bytearray(width * height)
        else:
            self.buffer = buffer
        self._mv = memoryview(self.buffer).cast('B')
        
        self._c_refs = []
        
        self._c_fb = CEngineFramebuffer()
        self._c_fb.width = width
        self._c_fb.height = height
        self._c_fb.format = 2 # kFormatIndex8
        self._c_data = (ctypes.c_uint8 * len(self.buffer)).from_buffer(self.buffer)
        self._c_fb.buffer = ctypes.cast(self._c_data, ctypes.POINTER(ctypes.c_uint8))
        
        self._c_dl = core.dl_create()

    def _flush(self):
        core.render_display_list(ctypes.pointer(self._c_fb), self._c_dl)
        core.dl_clear(self._c_dl)
        self._c_refs.clear()

    def clear(self, col=0):
        core.dl_push_clear(self._c_dl, col)

    def fill(self, col):
        core.dl_push_clear(self._c_dl, col)

    def rect(self, x, y, w, h, col, is_filled=True):
        if is_filled:
            core.dl_push_fill_rect(self._c_dl, int(x), int(y), int(w), int(h), col)
        else:
            start_x = max(0, int(x))
            start_y = max(0, int(y))
            end_x = min(self.width, int(x + w))
            end_y = min(self.height, int(y + h))
            if start_x >= end_x or start_y >= end_y: return
            core.dl_push_fill_rect(self._c_dl, start_x, start_y, end_x - start_x, 1, col)
            core.dl_push_fill_rect(self._c_dl, start_x, end_y - 1, end_x - start_x, 1, col)
            core.dl_push_fill_rect(self._c_dl, start_x, start_y, 1, end_y - start_y, col)
            core.dl_push_fill_rect(self._c_dl, end_x - 1, start_y, 1, end_y - start_y, col)

    def pset(self, x, y, col):
        core.dl_push_pset(self._c_dl, int(x), int(y), col)

    def line(self, x1, y1, x2, y2, col):
        core.dl_push_line(self._c_dl, int(x1), int(y1), int(x2), int(y2), col)

    def blt(self, x, y, img, u, v, w, h, colkey=0, tint=None):
        if not hasattr(img, '_c_image'): return
        t = tint if tint is not None else -1
        core.dl_push_blt(self._c_dl, int(x), int(y), ctypes.pointer(img._c_image), int(u), int(v), int(w), int(h), colkey, t)

    def sprite(self, cx, cy, spr, rotate=0.0, scale=1.0):
        if not hasattr(spr, '_c_sprite'): return
        t = spr.tint if spr.tint is not None else -1
        core.dl_push_draw_sprite(self._c_dl, int(cx), int(cy), float(scale), ctypes.pointer(spr._c_sprite), t)

    def text(self, font, text, x, y, color=1, scale=1.0):
        if hasattr(font, 'image') and hasattr(font, '_c_lookup'):
            text_bytes = text.encode('utf-8')
            c_text = ctypes.create_string_buffer(text_bytes)
            self._c_refs.append(c_text)
            
            core.dl_push_draw_text(
                self._c_dl, int(x), int(y),
                ctypes.pointer(font.image._c_image),
                font.char_w, font.char_h, font.cols,
                ctypes.cast(c_text, ctypes.POINTER(ctypes.c_uint8)), len(text_bytes),
                ctypes.cast(font._c_lookup, ctypes.POINTER(ctypes.c_int16)),
                color
            )


# ---- Window and Game Loop Management ----
screen = Framebuffer(240, 135)
_root = None
_canvas = None
_img_tk = None
_update_func = None
_draw_func = None
_target_fps = 30

def _tick():
    import time
    start_time = time.time()
    
    global _root
    
    from engine import time as engine_time
    engine_time.clock.tick()
    
    global _img_tk
    
    if _update_func:
        _update_func()
        
    if _draw_func:
        _draw_func()
        
    screen._flush()
        
    # Fast Conversion from INDEX8 to RGB using PIL's native palette support
    from engine import palette
    w = screen.width
    h = screen.height
    
    img = PILImage.frombytes("P", (w, h), bytes(screen._mv))
    
    # Build flat palette list: [r, g, b, r, g, b, ...]
    flat_palette = []
    for c in palette.colors:
        flat_palette.extend([(c >> 16) & 0xFF, (c >> 8) & 0xFF, c & 0xFF])
    img.putpalette(flat_palette)
    
    # Convert to RGB before resizing for compatibility with PhotoImage
    img = img.convert("RGB")
    
    # Dynamic scaling while preserving aspect ratio
    cw = _canvas.winfo_width()
    ch = _canvas.winfo_height()
    
    if cw > 1 and ch > 1:
        # Calculate max scale to fit the canvas (letterboxing)
        scale = min(cw / w, ch / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        offset_x = (cw - new_w) // 2
        offset_y = (ch - new_h) // 2
    else:
        # Fallback to 2x scale before the window is fully initialized
        new_w = w * 2
        new_h = h * 2
        offset_x = 0
        offset_y = 0
        
    img = img.resize((new_w, new_h), PILImage.NEAREST)
    _img_tk = ImageTk.PhotoImage(image=img)
    
    _canvas.delete("all")
    _canvas.create_image(offset_x, offset_y, anchor=tk.NW, image=_img_tk)
        
    # Calculate delay to maintain target FPS
    end_time = time.time()
    execution_time_ms = int((end_time - start_time) * 1000)
    target_ms = 1000 // _target_fps
    delay = max(1, target_ms - execution_time_ms)
    
    _root.after(delay, _tick)


def run(update, draw, fps=30):
    global _root, _canvas, _update_func, _draw_func, _target_fps
    
    _update_func = update
    _draw_func = draw
    _target_fps = fps
    
    _root = tk.Tk()
    _root.title("Cardputer Pyxel HAL (CPython)")
    # Canvas size is doubled for easier viewing
    _canvas = tk.Canvas(_root, width=240*2, height=135*2, bg='black', highlightthickness=0)
    _canvas.pack(fill=tk.BOTH, expand=True)
    
    from . import input_cpython
    input_cpython.init(_root, _canvas)
    
    _tick()
    _root.mainloop()
