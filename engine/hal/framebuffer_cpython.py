import time
import tkinter as tk
from PIL import Image as PILImage, ImageTk

from .engine_ctypes import FramebufferBase

class Framebuffer(FramebufferBase):
    def __init__(self, width, height, buffer=None):
        super().__init__(width, height, buffer)


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
        
        if new_w > 0 and new_h > 0:
            # NEAREST for crisp pixel art scaling
            img = img.resize((new_w, new_h), PILImage.NEAREST)
            
            _img_tk = ImageTk.PhotoImage(img)
            _canvas.delete("all")
            # Draw centered in the canvas
            _canvas.create_image(cw // 2, ch // 2, image=_img_tk, anchor=tk.CENTER)
            
    # Process audio
    from engine import sound
    if hasattr(sound._hal, 'update'):
        sound._hal.update()

    elapsed = time.time() - start_time
    delay = max(1, int((1.0 / _target_fps - elapsed) * 1000))
    _root.after(delay, _tick)


def init(width, height, title="Pyxel (CPython + Native C Engine)", fps=30, scale=2):
    global _root, _canvas, _target_fps, screen
    screen.reinit(width, height)
    _target_fps = fps
    
    _root = tk.Tk()
    _root.title(title)
    _root.geometry(f"{width*scale}x{height*scale}")
    _root.configure(bg="black")
    
    _canvas = tk.Canvas(_root, width=width*scale, height=height*scale, bg="black", highlightthickness=0)
    _canvas.pack(fill=tk.BOTH, expand=True)
    
    from engine import input as inp
    inp.init(_root, _canvas)

def run(update, draw, fps=30):
    global _update_func, _draw_func, _target_fps, _root
    _update_func = update
    _draw_func = draw
    _target_fps = fps
    
    if _root is None:
        init(240, 135, fps=fps)
    
    _tick()
    _root.mainloop()

def title(t):
    if _root:
        _root.title(t)
