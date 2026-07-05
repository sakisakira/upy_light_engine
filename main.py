from engine import framebuffer as fb
from engine.image import Image
from engine import sound
import math

try:
    import engine.font as font_lib
    score_font_6px = font_lib.Font("assets/fonts/test_6px_font.afnt")
    score_font_16px = font_lib.Font("assets/fonts/test_16px_font.afnt")
except Exception as e:
    import gc
    from engine import logger
    logger.error(f"Could not load font: {e} (Free memory: {gc.mem_free()} bytes)")
    score_font_6px = None
    score_font_16px = None

# --- Lookup Tables for Performance (Float Reduction) ---
# To avoid allocating float objects and calling math.sin during the game loop
# (which is very slow on MicroPython), we precompute animation tables.
# Using tuple() ensures we pre-allocate float objects so they don't allocate during the loop.
BREATH_SCALE_TABLE = tuple(1.0 + 0.2 * math.sin(i * 0.1) for i in range(63)) # 63 frames full cycle
GRAD_SCALE_TABLE = tuple(1.5 + 0.5 * math.sin(i * 0.05) for i in range(126))
ROT_TABLE = tuple(i * 0.05 for i in range(126))
TRI_SCALE_TABLE = tuple(1.2 + 0.3 * math.sin(i * 0.03) for i in range(210))

# Remove particle system demonstration as it slowed down the main loop

# Generate a test INDEX8 sprite (circle: top red, bottom blue)
def create_test_image(width, height):
    buf = bytearray(width * height)
    
    cx = (width - 1) / 2.0
    cy = (height - 1) / 2.0
    radius_sq = (width / 2.0) ** 2
    
    col_red = fb.color(255, 0, 0)
    col_blue = fb.color(0, 0, 255)
    
    for y in range(height):
        for x in range(width):
            if (x - cx)**2 + (y - cy)**2 <= radius_sq:
                if y < cy:
                    buf[y * width + x] = col_red
                else:
                    buf[y * width + x] = col_blue
            
    # Use Image class as a container for sprite data
    return Image(width, height, buf)

# Generate a test INDEX8 sprite (solid cyan circle since no alpha)
def create_gradient_image(width, height):
    buf = bytearray(width * height)
    
    col_cyan = fb.color(0, 255, 255)
    
    for y in range(height):
        for x in range(width):
            cx = (width - 1) / 2.0
            cy = (height - 1) / 2.0
            dist = ((x - cx)**2 + (y - cy)**2)**0.5
            max_dist = width / 2.0
            
            if dist < max_dist:
                # Dithering effect for gradient
                if (x + y) % 2 == 0 or dist < max_dist * 0.5:
                    buf[y * width + x] = col_cyan
            
    return Image(width, height, buf)

# Generate a test INDEX8 sprite (RGB triangle)
def create_triangle_image(width, height):
    buf = bytearray(width * height)
    
    col_r = fb.color(255, 0, 0)
    col_g = fb.color(0, 255, 0)
    col_b = fb.color(0, 0, 255)
    
    cx = width / 2.0
    for y in range(height):
        for x in range(width):
            if 2 <= y <= height - 2:
                half_width = y * 0.5
                if cx - half_width <= x <= cx + half_width:
                    if y < height / 3:
                        c = col_r
                    elif x < cx:
                        c = col_g
                    else:
                        c = col_b
                    
                    buf[y * width + x] = c
            
    return Image(width, height, buf)

# --- Cached Colors ---
COL_BG_A = None
COL_BG_B = None
COL_BG_DEF = None
COL_RED = None
COL_WHITE = None
COL_MAGENTA = None
COL_CYAN = None
COL_YELLOW = None
COL_GRAY = None
COL_BLACK = None

# --- Game State ---
x = 100
y = 50
dx = 2
dy = 2
sprite = None
sprite_gradient = None
sprite_triangle = None
score_font = None
score_font_half = None
# Fonts are now loaded at the top
frames = 0
is_start_pressed = False

def update():
    global x, y, dx, dy, frames
    global is_start_pressed
    from engine import input as inp
    from engine.time import clock
    
    current_start = inp.button(inp.Button_Start)
    if current_start and not is_start_pressed:
        if clock.is_paused:
            clock.resume()
        else:
            clock.pause()
    is_start_pressed = current_start
    
    if clock.is_paused:
        return
        
    sound.update()
    frames += 1
    
    if frames == 120:
        sound.play_mml("V32 T180 O5 C8 E8 G8 O6 C4 O5 G8 E8 C2")
    
    if inp.button(inp.Button_Left):
        x -= 2
    if inp.button(inp.Button_Right):
        x += 2
    if inp.button(inp.Button_Up):
        y -= 2
    if inp.button(inp.Button_Down):
        y += 2
    
    # Restrict to screen edges
    if x <= 0: x = 0
    if x >= 240 - 32: x = 240 - 32
    if y <= 0: y = 0
    if y >= 135 - 32: y = 135 - 32

