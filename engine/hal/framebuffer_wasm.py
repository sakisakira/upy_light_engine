import sys

# WASM environment needs 'js' and 'pyodide'
try:
    import js
    from pyodide.ffi import to_js
except ImportError:
    pass

from .engine_ctypes import FramebufferBase

class Framebuffer(FramebufferBase):
    def __init__(self, width, height, buffer=None):
        super().__init__(width, height, buffer)
        
        js.eval("""
        window.drawFramebufferWasm = function(canvasId, buffer8, palette24, w, h) {
            const canvas = document.getElementById(canvasId);
            if (!canvas) return;
            const ctx = canvas.getContext("2d");
            
            // Re-create image data if dimensions don't match
            if (!window._wasmImgData || window._wasmImgData.width !== w || window._wasmImgData.height !== h) {
                window._wasmImgData = ctx.createImageData(w, h);
                // Also resize the canvas to match the framebuffer exactly (optional, but good for scaling)
                canvas.width = w;
                canvas.height = h;
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

# ---- Window and Game Loop Management ----
screen = Framebuffer(240, 135)
_update_func = None
_draw_func = None
_target_fps = 30
_last_time = 0

def _tick(timestamp):
    global _last_time
    
    # Calculate delta time
    if _last_time == 0:
        _last_time = timestamp
    
    elapsed = timestamp - _last_time
    target_ms = 1000.0 / _target_fps
    
    # Simple frame limiter (requestAnimationFrame might fire faster than target FPS)
    if elapsed < target_ms - 2: # 2ms tolerance
        js.window.requestAnimationFrame(_tick_proxy)
        return
        
    _last_time = timestamp

    from engine import time as engine_time
    engine_time.clock.tick()
    
    if _update_func:
        _update_func()
        
    if _draw_func:
        _draw_func()
        
    # Flush DisplayList commands to C buffer
    screen._flush()

    # Pass buffer to Javascript for canvas rendering
    from engine import palette
    import array
    
    # Convert palette to flat JS array
    pal_array = array.array('I', palette.colors)
    
    js.window.drawFramebufferWasm("gameCanvas", screen.buffer, pal_array, screen.width, screen.height)
    
    # Process audio
    from engine import sound
    if hasattr(sound._hal, 'update'):
        sound._hal.update()

    # Request next frame
    js.window.requestAnimationFrame(_tick_proxy)


_tick_proxy = None

def init(width, height, title="Pyxel (WASM + Native C Engine)", fps=30, scale=2):
    global _target_fps, screen, _tick_proxy
    screen.reinit(width, height)
    _target_fps = fps
    
    if "js" in sys.modules:
        import js
        from pyodide.ffi import create_proxy
        _tick_proxy = create_proxy(_tick)
        js.document.title = title
        
        # Initialize input system
        from engine import input as inp
        inp.init()

def run(update, draw, fps=30):
    global _update_func, _draw_func, _target_fps
    _update_func = update
    _draw_func = draw
    _target_fps = fps
    
    if _tick_proxy is None:
        init(240, 135, fps=fps)
        
    if "js" in sys.modules:
        import js
        # Start the requestAnimationFrame loop
        js.window.requestAnimationFrame(_tick_proxy)
    else:
        print("WASM run() called outside of Pyodide environment.")

def title(t):
    if "js" in sys.modules:
        import js
        js.document.title = t
