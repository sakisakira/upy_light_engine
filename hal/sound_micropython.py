import machine
import time
import struct
import math

class SoundHAL:
    def __init__(self):
        self.i2s = None
        self.speaker = None
        self.sample_rate = 44100
        self.is_ready = False
        
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
        # 1. Try to use official M5 library (UIFlow2 firmware)
        try:
            import M5
            M5.begin()
            self.speaker = M5.Speaker
            self.speaker.setVolume(128)
            self.use_m5 = True
            self.is_ready = True
            print("SoundHAL: Using official M5.Speaker")
            return
        except ImportError:
            self.use_m5 = False
            print("SoundHAL: M5 module not found, falling back to bare I2S")
            
        # 2. Fallback to direct I2S and ES8311 I2C initialization (Bare MicroPython)
        try:
            # Enable Amplifier (AMP_EN = GPIO 46)
            amp_en = machine.Pin(46, machine.Pin.OUT)
            amp_en.value(1)
            
            # Initialize I2S first so BCLK/WS are running (Cardputer ADV: BCLK=41, WS=43, DOUT=42)
            self.i2s = machine.I2S(
                1,
                sck=machine.Pin(41),
                ws=machine.Pin(43),
                sd=machine.Pin(42),
                mode=machine.I2S.TX,
                bits=16,
                format=machine.I2S.STEREO,
                rate=self.sample_rate,
                ibuf=self.sample_rate * 4
            )
            
            # Initialize I2C for ES8311 (Cardputer ADV: SDA=8, SCL=9)
            i2c = machine.I2C(1, scl=machine.Pin(9), sda=machine.Pin(8), freq=100000)
            
            # Check if ES8311 is present at address 0x18
            devices = i2c.scan()
            if 0x18 in devices:
                # Proper initialization sequence for ES8311
                # Must be done after I2S is running so BCLK is active
                i2c.writeto_mem(0x18, 0x00, b'\x1f') # Reset
                time.sleep(0.02)
                i2c.writeto_mem(0x18, 0x00, b'\x00') # Clear reset
                i2c.writeto_mem(0x18, 0x00, b'\x80') # Power up
                i2c.writeto_mem(0x18, 0x0D, b'\x01') # Vmid power up
                i2c.writeto_mem(0x18, 0x12, b'\x00') # DAC power up
                i2c.writeto_mem(0x18, 0x14, b'\x00') # Unmute DAC / output
                # REG 0x01: bit 7 (0x80) = Use BCLK as MCLK!
                i2c.writeto_mem(0x18, 0x01, b'\xBF') # Clock manager (BCLK as MCLK)
                i2c.writeto_mem(0x18, 0x31, b'\x00') # Set Volume Max
                i2c.writeto_mem(0x18, 0x32, b'\x00') # Set Volume Max
                time.sleep(0.02)
                
            self.is_ready = True
            print("SoundHAL: Bare I2S initialized successfully")
        except Exception as e:
            try:
                import logger
                logger.error(f"Sound init failed: {e}")
            except ImportError:
                print(f"Sound init failed: {e}")

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
            if self.use_m5:
                # Try to mute speaker if possible
                pass
            return
            
        freq, dur = self.current_sequence[self.current_note_index]
        self.current_freq = freq
        self.current_note_end_time = time.ticks_add(time.ticks_ms(), dur)
        
        if self.use_m5:
            if freq > 0:
                self.speaker.tone(int(freq), int(dur))
        else:
            self._fill_buffer(freq)

    def _fill_buffer(self, freq):
        if freq <= 0:
            for i in range(len(self.square_buf)):
                self.square_buf[i] = 0
            self.phase = 0
        else:
            period = self.sample_rate / freq
            for i in range(self.samples_per_frame):
                val = 4000 if (self.phase % period) < (period / 2) else -4000
                struct.pack_into('<hh', self.square_buf, i * 4, int(val), int(val))
                self.phase += 1

    def stop(self):
        self.current_sequence = []
        self.current_note_index = 0
        self.current_freq = 0

    def update(self):
        if not self.is_ready: return
        
        if self.current_note_index < len(self.current_sequence):
            now = time.ticks_ms()
            if time.ticks_diff(now, self.current_note_end_time) >= 0:
                # Note ended, play next note
                self.current_note_index += 1
                self._start_current_note()
                
            # If using bare I2S, feed the audio buffer constantly
            if not self.use_m5 and self.i2s and self.current_freq > 0:
                try:
                    # Write one frame of audio; this will block briefly if DMA buffer is full
                    self.i2s.write(self.square_buf)
                except Exception:
                    pass
