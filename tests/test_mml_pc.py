import sys
import os

# Add parent directory to path to import our engine modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import sound
import time

def test_mml_playback():
    print("Playing Super Mario theme intro MML...")
    mml = "T180 O5 C8 E8 G8 O6 C4 O5 G8 E8 C2"
    
    sound.play_mml(mml)
    
    # Simulate game loop
    for _ in range(60 * 3): # 3 seconds at 60fps
        sound.update()
        time.sleep(1/60.0)
        
    print("Finished.")

if __name__ == "__main__":
    test_mml_playback()
