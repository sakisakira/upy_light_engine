import sys
from engine import mml_parser

# Select the appropriate HAL based on the platform
if sys.platform == 'esp32':
    from engine.hal.sound_micropython import SoundHAL
elif sys.platform == 'win32':
    try:
        from engine.hal.sound_cpython_win import SoundHAL
    except ImportError:
        class SoundHAL:
            def play_tone(self, freq, duration_ms): pass
            def play_sequence(self, notes): pass
            def stop(self): pass
            def update(self): pass
elif sys.platform == 'darwin':
    from engine.hal.sound_cpython_mac import SoundHAL
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

def stop():
    """Stop all currently playing sounds."""
    _hal.stop()

def update():
    """Process any necessary background audio tasks. Should be called in the main game loop."""
    _hal.update()
