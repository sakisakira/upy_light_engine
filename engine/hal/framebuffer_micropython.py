import framebuf
try:
    import micropython
except ImportError:
    pass


class Framebuffer:
    """
    Screen buffer wrapped around _lightengine.Framebuffer.
    """
    def __init__(self, width, height, buffer=None):
        self.width = width
        self.height = height
        self.format = "INDEX8"
            
        import _lightengine
        if buffer is None:
            self._c_fb = _lightengine.Framebuffer(self.width, self.height, 2, None)
        else:
            self._c_fb = _lightengine.Framebuffer(self.width, self.height, 2, buffer)
        
        self.dls = [_lightengine.DisplayList(), _lightengine.DisplayList()]
        self.dl_idx = 0
        self.dl_strings = [[], []]

    @property
    def dl(self):
        return self.dls[self.dl_idx]

    def clear(self, col=0):
        self.dl_strings[self.dl_idx].clear()
        self.dl.push_clear(col)
        
    def fill(self, col=0):
        self.clear(col)

    def pset(self, x, y, col):
        self.dl.push_pset(int(x), int(y), col)
        
    def pixel(self, x, y, col):
        self.pset(x, y, col)
        
    def line(self, x1, y1, x2, y2, col):
        self.dl.push_line(int(x1), int(y1), int(x2), int(y2), col)
        
    def hline(self, x, y, w, col):
        self.line(x, y, x + w - 1, y, col)
        
    def vline(self, x, y, h, col):
        self.line(x, y, x, y + h - 1, col)

    def rect(self, x, y, w, h, col, is_filled=True):
        if is_filled:
            self.dl.push_fill_rect(int(x), int(y), int(w), int(h), col)
        else:
            self.dl.push_line(int(x), int(y), int(x+w), int(y), col)
            self.dl.push_line(int(x+w), int(y), int(x+w), int(y+h), col)
            self.dl.push_line(int(x+w), int(y+h), int(x), int(y+h), col)
            self.dl.push_line(int(x), int(y+h), int(x), int(y), col)

    def sprite(self, cx, cy, spr, rotate=0.0, scale=1.0):
        t = -1 if spr.tint is None else spr.tint
        self.dl.push_draw_sprite(int(cx), int(cy), float(scale), rotate, spr.image._c_image, spr.u, spr.v, spr.w, spr.h, spr.colkey, t)

    def draw_sprite(self, x, y, scale, img, tint=0, rotate=0.0):
        self.dl.push_draw_sprite(x, y, scale, rotate, img._c_img, 0, 0, img.width, img.height, 0, tint)

    def blt(self, x, y, img, u, v, w, h, colkey=0, tint=None):
        self.dl.push_blt(int(x), int(y), img._c_image, int(u), int(v), int(w), int(h), colkey, -1 if tint is None else tint)

    def text(self, font, text, x, y, color=1, scale=1.0):
        text_bytes = text if type(text) is bytes or type(text) is bytearray else text.encode('ascii', 'ignore')
        self.dl_strings[self.dl_idx].append(text_bytes)
        col_tbl = ()
        self.dl.push_draw_text(int(x), int(y), font.image._c_image, font.char_w, font.char_h, font.cols, text_bytes, col_tbl, -1 if color is None else color)

screen = Framebuffer(240, 135)

screen = Framebuffer(240, 135)
