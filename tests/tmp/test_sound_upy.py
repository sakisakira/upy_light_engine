import sys
import time

# モジュール検索パスを追加（tests/tmp から上へ）
sys.path.append('../../')

try:
    from hal.sound_micropython import SoundHAL
except ImportError as e:
    print("Error importing SoundHAL:", e)
    sys.exit(1)

def main():
    print("Testing SoundHAL on MicroPython...")
    hal = SoundHAL()
    
    if not hal.is_ready:
        print("SoundHAL failed to initialize.")
        return
        
    print("SoundHAL initialized successfully. Using M5 library:", getattr(hal, 'use_m5', False))
    print("Playing 440Hz A4 for 1 second...")
    
    hal.play_tone(440, 1000)
    
    # メインループを回して音を出し切る
    end_time = time.ticks_add(time.ticks_ms(), 1500)
    while time.ticks_diff(end_time, time.ticks_ms()) > 0:
        hal.update()
        time.sleep_ms(10) # 軽く待機
        
    print("Test finished!")

if __name__ == '__main__':
    main()
