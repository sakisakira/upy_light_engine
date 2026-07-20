import sys
# Select the appropriate HAL based on the platform
if sys.platform == 'esp32':
    from engine.hal.sound_micropython import SoundHAL
elif sys.platform == 'emscripten':
    from engine.hal.sound_wasm import SoundHAL
elif sys.platform == 'win32' or sys.platform == 'darwin':
    from engine.hal.sound_cpython import SoundHAL
else:
    # Fallback to dummy
    class SoundHAL:
        def play_tone(self, freq, duration_ms): pass
        def play_sequence(self, notes): pass
        def stop(self): pass
        def update(self): pass

_hal = SoundHAL()

def play_tone(freq, duration_ms):
    """Play a single frequency for a given duration in milliseconds."""
    _hal.play_tone(freq, duration_ms)

def play_mml(mml_string):
    """Parse and play an MML (Music Macro Language) string."""
    from engine import mml_parser
    intro_tracks, loop_tracks = mml_parser.parse_mml(mml_string)
    if intro_tracks or loop_tracks:
        _hal.play_sequence(intro_tracks, loop_tracks)

class _UBGMTrack:
    def __init__(self, data, offset, count):
        self.data = data
        self.offset = offset
        self.count = count
        
    def __len__(self):
        return self.count
        
    def __getitem__(self, idx):
        if idx < 0 or idx >= self.count:
            raise IndexError()
        import struct
        return struct.unpack_from('<HHBB', self.data, self.offset + idx * 6)

def load_ubgm(filepath):
    """Load a .ubgm binary file and return (intro_tracks, loop_tracks)."""
    with open(filepath, 'rb') as f:
        data = f.read()
        
    import struct
    magic, version, num_tracks = struct.unpack_from('<4sBB', data, 0)
    if magic != b'UBGM':
        raise ValueError("Invalid UBGM file format")
        
    intro_tracks = []
    loop_tracks = []
    
    for ch in range(num_tracks):
        offset = 16 + ch * 12
        ic, lc, io, lo = struct.unpack_from('<HHII', data, offset)
        
        intro_tracks.append(_UBGMTrack(data, io, ic) if ic > 0 else [])
        loop_tracks.append(_UBGMTrack(data, lo, lc) if lc > 0 else [])
        
    return intro_tracks, loop_tracks

# A preallocated buffer to avoid MemoryError during UBGM loading on memory-constrained devices.
_ubgm_buffer = bytearray(2048) if sys.platform == 'esp32' else None
_active_ubgm = None

def play_ubgm(filepath):
    """Load and play a .ubgm binary file."""
    global _active_ubgm
    if hasattr(_hal, "play_ubgm_data"):
        if _ubgm_buffer is not None:
            import os
            size = os.stat(filepath)[6]
            if size > len(_ubgm_buffer):
                raise MemoryError(f"UBGM file {filepath} too large ({size} > {len(_ubgm_buffer)})")
            with open(filepath, 'rb') as f:
                f.readinto(_ubgm_buffer)
            _hal.play_ubgm_data(memoryview(_ubgm_buffer)[:size])
            _active_ubgm = _ubgm_buffer
        else:
            with open(filepath, 'rb') as f:
                data = f.read()
                _hal.play_ubgm_data(data)
                _active_ubgm = data
    else:
        intro_tracks, loop_tracks = load_ubgm(filepath)
        _hal.play_sequence(intro_tracks, loop_tracks)

def play_loaded_ubgm(intro_tracks, loop_tracks):
    """Play UBGM tracks that were already loaded via load_ubgm()."""
    _hal.play_sequence(intro_tracks, loop_tracks)

def play_sfx(name):
    """Play a predefined sound effect."""
    # Presets: (freq, duration_ms, volume, wave_type)
    # Wave types: 0=Square, 1=Sawtooth, 2=Triangle, 3=Noise
    sfx_presets = {
        "jump": [(400, 50, 100, 0), (600, 100, 100, 0)],
        "coin": [(988, 50, 100, 0), (1318, 150, 100, 0)],
        "hit": [(200, 50, 100, 3), (100, 100, 80, 3)],
        "shoot": [(800, 20, 80, 1), (400, 30, 60, 1), (200, 50, 40, 1)],
    }
    
    if name in sfx_presets:
        if hasattr(_hal, "play_sfx"):
            _hal.play_sfx(sfx_presets[name])
        else:
            _hal.play_sequence(sfx_presets[name])

def stop():
    """Stop all currently playing sounds."""
    _hal.stop()

def update():
    """Process any necessary background audio tasks. Should be called in the main game loop."""
    _hal.update()
