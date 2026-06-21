import sys

from image import Image

class Font:
    def __init__(self, filepath):
        with open(filepath, 'rb') as f:
            header = f.read(4)
            if header not in (b"AFNT", b"AFN2"):
                raise ValueError(f"Invalid font file format: {filepath}")
            
            meta = f.read(4)
            self.char_w = meta[0]
            self.char_h = meta[1]
            self.cols = meta[2]
            self.rows = meta[3]
            
            self.char_map = None
            if header == b"AFN2":
                num_chars = int.from_bytes(f.read(2), 'little')
                self.char_map = {}
                for i in range(num_chars):
                    cp = int.from_bytes(f.read(2), 'little')
                    self.char_map[cp] = i
            
            # Read pixel data (ARGB4444)
            pixel_data = bytearray(f.read())
            
        img_w = self.char_w * self.cols
        img_h = self.char_h * self.rows
        
        self.image = Image(img_w, img_h, pixel_data)

def measure_text(string, font, spacing=0):
    """
    Calculate the bounding box of the text if it were drawn.
    Returns (width, height).
    """
    w = 0
    h = font.char_h if string else 0
    current_w = 0
    
    for char in string:
        if char == '\n':
            if current_w > w:
                w = current_w
            current_w = 0
            h += font.char_h
        else:
            code = ord(char)
            if font.char_map is not None:
                if code in font.char_map:
                    current_w += font.char_w + spacing
            else:
                if 0x20 <= code <= 0x7E:
                    current_w += font.char_w + spacing
                
    if current_w > w:
        w = current_w
        
    # Remove the extra spacing at the end of the longest line if length > 0
    if w > 0:
        w -= spacing
        
    return w, h

def text(fb, x, y, string, font, spacing=0):
    """
    Draw a string to the framebuffer using the given Font.
    ASCII range 0x20 to 0x7E is supported.
    spacing: extra pixels (can be negative) to add between characters.
    """
    cx = x
    cy = y
    for char in string:
        if char == '\n':
            cx = x
            cy += font.char_h
            continue
            
        code = ord(char)
        index = -1
        if font.char_map is not None:
            if code in font.char_map:
                index = font.char_map[code]
        else:
            if 0x20 <= code <= 0x7E:
                index = code - 0x20
                
        if index >= 0:
            col = index % font.cols
            row = index // font.cols
            
            u = col * font.char_w
            v = row * font.char_h
            
            # Use alpha blending (blt handles ARGB4444 automatically)
            fb.blt(cx, cy, font.image, u, v, font.char_w, font.char_h)
            
        # Advance cursor
        cx += font.char_w + spacing
