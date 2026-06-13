import framebuf
try:
    import micropython
except ImportError:
    pass

class Image:
    """
    ARGB4444 フォーマットの画像（スプライト）データを保持する軽量コンテナ
    MicroPythonでは、オーバーヘッドを最小限にするためFrameBufferを継承しない
    """
    def __init__(self, width, height, buffer=None):
        self.width = width
        self.height = height
        self.format = "ARGB4444"
        if buffer is None:
            self.buffer = bytearray(width * height * 2)
        else:
            self.buffer = buffer

class Framebuffer(framebuf.FrameBuffer):
    """
    RGB565 フォーマットの画面バッファ
    標準のframebufを継承しているため、fill, rect, text等がそのまま使える
    """
    def __init__(self, width, height, buffer=None):
        self.width = width
        self.height = height
        self.format = "RGB565"
        if buffer is None:
            self.buffer = bytearray(width * height * 2)
        else:
            self.buffer = buffer
        # RGB565フォーマットとして親クラスを初期化
        super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)

    def clear(self, col=0):
        self.fill(col)

    def blt(self, x, y, img, u, v, w, h, colkey=-1):
        """
        img のフォーマットに応じて合成処理を切り替える
        """
        is_argb = getattr(img, "format", "") == "ARGB4444"
        if is_argb:
            self._blt_viper_argb(x, y, img.buffer, img.width, u, v, w, h)
        else:
            self._blt_viper_rgb(x, y, img.buffer, img.width, u, v, w, h, colkey)

    @micropython.viper
    def _blt_viper_argb(self, x: int, y: int, src_buf, src_w: int, u: int, v: int, w: int, h: int):
        # 16bitポインタで高速アクセス
        dst = ptr16(self.buffer)
        src = ptr16(src_buf)
        
        dst_w = int(self.width)
        dst_h = int(self.height)
        
        # はみ出し対策（クリッピング）
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
                
                # ARGB4444 分解
                a = (src_val >> 12) & 15
                if a == 0:
                    continue
                    
                r = (src_val >> 8) & 15
                g = (src_val >> 4) & 15
                b = src_val & 15
                
                # RGB565へ拡張
                sr = (r << 1) | (r >> 3)
                sg = (g << 2) | (g >> 2)
                sb = (b << 1) | (b >> 3)
                
                dst_idx = dst_idx_base + j
                if a == 15:
                    dst[dst_idx] = (sr << 11) | (sg << 5) | sb
                    continue
                    
                dst_val = dst[dst_idx]
                dr = (dst_val >> 11) & 31
                dg = (dst_val >> 5) & 63
                db = dst_val & 31
                
                # ブレンド
                inv_a = 15 - a
                out_r = (sr * a + dr * inv_a) // 15
                out_g = (sg * a + dg * inv_a) // 15
                out_b = (sb * a + db * inv_a) // 15
                
                dst[dst_idx] = (out_r << 11) | (out_g << 5) | out_b

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

screen = Framebuffer(240, 135)

def run(update, draw, fps=30):
    """
    MicroPython環境向けのゲームループ
    ※CardputerのST7789等に描画内容を反映する処理は別途必要です。
    """
    import time
    import machine
    
    # 【実装時の注意】
    # ここでST7789などのSPIドライバを初期化する必要があります
    # 例: display = st7789.ST7789(...)
    
    while True:
        start = time.ticks_ms()
        
        update()
        draw()
        
        # SPI転送による画面反映のダミー
        # 例: display.show(screen.buffer)
        
        elapsed = time.ticks_diff(time.ticks_ms(), start)
        wait_ms = (1000 // fps) - elapsed
        if wait_ms > 0:
            time.sleep_ms(wait_ms)
