import sys
import js
from engine.framebuffer import screen

# ---- Window and Game Loop Management ----
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
