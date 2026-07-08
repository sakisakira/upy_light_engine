import ctypes
import os
import sys

if sys.platform == 'emscripten':
    # PyScript preserves directory structure for fetched files
    dll_path = "./build/core_engine.so"
    if not os.path.exists(dll_path):
        dll_path = "./core_engine.so" # fallback
else:
    # For CPython on Windows/Mac, use relative path to build folder
    dll_name = "core_engine_win.dll" if sys.platform == 'win32' else "core_engine.dylib"
    dll_path = os.path.join(os.path.dirname(__file__), "..", "..", "build", dll_name)
    dll_path = os.path.abspath(dll_path)

if not os.path.exists(dll_path):
    raise FileNotFoundError(f"DLL not found: {dll_path}. Please run scripts/build_engine_dll.ps1 or build_engine_wasm.ps1")

core = ctypes.CDLL(dll_path)

# --- C Structs ---

class CEngineImage(ctypes.Structure):
    _fields_ = [
        ("width", ctypes.c_int16),
        ("height", ctypes.c_int16),
        ("format", ctypes.c_uint8),
        ("data", ctypes.c_void_p)
    ]

class CEngineSprite(ctypes.Structure):
    _fields_ = [
        ("image", ctypes.POINTER(CEngineImage)),
        ("u", ctypes.c_int16),
        ("v", ctypes.c_int16),
        ("w", ctypes.c_int16),
        ("h", ctypes.c_int16),
        ("colkey", ctypes.c_uint16)
    ]

class CEngineFramebuffer(ctypes.Structure):
    _fields_ = [
        ("width", ctypes.c_int16),
        ("height", ctypes.c_int16),
        ("format", ctypes.c_uint8),
        ("buffer", ctypes.c_void_p)
    ]

class CRenderCommand(ctypes.Structure):
    _fields_ = [("data", ctypes.c_uint8 * 64)] # pad

class CDisplayList(ctypes.Structure):
    _fields_ = [
        ("commands", CRenderCommand * 256),
        ("count", ctypes.c_int)
    ]

# --- C Functions ---

# We use c_void_p to represent pointers here instead of ctypes.POINTER().
# This avoids a known bug in Pyodide's ctypes implementation where POINTER 
# types can cause memory corruption or type casting errors across the WASM boundary.
# By using c_void_p, pointers are safely passed as opaque integers on both 
# Windows (64-bit) and WASM (32-bit). We define aliases for readability.
CDisplayList_p = ctypes.c_void_p
CEngineImage_p = ctypes.c_void_p
CEngineSprite_p = ctypes.c_void_p
CEngineFramebuffer_p = ctypes.c_void_p
Uint8_p = ctypes.c_void_p
Int16_p = ctypes.c_void_p

core.dl_create.argtypes = []
core.dl_create.restype = CDisplayList_p

core.dl_destroy.argtypes = [CDisplayList_p]
core.dl_destroy.restype = None

core.dl_init.argtypes = [CDisplayList_p]
core.dl_init.restype = None

core.dl_clear.argtypes = [CDisplayList_p]
core.dl_clear.restype = None

core.dl_push_clear.argtypes = [CDisplayList_p, ctypes.c_uint16]
core.dl_push_clear.restype = None

core.dl_push_pset.argtypes = [CDisplayList_p, ctypes.c_int16, ctypes.c_int16, ctypes.c_uint16]
core.dl_push_pset.restype = None

core.dl_push_line.argtypes = [CDisplayList_p, ctypes.c_int16, ctypes.c_int16, ctypes.c_int16, ctypes.c_int16, ctypes.c_uint16]
core.dl_push_line.restype = None

core.dl_push_fill_rect.argtypes = [CDisplayList_p, ctypes.c_int16, ctypes.c_int16, ctypes.c_int16, ctypes.c_int16, ctypes.c_uint16]
core.dl_push_fill_rect.restype = None

core.dl_push_blt.argtypes = [
    CDisplayList_p, ctypes.c_int16, ctypes.c_int16,
    CEngineImage_p, ctypes.c_int16, ctypes.c_int16,
    ctypes.c_int16, ctypes.c_int16, ctypes.c_uint16, ctypes.c_int
]
core.dl_push_blt.restype = None

core.dl_push_draw_sprite.argtypes = [
    CDisplayList_p, ctypes.c_int16, ctypes.c_int16,
    ctypes.c_float, ctypes.c_float,
    CEngineImage_p, ctypes.c_int16, ctypes.c_int16,
    ctypes.c_int16, ctypes.c_int16, ctypes.c_uint16, ctypes.c_int
]
core.dl_push_draw_sprite.restype = None

core.dl_push_draw_text.argtypes = [
    CDisplayList_p, ctypes.c_int16, ctypes.c_int16,
    CEngineImage_p, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    Uint8_p, ctypes.c_int,
    Int16_p, ctypes.c_int
]
core.dl_push_draw_text.restype = None

