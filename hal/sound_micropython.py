import machine
import time
import struct
import math
import _thread

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
        self.current_note_index = 0
        self.audio_thread_running = False
        self.silence_buf = bytearray(1024)
        
        # Keep old variables for M5 compatibility
        self.current_note_end_time = 0
        self.current_freq = 0
        
        self._init_hardware()
        
    def _init_hardware(self):
        # 1. Try to use custom C module (_sound_engine)
        if self.force_mode != "bare_i2s":
            try:
                import _sound_engine
                self.c_engine = _sound_engine
                self.c_engine.init()
                self.mode = "c_module"
                self.is_ready = True
                print("SoundHAL: Using custom C module Synthesizer (_sound_engine)")
                return
            except ImportError:
                print("SoundHAL: _sound_engine module not found.")
            except Exception as e:
                print(f"SoundHAL: C module init failed: {e}")
        else:
            print("SoundHAL: Skipping C module check due to force_mode='bare_i2s'")
            
        # 2. Try to use bare MicroPython I2S fallback
        try:
            print("SoundHAL: falling back to bare I2S...")
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
        self.stop()
        
        # Wait for previous thread to finish if necessary
        if self.mode in ("bare_i2s", "c_module"):
            while self.audio_thread_running:
                time.sleep_ms(10)
                
        self.current_sequence = notes
        self.current_note_index = 0
        
        if self.mode in ("bare_i2s", "c_module"):
            self.audio_thread_running = True
            _thread.start_new_thread(self._audio_thread, ())
        else:
            self._start_current_note()
            
    def _audio_thread(self):
        amplitude = 8000
        while self.audio_thread_running and self.current_note_index < len(self.current_sequence):
            note = self.current_sequence[self.current_note_index]
            freq = note[0]
            duration_ms = note[1]
            
            if self.mode == "c_module":
                if freq == 0:
                    self.c_engine.set_channel(0, 0, 0, 0)
                else:
                    self.c_engine.set_channel(0, freq, 0, 255) # ch=0, wave=0, vol=255
                # Python Sequencer: just sleep for the duration!
                time.sleep_ms(duration_ms)
            else:
                # bare_i2s logic
                if freq == 0:
                    buf = self.silence_buf
                    samples_per_buf = len(buf) // 4
                    total_samples = int(self.sample_rate * (duration_ms / 1000.0))
                    num_writes = total_samples // samples_per_buf
                    if num_writes == 0: num_writes = 1
                else:
                    period = self.sample_rate // freq
                    half_period = period // 2
                    buf = bytearray(period * 4)
                    for i in range(period):
                        val = amplitude if i < half_period else -amplitude
                        buf[i*4] = val & 0xFF
                        buf[i*4+1] = (val >> 8) & 0xFF
                        buf[i*4+2] = val & 0xFF
                        buf[i*4+3] = (val >> 8) & 0xFF
                        
                    total_samples = int(self.sample_rate * (duration_ms / 1000.0))
                    num_writes = total_samples // period
                    if num_writes == 0: num_writes = 1
                    
                for _ in range(num_writes):
                    if not self.audio_thread_running:
                        break
                    self.i2s.write(buf)
                
            self.current_note_index += 1
            
        self.audio_thread_running = False
        if self.mode == "c_module":
            self.c_engine.stop_all()
        elif self.i2s:
            self.i2s.write(self.silence_buf)
            
    def _start_current_note(self):
        # Used only for m5_speaker
        if self.current_note_index >= len(self.current_sequence):
            self.current_freq = 0
            return
            
        note = self.current_sequence[self.current_note_index]
        self.current_freq = note[0]
        duration = note[1]
        
        self.current_note_end_time = time.ticks_add(time.ticks_ms(), duration)
        
        if self.mode == "m5_speaker" and self.speaker:
            self.speaker.tone(self.current_freq, duration)
            
    def update(self):
        # In bare_i2s/c_module mode, the background thread handles everything!
        if self.mode in ("bare_i2s", "c_module"):
            return
            
        if not self.is_ready or not self.current_sequence: return
        
        now = time.ticks_ms()
        if self.current_freq > 0 and time.ticks_diff(self.current_note_end_time, now) <= 0:
            self.current_note_index += 1
            self._start_current_note()

    def stop(self):
        self.audio_thread_running = False
        self.current_sequence = []
        self.current_freq = 0
        if self.mode == "c_module":
            self.c_engine.stop_all()
        elif self.mode == "bare_i2s" and self.i2s:
            pass
            
    def deinit(self):
        self.stop()
        if self.mode == "c_module" and self.c_engine:
            if hasattr(self.c_engine, "deinit"):
                self.c_engine.deinit()
        elif self.mode == "bare_i2s" and self.i2s:
            self.i2s.deinit()
