import sys
import argparse
import os
import struct

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Error: Pillow is required to run the font converter.")
    print("Please install it using: pip install Pillow")
    sys.exit(1)

def convert_png(png_path, out_path, colkey=None, color=None, shadow_color=None, shadow_offset=(1, 1), bold=False):
    """
    Convert a grid-based PNG image into an AFNT format font, with color/shadow support.
    """
    try:
        img = Image.open(png_path).convert("RGBA")
    except Exception as e:
        print(f"Error loading PNG: {e}")
        sys.exit(1)
        
    cols = 16
    rows = 6
    char_w = img.width // cols
    char_h = img.height // rows
    
    padding_x = (shadow_offset[0] if shadow_color else 0) + (1 if bold else 0)
    padding_y = (shadow_offset[1] if shadow_color else 0) + (1 if bold else 0)
    
    new_char_w = char_w + padding_x
    new_char_h = char_h + padding_y
    
    out_img = Image.new("RGBA", (cols * new_char_w, rows * new_char_h), (0, 0, 0, 0))
    
    for i in range(cols * rows):
        col = i % cols
        row = i // cols
        
        char_box = (col * char_w, row * char_h, (col + 1) * char_w, (row + 1) * char_h)
        char_crop = img.crop(char_box)
        
        if colkey is not None:
            c_pixels = char_crop.load()
            for py in range(char_crop.height):
                for px in range(char_crop.width):
                    r, g, b, a = c_pixels[px, py]
                    if (r, g, b) == colkey:
                        c_pixels[px, py] = (0, 0, 0, 0)
                        
        if color is not None:
            colorized = Image.new("RGBA", char_crop.size, color)
            # Use original image's alpha channel as mask
            main_layer = Image.composite(colorized, Image.new("RGBA", char_crop.size, (0,0,0,0)), char_crop.split()[3])
        else:
            main_layer = char_crop
            
        if shadow_color is not None:
            shadowized = Image.new("RGBA", char_crop.size, shadow_color)
            shadow_layer = Image.composite(shadowized, Image.new("RGBA", char_crop.size, (0,0,0,0)), char_crop.split()[3])
        else:
            shadow_layer = None
            
        dst_x = col * new_char_w
        dst_y = row * new_char_h
        
        if shadow_layer:
            out_img.alpha_composite(shadow_layer, (dst_x + shadow_offset[0], dst_y + shadow_offset[1]))
            
        if bold:
            out_img.alpha_composite(main_layer, (dst_x + 1, dst_y))
            
        out_img.alpha_composite(main_layer, (dst_x, dst_y))

    # Save preview PNG
    preview_path = out_path.replace('.afnt', '.png')
    out_img.save(preview_path)
    print(f"Saved preview to {preview_path} (size: {out_img.width}x{out_img.height}, cell: {new_char_w}x{new_char_h})")

    out_pixels = out_img.load()
    with open(out_path, 'wb') as f:
        f.write(b"AFNT")
        f.write(bytes([new_char_w, new_char_h, cols, rows]))
        
        for py in range(out_img.height):
            for px in range(out_img.width):
                r, g, b, a = out_pixels[px, py]
                val = ((a >> 4) << 12) | ((r >> 4) << 8) | ((g >> 4) << 4) | (b >> 4)
                f.write(val.to_bytes(2, byteorder='little'))
                
    print(f"Converted PNG to AFNT: {out_path}")

def convert_font(font_path, out_path, size=16, color=(255, 255, 255, 255),
                 shadow_color=None, shadow_offset=(1, 1), bold=False, no_aa=False, chars=None):
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

    # If chars is not provided, use default ASCII 0x20-0x7E
    if chars is None:
        char_list = [chr(0x20 + i) for i in range(95)]
        is_v2 = False
    else:
        # If chars is a file path, read it. Otherwise treat it as a string of chars.
        if os.path.exists(chars):
            with open(chars, 'r', encoding='utf-8') as f:
                chars_str = f.read()
        else:
            chars_str = chars
            
        char_list = sorted(list(set(chars_str)))
        # Remove control characters like newline
        char_list = [c for c in char_list if ord(c) >= 0x20]
        is_v2 = True

    num_chars = len(char_list)
    
    # Calculate bounding box for the tallest/widest characters
    ascent, descent = font.getmetrics()
    
    char_w = 0
    for c in char_list:
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
    
    # A grid of cols x rows
    cols = min(16, num_chars)
    rows = (num_chars + cols - 1) // cols
    img_w = char_w * cols
    img_h = char_h * rows

    # Create transparent image (RGBA)
    img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    for i, char_str in enumerate(char_list):
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
    preview_path = out_path.replace('.afnt', '.png')
    img.save(preview_path)
    print(f"Saved preview to {preview_path} (size: {img_w}x{img_h}, cell: {char_w}x{char_h})")

    # Convert to ARGB4444 binary format
    with open(out_path, 'wb') as f:
        if is_v2:
            f.write(b"AFN2")
            f.write(bytes([char_w, char_h, cols, rows]))
            f.write(num_chars.to_bytes(2, byteorder='little'))
            # Write codepoints
            for c in char_list:
                f.write(ord(c).to_bytes(2, byteorder='little'))
        else:
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
    description = """Convert TTF/BDF fonts or grid-based PNGs to AFNT (ARGB4444) for upy_light_engine.

Expected PNG Layout when using a .png input:
- 16 columns x 6 rows (96 cells total)
- Characters are mapped from ASCII 0x20 (Space) to 0x7E (~), total 95 characters.
- Each cell size is automatically calculated as (img.width // 16) x (img.height // 6).

The 6 lines of characters should be arranged exactly like this:
Row 1:  !"#$%&'()*+,-./
Row 2: 0123456789:;<=>?
Row 3: @ABCDEFGHIJKLMNO
Row 4: PQRSTUVWXYZ[\\]^_
Row 5: `abcdefghijklmno
Row 6: pqrstuvwxyz{|}~
(The very last cell at the end of Row 6 is unused)
"""
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawTextHelpFormatter
    )
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
    parser.add_argument("--chars", type=str, help="String of characters to include, or path to a text file. If provided, creates AFN2 format.")
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
        
    args = parser.parse_args()
    
    shadow_color = tuple(args.scolor) if args.shadow else None
    main_color = tuple(args.color)
    
    if args.font.lower().endswith('.png'):
        colkey = tuple(args.colkey) if args.colkey else None
        convert_png(args.font, args.out, colkey=colkey, color=main_color, 
                    shadow_color=shadow_color, shadow_offset=args.soffset, bold=args.bold)
    else:
        convert_font(args.font, args.out, size=args.size, color=main_color,
                     shadow_color=shadow_color, shadow_offset=args.soffset, bold=args.bold, no_aa=args.no_aa, chars=args.chars)
