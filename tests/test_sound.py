import sys
import os
import time

# Add root directory to sys.path so we can import sound
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sound

def main():
    print("Testing single tone: A4 (440Hz) for 500ms...")
    sound.play_tone(440, 500)
    
    # Wait to let async process finish
    time.sleep(1)
    
    print("Testing MML: Super Mario intro (short)...")
    mml = "T200 O5 E8 E8 R8 E8 R8 C8 E4 G4 R4 < G4 R4"
    sound.play_mml(mml)
    
    # Wait a bit
    time.sleep(4)
    print("Test complete.")

if __name__ == '__main__':
    main()
