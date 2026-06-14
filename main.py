import hal.framebuffer as fb

# Generate a test ARGB4444 sprite (semi-transparent circular gradient)
def create_test_sprite(width, height):
    buf = bytearray(width * height * 2)
    mv = memoryview(buf).cast('H')
    
    for y in range(height):
        for x in range(width):
            # Calculate alpha value based on distance from center (opaque at center, transparent at edges)
            cx = width / 2.0
            cy = height / 2.0
            dist = ((x - cx)**2 + (y - cy)**2)**0.5
            max_dist = width / 2.0
            
            a = max(0, min(15, int(15 * (1 - dist / max_dist))))
            
            # Set color to Cyan (R:0, G:15, B:15)
            r = 0
            g = 15
            b = 15
            
            # Pack into ARGB4444 format
            mv[y * width + x] = (a << 12) | (r << 8) | (g << 4) | b
            
    # Use Image class as a container for sprite data
    return fb.Image(width, height, buf)

# --- Game State ---
x = 100
y = 50
dx = 2
dy = 2
sprite = None
score_font = None
score_font_half = None
score_font_quarter = None

def update():
    global x, y, dx, dy
    import hal.input as inp
    
    if inp.button(inp.KEY_LEFT):
        x -= 2
    if inp.button(inp.KEY_RIGHT):
        x += 2
    if inp.button(inp.KEY_UP):
        y -= 2
    if inp.button(inp.KEY_DOWN):
        y += 2
    
    # Restrict to screen edges
    if x <= 0: x = 0
    if x >= 240 - 32: x = 240 - 32
    if y <= 0: y = 0
    if y >= 135 - 32: y = 135 - 32

def draw():
    # Fill background with dark blue (RGB: 0, 0, 136)
    fb.screen.fill(fb.color(0, 0, 136))
    
    # Draw multiple rectangles to easily check if alpha blending works
    for i in range(5):
        bx, by, bw, bh = 50 + i*30, 40 + i*10, 40, 40
        bcol = fb.color(255, 0, 0) # Opaque Red
        fb.screen.rect(bx, by, bw, bh, bcol)

    # Blend the sprite
    fb.screen.blt(x, y, sprite, 0, 0, 32, 32)

    # Test pset
    fb.screen.pset(10, 10, fb.color(255, 255, 255))
    
    # Test line primitives (with different colors and positions so they don't overlap text)
    fb.screen.line(10, 110, 100, 110, fb.color(255, 0, 255)) # horizontal (Magenta)
    fb.screen.line(110, 80, 110, 120, fb.color(0, 255, 255)) # vertical (Cyan)

    # Test text drawing
    import hal.font as font_lib
    if score_font:
        font_lib.text(fb.screen, 80, 10, "SCORE 1234 (100%)", score_font)
    if score_font_half:
        font_lib.text(fb.screen, 80, 50, "SCORE 1234 (50%)", score_font_half)
    if score_font_quarter:
        # Test measure_text and spacing options
        text_str = "SCORE 1234 (25%)"
        spacing_val = -2
        w, h = font_lib.measure_text(text_str, score_font_quarter, spacing=spacing_val)
        
        # Draw a dark gray background rectangle exactly matching the text bounds
        fb.screen.rect(80, 80, w, h, fb.color(50, 50, 50))
        
        # Draw the text on top
        font_lib.text(fb.screen, 80, 80, text_str, score_font_quarter, spacing=spacing_val)

if __name__ == "__main__":
    sprite = create_test_sprite(32, 32)
    
    import hal.font as font_lib
    try:
        score_font = font_lib.Font("fonts/score_font.afnt")
        score_font_half = font_lib.Font("fonts/score_font_half.afnt")
        score_font_quarter = font_lib.Font("fonts/score_font_quarter.afnt")
    except Exception as e:
        print("Could not load font:", e)
        
    # Start the game loop at 60 FPS
    fb.run(update, draw, fps=60)
