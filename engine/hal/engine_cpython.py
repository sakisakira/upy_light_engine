import ctypes
import os

dll_path = os.path.join(os.path.dirname(__file__), "..", "..", "build", "core_engine.dll")
dll_path = os.path.abspath(dll_path)

if not os.path.exists(dll_path):
    raise FileNotFoundError(f"DLL not found: {dll_path}. Please run scripts/build_engine_dll.ps1")

core = ctypes.CDLL(dll_path)

# --- C Structs ---

class CEngineImage(ctypes.Structure):
    _fields_ = [
        ("width", ctypes.c_int16),
        ("height", ctypes.c_int16),
        ("format", ctypes.c_uint8),
        ("data", ctypes.POINTER(ctypes.c_uint8))
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
        ("buffer", ctypes.POINTER(ctypes.c_uint8))
    ]

class CDisplayList(ctypes.Structure):
    pass # Opaque structure, managed by dl_create/dl_destroy

# --- C Functions ---

core.dl_create.argtypes = []
core.dl_create.restype = ctypes.POINTER(CDisplayList)

core.dl_destroy.argtypes = [ctypes.POINTER(CDisplayList)]
core.dl_destroy.restype = None

core.dl_init.argtypes = [ctypes.POINTER(CDisplayList)]
core.dl_init.restype = None

core.dl_clear.argtypes = [ctypes.POINTER(CDisplayList)]
core.dl_clear.restype = None

core.dl_push_clear.argtypes = [ctypes.POINTER(CDisplayList), ctypes.c_uint16]
core.dl_push_clear.restype = None

core.dl_push_pset.argtypes = [ctypes.POINTER(CDisplayList), ctypes.c_int16, ctypes.c_int16, ctypes.c_uint16]
core.dl_push_pset.restype = None

core.dl_push_line.argtypes = [ctypes.POINTER(CDisplayList), ctypes.c_int16, ctypes.c_int16, ctypes.c_int16, ctypes.c_int16, ctypes.c_uint16]
core.dl_push_line.restype = None

core.dl_push_fill_rect.argtypes = [ctypes.POINTER(CDisplayList), ctypes.c_int16, ctypes.c_int16, ctypes.c_int16, ctypes.c_int16, ctypes.c_uint16]
core.dl_push_fill_rect.restype = None

core.dl_push_blt.argtypes = [
    ctypes.POINTER(CDisplayList), ctypes.c_int16, ctypes.c_int16,
    ctypes.POINTER(CEngineImage), ctypes.c_int16, ctypes.c_int16, ctypes.c_int16, ctypes.c_int16,
    ctypes.c_uint16, ctypes.c_int
]
core.dl_push_blt.restype = None

core.dl_push_draw_sprite.argtypes = [ctypes.POINTER(CDisplayList), ctypes.c_int16, ctypes.c_int16, ctypes.c_float, ctypes.POINTER(CEngineSprite), ctypes.c_int]
core.dl_push_draw_sprite.restype = None

core.dl_push_draw_text.argtypes = [
    ctypes.POINTER(CDisplayList), ctypes.c_int16, ctypes.c_int16,
    ctypes.POINTER(CEngineImage), ctypes.c_int, ctypes.c_int, ctypes.c_int,
    ctypes.POINTER(ctypes.c_uint8), ctypes.c_int,
    ctypes.POINTER(ctypes.c_int16), ctypes.c_int
]
core.dl_push_draw_text.restype = None

core.render_display_list.argtypes = [ctypes.POINTER(CEngineFramebuffer), ctypes.POINTER(CDisplayList)]
core.render_display_list.restype = None
