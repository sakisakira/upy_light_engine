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

def update():
    global x, y, dx, dy
    x += dx
    y += dy
    
    # Bounce at screen edges
    if x <= 0 or x >= 240 - 32:
        dx = -dx
    if y <= 0 or y >= 135 - 32:
        dy = -dy

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

if __name__ == "__main__":
    sprite = create_test_sprite(32, 32)
    # Start the game loop at 60 FPS
    fb.run(update, draw, fps=60)
