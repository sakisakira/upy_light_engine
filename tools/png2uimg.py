import argparse
import struct
import sys
from PIL import Image

def main():
    parser = argparse.ArgumentParser(description="Convert PNG to UIMG (ARGB4444) format.")
    parser.add_argument("input", help="Input PNG file")
    parser.add_argument("output", help="Output UIMG file")
    args = parser.parse_args()

    try:
        img = Image.open(args.input).convert("RGBA")
    except Exception as e:
        print(f"Error opening image: {e}")
        sys.exit(1)

    width, height = img.size
    if width > 65535 or height > 65535:
        print("Image dimensions too large.")
        sys.exit(1)

    # uimg header
    # Magic: 'UIMG' (4 bytes)
    # Version: 1 (1 byte)
    # Format: 1 (1 byte) -> 1=ARGB4444
    # Width: 2 bytes (LE)
    # Height: 2 bytes (LE)
    # Total header size: 10 bytes
    header = struct.pack("<4sBBHH", b"UIMG", 1, 1, width, height)

    pixels = img.load()
    data = bytearray()

    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            
            # Convert 8-bit to 4-bit
            a4 = a >> 4
            r4 = r >> 4
            g4 = g >> 4
            b4 = b >> 4
            
            # Pack as ARGB4444 (A is most significant nibble)
            val = (a4 << 12) | (r4 << 8) | (g4 << 4) | b4
            
            # Store as Little Endian 16-bit
            data.extend(struct.pack("<H", val))

    with open(args.output, "wb") as f:
        f.write(header)
        f.write(data)

    print(f"Converted {args.input} to {args.output} ({width}x{height})")

if __name__ == "__main__":
    main()
