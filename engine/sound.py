import sys
from engine import mml_parser

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
    notes = mml_parser.parse_mml(mml_string)
    if notes:
        _hal.play_sequence(notes)

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
