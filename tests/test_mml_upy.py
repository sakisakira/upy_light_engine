import sys
import time
from engine import sound

def play_test(mode_name, force_mode=None):
    if force_mode:
        # Re-initialize HAL to force a specific mode
        from hal.sound_micropython import SoundHAL
        sound._hal = SoundHAL(force_mode=force_mode)
        
    print(f"\n--- Testing Mode: {mode_name} ---")
    print("Current Sound Mode:", sound._hal.mode)
    
    mml = "T180 O5 E8 E8 R8 E8 R8 C8 E4 G4 R4 O4 G4 R4"
    print("Playing MML:", mml)
    
    sound.play_mml(mml)
    
    start_time = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start_time) < 3000:
        sound.update()
        time.sleep_ms(16) # ~60fps
        
    sound.stop()
    print("Playback finished.")
    time.sleep_ms(1000)

def main():
    print("Starting MML Playback Test on Cardputer...")
    
    # 1. Test Default Mode (Native Module expected)
    play_test("Default (Native Module expected)")
    
    time.sleep(3)
    
    # Release hardware resources before switching modes
    if hasattr(sound._hal, 'deinit'):
        sound._hal.deinit()
    
    # 2. Test Forced Pure uPy (Phase B)
    play_test("Forced Pure uPy (Phase B)", force_mode="bare_i2s")

if __name__ == "__main__":
    main()
