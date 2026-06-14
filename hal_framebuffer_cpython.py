import time
import tkinter as tk
from PIL import Image as PILImage, ImageTk

class Image:
    """
    ARGB4444 フォーマットの画像（スプライト）データを保持するクラス
    """
    def __init__(self, width, height, buffer=None):
        self.width = width
        self.height = height
        self.format = "ARGB4444"
        if buffer is None:
            self.buffer = bytearray(width * height * 2)
        else:
            self.buffer = buffer
        self._mv = memoryview(self.buffer).cast('H')

class Framebuffer:
    def __init__(self, width, height, buffer=None):
        self.width = width
        self.height = height
        self.format = "RGB565"
        if buffer is None:
            # CPython/MicroPython共通で16bitアクセスしやすくするため bytearray と memoryview(cast('H')) を使用
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
        # 互換性のため残す(RGB565入力)
        self.fill_565(col)

    def fill_565(self, col):
        for i in range(self.width * self.height):
            self._mv[i] = col

    def fill(self, col):
        """画面を特定の色(ARGB4444)で塗りつぶす"""
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
        """矩形を描画する (ARGB4444)"""
        self.rect_565(x, y, w, h, self._col4444_to_565(col), is_filled)

    def blt(self, x, y, img, u, v, w, h, colkey=-1):
        """
        img: Image(ARGB4444) または Framebuffer(RGB565)
        フォーマットに応じてアルファブレンドか直接コピー(colkey対応)を切り替える
        """
        dst_w = self.width
        dst_h = self.height
        src_w = img.width
        src_h = img.height
        
        dst_mv = self._mv
        src_mv = img._mv
        
        # クリッピング（画面外はみ出し対策。今回はマイナス幅(反転)は省略）
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
                    # ARGB4444を各要素(4bit)に分解
                    a = (src_val >> 12) & 0xF
                    if a == 0:
                        continue  # 完全に透明ならスキップ
                    
                    r = (src_val >> 8) & 0xF
                    g = (src_val >> 4) & 0xF
                    b = src_val & 0xF
                    
                    # RGB565の幅(5,6,5 bit)に拡張
                    sr = (r << 1) | (r >> 3)
                    sg = (g << 2) | (g >> 2)
                    sb = (b << 1) | (b >> 3)
                    
                    if a == 15:
                        # 完全不透明ならそのまま上書き
                        dst_mv[dst_idx_base + j] = (sr << 11) | (sg << 5) | sb
                        continue
                        
                    # アルファブレンド処理
                    dst_val = dst_mv[dst_idx_base + j]
                    dr = (dst_val >> 11) & 0x1F
                    dg = (dst_val >> 5) & 0x3F
                    db = dst_val & 0x1F
                    
                    inv_a = 16 - a
                    # 割り算の代わりにビットシフト(>> 4)で高速化
                    out_r = (sr * a + dr * inv_a) >> 4
                    out_g = (sg * a + dg * inv_a) >> 4
                    out_b = (sb * a + db * inv_a) >> 4
                    
                    # RGB565にパックして書き戻す
                    dst_mv[dst_idx_base + j] = (out_r << 11) | (out_g << 5) | out_b
                else:
                    # RGB565 コピー
                    if src_val != colkey:
                        dst_mv[dst_idx_base + j] = src_val


# ---- ウィンドウとゲームループ管理 ----
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
        
    # RGB565 -> RGB888 への変換 (Tkinter/PIL表示用)
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
    # PCで見やすいように2倍に拡大
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
    # 見やすいようにキャンバスは2倍サイズ
    _canvas = tk.Canvas(_root, width=240*2, height=135*2, bg='black')
    _canvas.pack()
    
    _tick()
    _root.mainloop()
