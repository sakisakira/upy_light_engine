import framebuf
try:
    import micropython
except ImportError:
    pass

try:
    import graphics_engine
except ImportError:
    graphics_engine = None

class Framebuffer:
    """
    Screen buffer wrapped around _lightengine.Framebuffer.
    """
    def __init__(self, width, height, buffer=None):
        self.width = width
        self.height = height
        self.format = "INDEX8"
        self.buf_idx = 0
            
        import _lightengine
        if buffer is None:
            self._c_fbs = [
                _lightengine.Framebuffer(self.width, self.height, 2, None),
                _lightengine.Framebuffer(self.width, self.height, 2, None)
            ]
        else:
            self._c_fbs = [
                _lightengine.Framebuffer(self.width, self.height, 2, buffer),
                _lightengine.Framebuffer(self.width, self.height, 2, None)
            ]
        
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
        self.dl.push_draw_text(int(x), int(y), font.image._c_image, font.char_w, font.char_h, font.cols, text_bytes, -1 if color is None else color)

# ---- Window and Game Loop Management ----
screen = Framebuffer(240, 135)

def run(update, draw, fps=30):
    import engine.hal.st7789 as st7789
    from engine import time as engine_time
    import engine.input as input
    import utime as time
    import _lightengine
    
    display = st7789.ST7789()
    
    # Inject screen into fb module explicitly
    import engine.framebuffer as fb
    fb.screen = screen
    
    input.init()
    _lightengine.init()
    
    target_ms = 1000 // fps
    
    import sys
    try:
        from engine.profiler import profiler
        import gc
        
        # Submit first empty frame to bootstrap pipeline
        screen.buf_idx = 1
        screen.dl_idx = 1
        display.set_window(0, 0, 239, 134)
        _lightengine.submit_and_send(screen._c_fbs[screen.buf_idx], screen.dls[screen.dl_idx], None)
        
        while True:
            t0 = time.ticks_ms()
            engine_time.clock.tick()
            
            # Switch DisplayList and Buffer
            screen.dl_idx = 1 - screen.dl_idx
            screen.buf_idx = 1 - screen.buf_idx
            screen.dl_strings[screen.dl_idx].clear()
            screen.dl.clear()
            
            profiler.start("update")
            update()
            profiler.end("update")
            
            profiler.start("draw_all")
            draw()
            profiler.end("draw_all")
            
            # Wait for Core 1 to finish previous frame rendering
            profiler.start("sync")
            _lightengine.sync()
            profiler.end("sync")
            
            # Submit newly built display list for Core 1 to start rendering into CURRENT buffer AND sending it via SPI
            from engine.palette import colors565
            profiler.start("submit")
            _lightengine.submit_and_send(screen._c_fbs[screen.buf_idx], screen.dl, colors565)
            profiler.end("submit")
            
            # Print free memory every 600 frames to monitor leaks
            if engine_time.clock.frame_count % 600 == 0:
                print(f"FPS: {engine_time.clock.fps} | Free Mem: {gc.mem_free()} bytes")
            
            profiler.start("sleep")
            t1 = time.ticks_ms()
            dt = time.ticks_diff(t1, t0)
            sleep_ms = target_ms - dt
            if sleep_ms > 0:
                # Sleep to yield CPU to FreeRTOS IDLE task (prevents Watchdog Timeout crash)
                if sleep_ms > 2:
                    time.sleep_ms(sleep_ms - 2)
                # Busy-wait the remaining time to avoid ESP32 RTOS tick rounding
                while time.ticks_diff(time.ticks_ms(), t0) < target_ms:
                    pass
            profiler.end("sleep")
    except Exception as e:
        with open('error.log', 'w') as f:
            sys.print_exception(e, f)
        raise
