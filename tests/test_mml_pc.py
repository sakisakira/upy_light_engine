import sys
import os

# Add parent directory to path to import our engine modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import sound
import time

def test_mml_playback():
    print("Playing Super Mario theme intro MML...")
    mml = "T180 O5 E8 E8 R8 E8 R8 C8 E4 G4 R4 O4 G4 R4"
    
    sound.play_mml(mml)
    
    # Simulate game loop
    for _ in range(60 * 3): # 3 seconds at 60fps
        sound.update()
        time.sleep(1/60.0)
        
    print("Finished.")

if __name__ == "__main__":
    test_mml_playback()
