import argparse
import struct
import sys
import os
import glob
from PIL import Image
import math

def color_distance(c1, c2):
    return (c1[0]-c2[0])**2 + (c1[1]-c2[1])**2 + (c1[2]-c2[2])**2

def get_nearest_color_index(color, palette):
    min_dist = float('inf')
    best_idx = 0
    for i, p in enumerate(palette):
        if i == 0: continue # Skip colorkey
        dist = color_distance(color, p)
        if dist < min_dist:
            min_dist = dist
            best_idx = i
    return best_idx

def rgb888_to_rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

def process_directory(input_dir, output_palette_path):
    png_files = glob.glob(os.path.join(input_dir, "*.png"))
    if not png_files:
        print(f"No PNG files found in {input_dir}")
        return

    print(f"Found {len(png_files)} PNG files. Building common palette...")
    
    unique_colors = set()
    
    # 1. Collect all unique colors
    for png_path in png_files:
        img = Image.open(png_path).convert("RGBA")
        pixels = img.load()
        width, height = img.size
        for y in range(height):
            for x in range(width):
                r, g, b, a = pixels[x, y]
                if a >= 128:
                    unique_colors.add((r, g, b))
                    
    # 2. Build palette
    # Index 0 is reserved for transparent (colorkey)
    # Since Pyxel's transparent is typically black (0,0,0) and alpha=0, we just map anything with alpha<128 to index 0.
    palette = [(0, 0, 0)] 
    
    if len(unique_colors) > 255:
        print(f"Warning: Found {len(unique_colors)} colors. Quantizing to 255 colors.")
        unique_colors = list(unique_colors)[:255]
    else:
        print(f"Total unique solid colors found: {len(unique_colors)}")
        unique_colors = list(unique_colors)
        
    palette.extend(unique_colors)
    
    # Pad palette to 256 colors using RGB332
    idx = len(palette)
    while len(palette) < 256:
        r = (idx >> 5) * 255 // 7
        g = ((idx >> 2) & 7) * 255 // 7
        b = (idx & 3) * 255 // 3
        palette.append((r, g, b))
        idx += 1
        
    # Save palette as 24-bit RGB (it is easier for users to modify engine.colors if it's 24-bit RGB, but ST7789 needs 16-bit)
    # Wait, Pyxel exposes 24-bit RGB. Let's save as 24-bit RGB (3 bytes per color).
    # That's 256 * 3 = 768 bytes. The engine will load this and convert to RGB565 internally for fast transfer.
    print(f"Saving global palette to {output_palette_path} (24-bit RGB)...")
    with open(output_palette_path, "wb") as f:
        for r, g, b in palette:
            f.write(bytes([r, g, b]))
            
    # 3. Convert all images using the palette
    for png_path in png_files:
        uimg_path = os.path.splitext(png_path)[0] + ".uimg"
        convert_image(png_path, uimg_path, palette)
        
def convert_image(png_path, uimg_path, palette):
    img = Image.open(png_path).convert("RGBA")
    width, height = img.size
    
    if width > 65535 or height > 65535:
        print(f"Image {png_path} dimensions too large.")
        return

    # UIMG v2 Header (INDEX8)
    # Magic: 'UIMG' (4 bytes)
    # Version: 2 (1 byte) -> Version 2 = INDEX8
    # Format: 2 (1 byte) -> 2 = INDEX8
    # Width: 2 bytes (LE)
    # Height: 2 bytes (LE)
    # Total header size: 10 bytes
    header = struct.pack("<4sBBHH", b"UIMG", 2, 2, width, height)
    
    pixels = img.load()
    data = bytearray(width * height)
    
    idx = 0
    # Create a quick lookup for exact matches to speed up conversion
    color_map = {color: i for i, color in enumerate(palette)}
    
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if a < 128:
                data[idx] = 0 # Transparent colorkey
            else:
                color = (r, g, b)
                if color in color_map:
                    data[idx] = color_map[color]
                else:
                    data[idx] = get_nearest_color_index(color, palette)
            idx += 1

    with open(uimg_path, "wb") as f:
        f.write(header)
        f.write(data)

    print(f"Converted {os.path.basename(png_path)} -> {os.path.basename(uimg_path)} ({width}x{height}, INDEX8)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert directory of PNGs to INDEX8 UIMG format and generate a global palette.")
    parser.add_argument("input_dir", help="Directory containing PNG files")
    parser.add_argument("palette_out", help="Output path for the global palette.bin")
    args = parser.parse_args()

    process_directory(args.input_dir, args.palette_out)
