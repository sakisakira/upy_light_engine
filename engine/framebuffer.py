import sys

if sys.platform == 'esp32':
    from engine.hal.framebuffer_micropython import Framebuffer, screen
elif sys.platform == 'emscripten':
    from engine.hal.framebuffer_wasm import Framebuffer, screen
else:
    from engine.hal.framebuffer_cpython import Framebuffer, screen

def color(r, g, b, a=255):
    """
    Utility to find the nearest INDEX8 palette color from RGB.
    If a < 128, returns 0 (colorkey).
    
    WARNING: This function performs an expensive pure Python search 
    over the 256-color palette (up to 255 iterations). 
    DO NOT call this inside a game loop (e.g. inside draw()).
    Instead, pre-calculate the color at initialization and cache 
    the resulting index integer in your game script!
    """
    if a < 128:
        return 0
        
    from engine import palette
    
    min_dist = float('inf')
    best_idx = 0
    for i in range(1, 256): # skip 0 (colorkey)
        c = palette.colors[i]
        pr = (c >> 16) & 0xFF
        pg = (c >> 8) & 0xFF
        pb = c & 0xFF
        dist = (r - pr)**2 + (g - pg)**2 + (b - pb)**2
        if dist < min_dist:
            min_dist = dist
            best_idx = i
            if dist == 0:
                break
                
    return best_idx
