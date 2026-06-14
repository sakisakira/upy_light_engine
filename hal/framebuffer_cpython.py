import time
import tkinter as tk
from PIL import Image as PILImage, ImageTk


class Framebuffer:
    def __init__(self, width, height, buffer=None):
        self.width = width
        self.height = height
        self.format = "RGB565"
        if buffer is None:
            # Use bytearray and memoryview(cast('H')) for easy 16-bit access common to CPython/MicroPython
            self.buffer = bytearray(width * height * 2)
        else:
            self.buffer = buffer
        self._mv = memoryview(self.buffer).cast('H')

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
        """
        img: Image(ARGB4444) or Framebuffer(RGB565)
        Switches between alpha blending or direct copy (colkey supported) based on format.
        """
        dst_w = self.width
        dst_h = self.height
        src_w = img.width
        src_h = img.height
        
        dst_mv = self._mv
        src_mv = img._mv
        
        # Clipping (Prevent drawing outside the screen. Negative width/flip omitted for now)
        start_x = max(0, -x)
        start_y = max(0, -y)
        end_x = min(w, dst_w - x)
        end_y = min(h, dst_h - y)
        
        if start_x >= end_x or start_y >= end_y:
            return

        is_argb = getattr(img, "format", "") == "ARGB4444"

        for i in range(start_y, end_y):
            dst_idx_base = (y + i) * dst_w + x
            src_idx_base = (v + i) * src_w + u
            
            for j in range(start_x, end_x):
                src_val = src_mv[src_idx_base + j]
                
                if is_argb:
                    # Decompose ARGB4444 into 4-bit components
                    a = (src_val >> 12) & 0xF
                    if a == 0:
                        continue  # Skip if completely transparent
                    
                    r = (src_val >> 8) & 0xF
                    g = (src_val >> 4) & 0xF
                    b = src_val & 0xF
                    
                    # Expand to RGB565 width (5,6,5 bit)
                    sr = (r << 1) | (r >> 3)
                    sg = (g << 2) | (g >> 2)
                    sb = (b << 1) | (b >> 3)
                    
                    if a == 15:
                        # Overwrite directly if completely opaque
                        dst_mv[dst_idx_base + j] = (sr << 11) | (sg << 5) | sb
                        continue
                        
                    # Alpha blending process
                    dst_val = dst_mv[dst_idx_base + j]
                    dr = (dst_val >> 11) & 0x1F
                    dg = (dst_val >> 5) & 0x3F
                    db = dst_val & 0x1F
                    
                    inv_a = 16 - a
                    # Speed up using bit shift (>> 4) instead of division
                    out_r = (sr * a + dr * inv_a) >> 4
                    out_g = (sg * a + dg * inv_a) >> 4
                    out_b = (sb * a + db * inv_a) >> 4
                    
                    # Pack into RGB565 and write back
                    dst_mv[dst_idx_base + j] = (out_r << 11) | (out_g << 5) | out_b
                else:
                    # RGB565 copy
                    if src_val != colkey:
                        dst_mv[dst_idx_base + j] = src_val


# ---- Window and Game Loop Management ----
screen = Framebuffer(240, 135)
_root = None
_canvas = None
_img_tk = None
_update_func = None
_draw_func = None
_target_fps = 30

def _tick():
    global _img_tk
    
    if _update_func:
        _update_func()
        
    if _draw_func:
        _draw_func()
        
    # Conversion from RGB565 to RGB888 (for Tkinter/PIL display)
    w = screen.width
    h = screen.height
    out = bytearray(w * h * 3)
    mv = screen._mv
    for i in range(w * h):
        val = mv[i]
        r = (val >> 11) & 0x1F
        g = (val >> 5) & 0x3F
        b = val & 0x1F
        
        out[i*3]   = (r << 3) | (r >> 2)
        out[i*3+1] = (g << 2) | (g >> 4)
        out[i*3+2] = (b << 3) | (b >> 2)
        
    img = PILImage.frombytes("RGB", (w, h), bytes(out))
    # Scale up by 2x for easier viewing on PC
    img = img.resize((w * 2, h * 2), PILImage.NEAREST)
    
    _img_tk = ImageTk.PhotoImage(image=img)
    _canvas.create_image(0, 0, anchor=tk.NW, image=_img_tk)
        
    _root.after(1000 // _target_fps, _tick)


def run(update, draw, fps=30):
    global _root, _canvas, _update_func, _draw_func, _target_fps
    
    _update_func = update
    _draw_func = draw
    _target_fps = fps
    
    _root = tk.Tk()
    _root.title("Cardputer Pyxel HAL (CPython)")
    # Canvas size is doubled for easier viewing
    _canvas = tk.Canvas(_root, width=240*2, height=135*2, bg='black')
    _canvas.pack()
    
    from . import input_cpython
    input_cpython.init(_root, _canvas)
    
    _tick()
    _root.mainloop()
