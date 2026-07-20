import sys

from engine.image import Image

class Font:
    _cache = {}

    def __new__(cls, filepath):
        if filepath in cls._cache:
            return cls._cache[filepath]
        instance = super().__new__(cls)
        cls._cache[filepath] = instance
        return instance

    def __init__(self, filepath):
        if hasattr(self, 'char_w'):
            return
            
        import sys
        is_frozen = False
        data_bytes = None
        if sys.platform == 'esp32':
            try:
                import font_data
                name = filepath.split('/')[-1].replace('.afnt', '')
                if hasattr(font_data, name):
                    data_bytes = getattr(font_data, name)
                    is_frozen = True
            except ImportError:
                pass

        if is_frozen:
            mv = memoryview(data_bytes)
            header = bytes(mv[0:4])
            if header not in (b"AFNT", b"AFN2"):
                raise ValueError(f"Invalid font format in frozen: {filepath}")
            self.char_w = data_bytes[4]
            self.char_h = data_bytes[5]
            self.cols = data_bytes[6]
            self.rows = data_bytes[7]
            self.char_map = None
            
            offset = 8
            if header == b"AFN2":
                num_chars = int.from_bytes(bytes(mv[offset:offset+2]), 'little')
                offset += 2
                self.char_map = {}
                for i in range(num_chars):
                    cp = int.from_bytes(bytes(mv[offset:offset+2]), 'little')
                    self.char_map[cp] = i
                    offset += 2
                    
            img_w = self.char_w * self.cols
            img_h = self.char_h * self.rows
            pixel_data = mv[offset:offset + img_w * img_h]
        else:
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
                
                img_w = self.char_w * self.cols
                img_h = self.char_h * self.rows
                
                # Read pixel data (INDEX8) efficiently without intermediate bytes object
                pixel_data = bytearray(img_w * img_h)
                f.readinto(pixel_data)
            
            
        self.image = Image(img_w, img_h, pixel_data)
        
        if sys.platform != 'esp32':
            import ctypes
            self._c_lookup = (ctypes.c_int16 * 256)()
            for i in range(256):
                self._c_lookup[i] = -1
                
            if self.char_map is not None:
                for cp, idx in self.char_map.items():
                    if 0 <= cp < 256:
                        self._c_lookup[cp] = idx
            else:
                for cp in range(0x20, 0x7E + 1):
                    self._c_lookup[cp] = cp - 0x20

def measure_text(string, font, spacing=0):
    """
    Measure the pixel width and height of a string using the specified Font.
    """
    if not string:
        return 0, 0
        
    lines = string.split(b'\n' if type(string) is bytes or type(string) is bytearray else '\n')
    h = len(lines) * font.char_h
    
    max_chars = 0
    for line in lines:
        if len(line) > max_chars:
            max_chars = len(line)
            
    if max_chars == 0:
        return 0, h
        
    w = max_chars * (font.char_w + spacing) - spacing
    return w, h

def text(fb, x, y, string, font, color=None, spacing=0):
    """
    Draw a string to the framebuffer using the specified Font.
    ASCII range 0x20 to 0x7E is supported.
    spacing: extra pixels (can be negative) to add between characters.
    """
    # Delegate to optimized C module if available
    if hasattr(fb, 'text') and spacing == 0:
        fb.text(font, string, x, y, color=color, scale=1.0)
        return

    cx = x
    cy = y
    for char in string:
        code = char if type(char) is int else ord(char)
        if char == '\n' or code == 10:
            cx = x
            cy += font.char_h
            continue
            
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
            
            # Use alpha blending (blt handles colorkey automatically)
            # Pass color as tint if provided
            fb.blt(cx, cy, font.image, u, v, font.char_w, font.char_h, tint=color)
            
        # Advance cursor
        cx += font.char_w + spacing

def text_shadowed(fb, x, y, string, font, color=1, shadow_color=0, shadow_offset=(1, 1), spacing=0):
    """
    Draw a string with a drop shadow.
    """
    if shadow_color is not None:
        text(fb, x + shadow_offset[0], y + shadow_offset[1], string, font, shadow_color, spacing)
    text(fb, x, y, string, font, color, spacing)