def draw():
    from engine import input as inp
    try:
        from engine.profiler import profiler
        profiler.enabled = False
    except ImportError:
        pass
    
    profiler.start("draw_rects")
    # Fill background depending on button press
    if inp.button(inp.Button_A):
        fb.screen.fill(COL_BG_A) # Red for A
    elif inp.button(inp.Button_B):
        fb.screen.fill(COL_BG_B) # Green for B
    else:
        fb.screen.fill(COL_BG_DEF) # Default dark blue

    # Draw multiple rectangles to easily check if alpha blending works
    for i in range(5):
        bx = 50 + i * 30
        by = 40 + i * 10
        fb.screen.rect(bx, by, 40, 40, COL_RED) # Opaque Red
        
    profiler.end("draw_rects")

    profiler.start("draw_sprites")
    # Blend the sprite
    if sprite:
        # Convert left-top (x, y) to center (cx, cy)
        cx = x + sprite.w // 2
        cy = y + sprite.h // 2
        
        # Breathing animation using LUT
        breath_scale = BREATH_SCALE_TABLE[frames % len(BREATH_SCALE_TABLE)]
        fb.screen.sprite(cx, cy, sprite, scale=breath_scale)
        
    if sprite_gradient:
        cx_grad = (x - 40) + sprite_gradient.w // 2
        cy_grad = y + sprite_gradient.h // 2
        
        # Breathing animation using LUT
        grad_scale = GRAD_SCALE_TABLE[frames % len(GRAD_SCALE_TABLE)]
        fb.screen.sprite(cx_grad, cy_grad, sprite_gradient, scale=grad_scale)
        
    if sprite_triangle:
        cx_tri = (x + 40) + sprite_triangle.w // 2
        cy_tri = (y + 40) + sprite_triangle.h // 2
        # Continuous rotation using LUT
        rot = ROT_TABLE[frames % len(ROT_TABLE)]
        # Scale oscillates slightly using LUT
        tri_scale = TRI_SCALE_TABLE[frames % len(TRI_SCALE_TABLE)]
        fb.screen.sprite(cx_tri, cy_tri, sprite_triangle, rotate=rot, scale=tri_scale)

    # Test pset
    fb.screen.pset(10, 10, COL_WHITE)
    
    # Test line primitives (with different colors and positions so they don't overlap text)
    fb.screen.line(10, 110, 100, 110, COL_MAGENTA) # horizontal (Magenta)
    fb.screen.line(110, 80, 110, 120, COL_CYAN) # vertical (Cyan)
    profiler.end("draw_sprites")

    profiler.start("draw_text")
    # Test text drawing
    import engine.font as font_lib
    if score_font:
        font_lib.text(fb.screen, 80, 10, b"SCORE 1234 (100%)", score_font, COL_YELLOW)
    if score_font_half:
        font_lib.text(fb.screen, 80, 50, b"SCORE 1234 (50%)", score_font_half, COL_YELLOW)
    if score_font_6px:
        # Measure text first
        text_str = b"SCORE 1234 (6PX PIXEL FONT)"
        w, h = font_lib.measure_text(text_str, score_font_6px)
        
        # Draw a dark gray background rectangle exactly matching the text bounds
        fb.screen.rect(80, 80, w + 1, h + 1, COL_GRAY)
        font_lib.text_shadowed(fb.screen, 80, 80, text_str, score_font_6px, color=COL_YELLOW, shadow_color=COL_BLACK)
        
    if score_font_16px:
        text_str_16 = b"HELLO 16PX FONT!"
        w16, h16 = font_lib.measure_text(text_str_16, score_font_16px)
        fb.screen.rect(10, 100, w16, h16, COL_GRAY)
        font_lib.text(fb.screen, 10, 100, text_str_16, score_font_16px, COL_WHITE)

    from engine.time import clock
    if score_font_6px:
        text_str = f"FPS: {clock.fps}"
        if clock.is_paused:
            text_str += " (PAUSED)"
        w, h = font_lib.measure_text(text_str, score_font_6px)
        fb.screen.rect(fb.screen.width - w - 2, 2, w + 1, h + 1, COL_BLACK)
        font_lib.text_shadowed(fb.screen, fb.screen.width - w - 2, 2, text_str, score_font_6px, color=COL_YELLOW, shadow_color=COL_BLACK)
    profiler.end("draw_text")

if __name__ == "__main__":
    from engine import logger
    # Set to False to mute all debug logs
    logger.DEBUG_ENABLED = True

    try:
        from engine import palette
        palette.load_palette("assets/images/palette.bin")
        
        # Initialize color constants once
        COL_BG_A = fb.color(136, 0, 0)
        COL_BG_B = fb.color(0, 136, 0)
        COL_BG_DEF = fb.color(0, 0, 136)
        COL_RED = fb.color(255, 0, 0)
        COL_WHITE = fb.color(255, 255, 255)
        COL_MAGENTA = fb.color(255, 0, 255)
        COL_CYAN = fb.color(0, 255, 255)
        COL_YELLOW = fb.color(255, 255, 0)
        COL_GRAY = fb.color(50, 50, 50)
        COL_BLACK = fb.color(0, 0, 0)
        
        img_sprite = Image.load("assets/images/test_sprite.uimg")
    except Exception as e:
        logger.error(f"Failed to load uimg or palette: {e}")
        img_sprite = create_test_image(16, 16)
    sprite = img_sprite.subimage(0, 0, img_sprite.width, img_sprite.height)
        
    img_gradient = create_gradient_image(32, 32)
    sprite_gradient = img_gradient.subimage(0, 0, img_gradient.width, img_gradient.height)
    
    img_triangle = create_triangle_image(32, 32)
    sprite_triangle = img_triangle.subimage(0, 0, img_triangle.width, img_triangle.height)
    
    logger.debug("test 1: Engine init complete")
        
    logger.debug("test 5: Before fb.run")
    
    # Start the game loop at 60 FPS
    fb.run(update, draw, fps=60)
