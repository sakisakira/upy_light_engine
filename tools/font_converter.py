import sys
import argparse
import os

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Error: Pillow is required to run the font converter.")
    print("Please install it using: pip install Pillow")
    sys.exit(1)

def convert_png(png_path, out_path, colkey=None):
    try:
        img = Image.open(png_path).convert("RGBA")
    except Exception as e:
        print(f"Error loading PNG: {e}")
        sys.exit(1)
        
    cols = 16
    rows = 6
    char_w = img.width // cols
    char_h = img.height // rows
    
    pixels = img.load()
    
    # Handle color keying (e.g., treat black as transparent)
    if colkey is not None:
        for py in range(img.height):
            for px in range(img.width):
                r, g, b, a = pixels[px, py]
                if (r, g, b) == colkey:
                    pixels[px, py] = (0, 0, 0, 0)

    # Save preview PNG
    preview_path = out_path.replace('.afnt', '_preview.png')
    img.save(preview_path)
    print(f"Saved preview to {preview_path} (size: {img.width}x{img.height}, cell: {char_w}x{char_h})")

    with open(out_path, 'wb') as f:
        f.write(b"AFNT")
        f.write(bytes([char_w, char_h, cols, rows]))
        
        for py in range(img.height):
            for px in range(img.width):
                r, g, b, a = pixels[px, py]
                val = ((a >> 4) << 12) | ((r >> 4) << 8) | ((g >> 4) << 4) | (b >> 4)
                f.write(val.to_bytes(2, byteorder='little'))
                
    print(f"Converted PNG to AFNT: {out_path}")

def convert_font(font_path, out_path, size=16, color=(255, 255, 255, 255),
                 shadow_color=None, shadow_offset=(1, 1), bold=False, no_aa=False):
    try:
        font = ImageFont.truetype(font_path, size)
    except IOError:
        try:
            # Fallback to default if load fails, though default might not support size
            font = ImageFont.load_default()
            print(f"Warning: Could not load {font_path}, using default font.")
        except Exception as e:
            print(f"Error loading font: {e}")
            sys.exit(1)

    # Calculate bounding box for the tallest/widest characters
    ascent, descent = font.getmetrics()
    
    char_w = 0
    for i in range(95):
        c = chr(0x20 + i)
        bbox = font.getbbox(c)
        if bbox:
            char_w = max(char_w, bbox[2])
            
        try:
            char_w = max(char_w, int(font.getlength(c)))
        except AttributeError:
            w, _ = font.getsize(c)
            char_w = max(char_w, w)

    # Ensure min size and add padding for shadows/bold
    padding_x = 2 + (shadow_offset[0] if shadow_color else 0) + (1 if bold else 0)
    padding_y = 2 + (shadow_offset[1] if shadow_color else 0) + (1 if bold else 0)
    char_w += padding_x
    char_h = ascent + descent + padding_y
    
    # We will map ASCII 0x20 to 0x7E (95 characters)
    # A grid of 16 columns x 6 rows = 96 cells
    cols = 16
    rows = 6
    img_w = char_w * cols
    img_h = char_h * rows

    # Create transparent image (RGBA)
    img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    for i in range(95):
        char_code = 0x20 + i
        char_str = chr(char_code)
        
        col = i % cols
        row = i // cols
        
        x = col * char_w
        y = row * char_h
        
        # Center horizontally
        try:
            w = int(font.getlength(char_str))
        except AttributeError:
            w, _ = font.getsize(char_str)
            
        cx = x + (char_w - w - padding_x) // 2 + 1
        cy = y + 1
        
        # Draw shadow
        if shadow_color:
            draw.text((cx + shadow_offset[0], cy + shadow_offset[1]), char_str, font=font, fill=shadow_color)
        
        # Draw main text
        draw.text((cx, cy), char_str, font=font, fill=color, stroke_width=1 if bold else 0)

    if no_aa:
        pixels = img.load()
        for py in range(img_h):
            for px in range(img_w):
                r, g, b, a = pixels[px, py]
                pixels[px, py] = (r, g, b, 255 if a > 127 else 0)

    # Save preview PNG
    preview_path = out_path.replace('.afnt', '_preview.png')
    img.save(preview_path)
    print(f"Saved preview to {preview_path} (size: {img_w}x{img_h}, cell: {char_w}x{char_h})")

    # Convert to ARGB4444 binary format
    # Header: "AFNT" (4) + char_w (1) + char_h (1) + cols (1) + rows (1)
    with open(out_path, 'wb') as f:
        f.write(b"AFNT")
        f.write(bytes([char_w, char_h, cols, rows]))
        
        # Pixel data
        pixels = img.load()
        for py in range(img_h):
            for px in range(img_w):
                r, g, b, a = pixels[px, py]
                # ARGB4444
                a4 = a >> 4
                r4 = r >> 4
                g4 = g >> 4
                b4 = b >> 4
                val = (a4 << 12) | (r4 << 8) | (g4 << 4) | b4
                f.write(val.to_bytes(2, byteorder='little'))
                
    print(f"Saved ARGB4444 font data to {out_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert TTF/BDF fonts to AFNT (ARGB4444) for upy_light_engine.")
    parser.add_argument("font", help="Path to input font file (.ttf, .bdf)")
    parser.add_argument("out", help="Path to output .afnt file")
    parser.add_argument("--size", type=int, default=16, help="Font size")
    parser.add_argument("--bold", action="store_true", help="Apply bold effect")
    parser.add_argument("--shadow", action="store_true", help="Add drop shadow")
    parser.add_argument("--color", type=int, nargs=4, default=(255, 255, 255, 255), metavar=('R', 'G', 'B', 'A'), help="Main text color (RGBA 0-255)")
    parser.add_argument("--scolor", type=int, nargs=4, default=(0, 0, 0, 180), metavar=('R', 'G', 'B', 'A'), help="Shadow color (RGBA 0-255)")
    parser.add_argument("--soffset", type=int, nargs=2, default=(1, 1), metavar=('X', 'Y'), help="Shadow offset")
    parser.add_argument("--no-aa", action="store_true", help="Disable anti-aliasing (useful for small sizes)")
    parser.add_argument("--colkey", type=int, nargs=3, metavar=('R', 'G', 'B'), help="Transparent color key for PNG input (e.g., 0 0 0 for black)")
    
    args = parser.parse_args()
    
    if args.font.lower().endswith('.png'):
        colkey = tuple(args.colkey) if args.colkey else None
        convert_png(args.font, args.out, colkey=colkey)
    else:
        shadow_color = tuple(args.scolor) if args.shadow else None
        main_color = tuple(args.color)
        
        convert_font(args.font, args.out, size=args.size, color=main_color,
                     shadow_color=shadow_color, shadow_offset=args.soffset, bold=args.bold, no_aa=args.no_aa)
