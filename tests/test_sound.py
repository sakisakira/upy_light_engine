import sys
import os
import time

# Add root directory to sys.path so we can import sound
try:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
except AttributeError:
    # MicroPython fallback
    sys.path.insert(0, '..')
    sys.path.insert(0, '/')

from engine import sound

def main():
    # Cross-platform ticks_ms
    try:
        ticks_ms = time.ticks_ms
        ticks_diff = time.ticks_diff
    except AttributeError:
        ticks_ms = lambda: int(time.time() * 1000)
        ticks_diff = lambda a, b: a - b



    print("Testing single tone: A4 (440Hz) for 500ms...")
    sound.play_tone(440, 500)
    
    # Wait with update loop
    start = ticks_ms()
    while ticks_diff(ticks_ms(), start) < 1000:
        sound.update()
        time.sleep(0.016)
    
    print("Testing MML: Super Mario intro (short)...")
    mml = "T200 O5 E8 E8 R8 E8 R8 C8 E4 G4 R4 < G4 R4"
    sound.play_mml(mml)
    
    # Wait with update loop
    start = ticks_ms()
    while ticks_diff(ticks_ms(), start) < 4000:
        sound.update()
        time.sleep(0.016)
    print("Test complete.")

if __name__ == '__main__':
    main()
