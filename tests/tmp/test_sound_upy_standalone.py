import machine
import time
import struct

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
        self.samples_per_frame = self.sample_rate // 60
        self.square_buf = bytearray(self.samples_per_frame * 4)
        self._init_hardware()
        
    def _init_hardware(self):
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
            
        try:
            amp_en = machine.Pin(46, machine.Pin.OUT)
            amp_en.value(1)
            self.i2s = machine.I2S(
                1, sck=machine.Pin(41), ws=machine.Pin(43), sd=machine.Pin(42),
                mode=machine.I2S.TX, bits=16, format=machine.I2S.STEREO,
                rate=self.sample_rate, ibuf=10000
            )
            i2c = machine.I2C(1, scl=machine.Pin(9), sda=machine.Pin(8), freq=100000)
            devices = i2c.scan()
            if 0x18 in devices:
                i2c.writeto_mem(0x18, 0x00, b'\x1f') # Reset
                time.sleep(0.02)
                i2c.writeto_mem(0x18, 0x00, b'\x00') # Clear reset
                i2c.writeto_mem(0x18, 0x00, b'\x80') # Power up
                i2c.writeto_mem(0x18, 0x0D, b'\x01') # Vmid power up
                i2c.writeto_mem(0x18, 0x12, b'\x00') # DAC power up
                i2c.writeto_mem(0x18, 0x14, b'\x00') # Unmute DAC / output
                i2c.writeto_mem(0x18, 0x01, b'\xBF') # Clock manager (BCLK as MCLK)
                i2c.writeto_mem(0x18, 0x31, b'\x00') # Set Volume Max
                i2c.writeto_mem(0x18, 0x32, b'\x00') # Set Volume Max
                time.sleep(0.02)
            self.is_ready = True
            print("SoundHAL: Bare I2S initialized successfully")
        except Exception as e:
            print(f"Sound init failed: {e}")

    def play_tone(self, freq, duration_ms):
        self.current_sequence = [(freq, duration_ms)]
        self.current_note_index = 0
        self._start_current_note()
        
    def _start_current_note(self):
        if self.current_note_index >= len(self.current_sequence):
            self.current_freq = 0
            return
        freq, dur = self.current_sequence[self.current_note_index]
        self.current_freq = freq
        self.current_note_end_time = time.ticks_add(time.ticks_ms(), dur)
        if self.use_m5:
            if freq > 0: self.speaker.tone(int(freq), int(dur))
        else:
            self._fill_buffer(freq)

    def _fill_buffer(self, freq):
        if freq <= 0:
            for i in range(len(self.square_buf)): self.square_buf[i] = 0
            self.phase = 0
        else:
            period = self.sample_rate / freq
            for i in range(self.samples_per_frame):
                val = 4000 if (self.phase % period) < (period / 2) else -4000
                struct.pack_into('<hh', self.square_buf, i * 4, int(val), int(val))
                self.phase += 1

    def update(self):
        if not self.is_ready: return
        if self.current_note_index < len(self.current_sequence):
            now = time.ticks_ms()
            if time.ticks_diff(now, self.current_note_end_time) >= 0:
                self.current_note_index += 1
                self._start_current_note()
            if not self.use_m5 and self.i2s and self.current_freq > 0:
                try: self.i2s.write(self.square_buf)
                except Exception: pass

print("Testing SoundHAL on MicroPython...")
hal = SoundHAL()
if not hal.is_ready:
    print("SoundHAL failed to initialize.")
else:
    print("Playing 440Hz A4 for 1 second...")
    hal.play_tone(440, 1000)
    end_time = time.ticks_add(time.ticks_ms(), 1500)
    while time.ticks_diff(end_time, time.ticks_ms()) > 0:
        hal.update()
        time.sleep_ms(10)
    print("Test finished!")