core.render_display_list.argtypes = [CEngineFramebuffer_p, CDisplayList_p]
core.render_display_list.restype = None

core.sound_synth_init.argtypes = [ctypes.c_int]
core.sound_synth_init.restype = None

core.sound_synth_set_channel.argtypes = [ctypes.c_int, ctypes.c_uint16, ctypes.c_uint8, ctypes.c_uint8]
core.sound_synth_set_channel.restype = None

core.sound_synth_render_int16.argtypes = [Int16_p, ctypes.c_int]
core.sound_synth_render_int16.restype = None

core.sound_synth_stop_all.argtypes = []
core.sound_synth_stop_all.restype = None

# --- Base Wrapper Class ---

class FramebufferBase:
    def __init__(self, width, height, buffer=None):
        self.width = width
        self.height = height
        self.format = "INDEX8"
        if buffer is None:
            self.buffer = bytearray(width * height)
        else:
            self.buffer = buffer
        self._mv = memoryview(self.buffer).cast('B')
        
        self._c_refs = []
        
        self._c_fb = CEngineFramebuffer()
        self._c_fb.width = width
        self._c_fb.height = height
        self._c_fb.format = 2 # kFormatIndex8
        self._c_data = (ctypes.c_uint8 * len(self.buffer)).from_buffer(self.buffer)
        self._c_fb.buffer = ctypes.addressof(self._c_data)
        
        # Use C-side allocation so layout is guaranteed to match
        # We store it as an integer address to bypass Pyodide POINTER bugs
        self._c_dl_addr = core.dl_create()

    def reinit(self, width, height, buffer=None):
        self.width = width
        self.height = height
        if buffer is None:
            self.buffer = bytearray(width * height)
        else:
            self.buffer = buffer
        self._mv = memoryview(self.buffer).cast('B')
        
        self._c_fb.width = width
        self._c_fb.height = height
        self._c_data = (ctypes.c_uint8 * len(self.buffer)).from_buffer(self.buffer)
        self._c_fb.buffer = ctypes.addressof(self._c_data)
        
        core.dl_clear(self._c_dl_addr)
        self._c_refs.clear()

    def _flush(self):
        """Called by HAL implementation to render the display list before blitting to screen"""
        fb_addr = ctypes.addressof(self._c_fb)
        core.render_display_list(fb_addr, self._c_dl_addr)
        core.dl_clear(self._c_dl_addr)
        self._c_refs.clear()

    def clear(self, col=0):
        core.dl_push_clear(self._c_dl_addr, col)

    def fill(self, col):
        core.dl_push_clear(self._c_dl_addr, col)

    def rect(self, x, y, w, h, col, is_filled=True):
        if is_filled:
            core.dl_push_fill_rect(self._c_dl_addr, int(x), int(y), int(w), int(h), col)
        else:
            core.dl_push_line(self._c_dl_addr, int(x), int(y), int(x + w - 1), int(y), col)
            core.dl_push_line(self._c_dl_addr, int(x), int(y + h - 1), int(x + w - 1), int(y + h - 1), col)
            core.dl_push_line(self._c_dl_addr, int(x), int(y), int(x), int(y + h - 1), col)
            core.dl_push_line(self._c_dl_addr, int(x + w - 1), int(y), int(x + w - 1), int(y + h - 1), col)

    def pset(self, x, y, col):
        core.dl_push_pset(self._c_dl_addr, int(x), int(y), col)

    def line(self, x1, y1, x2, y2, col):
        core.dl_push_line(self._c_dl_addr, int(x1), int(y1), int(x2), int(y2), col)

    def blt(self, x, y, img, u, v, w, h, colkey=-1):
        if not hasattr(img, '_c_image'): return
        t = img.tint if hasattr(img, 'tint') and img.tint is not None else -1
        core.dl_push_blt(self._c_dl_addr, int(x), int(y), ctypes.addressof(img._c_image), int(u), int(v), int(w), int(h), colkey, t)

    def sprite(self, cx, cy, spr, rotate=0.0, scale=1.0):
        if not hasattr(spr, '_c_sprite'): return
        t = spr.tint if spr.tint is not None else -1
        core.dl_push_draw_sprite(self._c_dl_addr, int(cx), int(cy), float(scale), float(rotate), ctypes.addressof(spr.image._c_image), spr.u, spr.v, spr.w, spr.h, spr.colkey, t)

    def text(self, font, text, x, y, color=1, scale=1.0):
        if hasattr(font, 'image') and hasattr(font, '_c_lookup'):
            text_bytes = text if type(text) is bytes or type(text) is bytearray else text.encode('utf-8')
            c_text = ctypes.create_string_buffer(text_bytes)
            self._c_refs.append(c_text)
            
            core.dl_push_draw_text(
                self._c_dl_addr, int(x), int(y),
                ctypes.addressof(font.image._c_image),
                font.char_w, font.char_h, font.cols,
                ctypes.addressof(c_text), len(text_bytes),
                ctypes.addressof(font._c_lookup),
                color
            )
