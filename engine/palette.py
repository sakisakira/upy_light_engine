"""
Palette management for 8-bit INDEX8 architecture.
Provides `colors` list to manipulate the global 256-color palette at runtime.
"""

# Global palette storing 24-bit RGB values (for easy user manipulation)
# Internal ST7789 display will use colors565 which is derived from this.
colors = [0] * 256
colors565 = bytearray(256 * 2)

def rgb24_to_565(rgb24):
    r = (rgb24 >> 16) & 0xFF
    g = (rgb24 >> 8) & 0xFF
    b = rgb24 & 0xFF
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

# Initialize with a default RGB332 palette so it's not completely black by default
colors = [0] * 256
colors565 = bytearray(256 * 2)

for _i in range(256):
    _r = (_i >> 5) * 255 // 7
    _g = ((_i >> 2) & 7) * 255 // 7
    _b = (_i & 3) * 255 // 3
    _c = (_r << 16) | (_g << 8) | _b
    colors[_i] = _c
    _v = rgb24_to_565(_c)
    colors565[_i * 2] = _v & 0xFF
    colors565[_i * 2 + 1] = (_v >> 8) & 0xFF

class ColorsList:
    """
    List-like interface for modifying palette colors (24-bit RGB).
    Automatically updates the 16-bit RGB565 internal buffer when modified.
    """
    def __getitem__(self, index):
        return colors[index]
        
    def __setitem__(self, index, rgb24):
        colors[index] = rgb24
        
        # Update internal 565 buffer (Little Endian for SPI/ST7789)
        val565 = rgb24_to_565(rgb24)
        colors565[index * 2] = val565 & 0xFF
        colors565[index * 2 + 1] = (val565 >> 8) & 0xFF

    def __len__(self):
        return 256

# Expose as a list-like object
colors_api = ColorsList()

def load_palette(filepath):
    """
    Load the global palette.bin (24-bit RGB format, 3 bytes per color).
    """
    try:
        with open(filepath, "rb") as f:
            data = f.read(256 * 3)
            
        for i in range(256):
            if i * 3 + 2 < len(data):
                r = data[i * 3]
                g = data[i * 3 + 1]
                b = data[i * 3 + 2]
                rgb24 = (r << 16) | (g << 8) | b
                colors_api[i] = rgb24
                
    except Exception as e:
        print(f"Error loading palette {filepath}: {e}")
