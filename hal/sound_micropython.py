import machine
import time
import struct
import math

class SoundHAL:
    def __init__(self, force_mode=None):
        self.i2s = None
        self.speaker = None
        self.c_engine = None
        self.sample_rate = 44100
        self.is_ready = False
        self.mode = "none"
        self.force_mode = force_mode
        
        self.current_sequence = []
        self.current_note_end_time = 0
        self.current_note_index = 0
        self.current_freq = 0
        self.phase = 0
        
        # Buffer for 1 frame of audio at 60 FPS (~16.6ms)
        self.samples_per_frame = self.sample_rate // 60
        self.square_buf = bytearray(self.samples_per_frame * 4) # 16-bit stereo
        
        self._init_hardware()
        
    def _init_hardware(self):
        # 1. Try to use custom C module (_sound_engine)
        if self.force_mode != "bare_i2s":
            try:
                import _sound_engine
                self.c_engine = _sound_engine
                self.mode = "c_module"
                self.is_ready = True
                print("SoundHAL: Using custom C module (_sound_engine)")
                return
            except ImportError:
                pass
        else:
            print("SoundHAL: Skipping C module check due to force_mode='bare_i2s'")
            
        # 2. Try to use bare MicroPython I2S fallback
        try:
            print("SoundHAL: C module not found, falling back to bare I2S...")
            self.i2s = machine.I2S(
                1,
                sck=machine.Pin(41),
                ws=machine.Pin(43),
                sd=machine.Pin(42),
                mode=machine.I2S.TX,
                bits=16,
                format=machine.I2S.STEREO,
                rate=self.sample_rate,
                ibuf=8192
            )
            
            i2c = machine.I2C(1, scl=machine.Pin(9), sda=machine.Pin(8), freq=100000)
            if 0x18 in i2c.scan():
                print("SoundHAL: Initializing ES8311...")
                def write_reg(reg, val):
                    i2c.writeto_mem(0x18, reg, bytes([val]))
                # ES8311 Init array from M5Unified
                write_reg(0x00, 0x80)  # RESET/ CSM POWER ON
                write_reg(0x01, 0xB5)  # CLOCK_MANAGER/ MCLK=BCLK
                write_reg(0x02, 0x18)  # CLOCK_MANAGER/ MULT_PRE=3
                write_reg(0x0D, 0x01)  # SYSTEM/ Power up analog circuitry
                write_reg(0x12, 0x00)  # SYSTEM/ power-up DAC
                write_reg(0x13, 0x10)  # SYSTEM/ Enable output to HP drive
                write_reg(0x32, 0xBF)  # DAC volume
                write_reg(0x37, 0x08)  # Bypass DAC equalizer
                
            self.mode = "bare_i2s"
            self.is_ready = True
            print("SoundHAL: Bare I2S ready")
            return
        except Exception as e:
            print(f"SoundHAL: Bare I2S failed: {e}")
            
        # 3. Try official M5.Speaker as last resort
        try:
            import M5
            M5.begin()
            self.speaker = M5.Speaker
            self.speaker.setVolume(128)
            self.mode = "m5_speaker"
            self.is_ready = True
            print("SoundHAL: Using official M5.Speaker")
            return
        except ImportError:
            print("SoundHAL: All sound initializations failed.")

    def play_tone(self, freq, duration_ms):
        self.play_sequence([(freq, duration_ms)])
        
    def play_sequence(self, notes):
        if not self.is_ready: return
        self.current_sequence = notes
        self.current_note_index = 0
        self._start_current_note()
        
    def _start_current_note(self):
        if self.current_note_index >= len(self.current_sequence):
            self.current_freq = 0
            # Optional: fade out / send silence to prevent pop
            if self.mode == "bare_i2s" and self.i2s:
                self.i2s.write(bytearray(1024))
            return
            
        note = self.current_sequence[self.current_note_index]
        self.current_freq = note[0]
        duration = note[1]
        
        self.current_note_end_time = time.ticks_add(time.ticks_ms(), duration)
        
        if self.mode == "c_module" and self.c_engine:
            # We will implement real async sequence playing in C module later,
            # for now, if there's a play_tone function, we use it.
            if hasattr(self.c_engine, 'play_tone'):
                self.c_engine.play_tone(self.current_freq, duration)
        elif self.mode == "m5_speaker" and self.speaker:
            self.speaker.tone(self.current_freq, duration)
            
    def update(self):
        if not self.is_ready or not self.current_sequence: return
        
        now = time.ticks_ms()
        if self.current_freq > 0 and time.ticks_diff(self.current_note_end_time, now) <= 0:
            self.current_note_index += 1
            self._start_current_note()
            
        if self.mode == "bare_i2s" and self.current_freq > 0:
            self._fill_and_play_i2s()
            
    def _fill_and_play_i2s(self):
        # Generate 1 frame of square wave
        if self.current_freq == 0:
            return
            
        period = self.sample_rate // self.current_freq
        half_period = period // 2
        amplitude = 8000
        
        # Simple square wave generation in Python (slow, but works for basic beeps)
        # To make it faster, we could pre-calculate the buffer or use memoryview
        for i in range(self.samples_per_frame):
            if (self.phase % period) < half_period:
                val = amplitude
            else:
                val = -amplitude
                
            # Pack as 16-bit little endian, stereo
            self.square_buf[i*4] = val & 0xFF
            self.square_buf[i*4+1] = (val >> 8) & 0xFF
            self.square_buf[i*4+2] = val & 0xFF
            self.square_buf[i*4+3] = (val >> 8) & 0xFF
            self.phase += 1
            
        self.i2s.write(self.square_buf)
