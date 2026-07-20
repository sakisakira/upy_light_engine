import machine
import utime as time
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
        self.stop_request = False
        self.silence_buf = bytearray(1024)
        
        self.tracks = [None] * 4
        self.track_indices = [0] * 4
        self.track_end_times = [0] * 4
        self.track_state = ["stopped"] * 4
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
        self.play_sequence([[(freq, duration_ms, 64)]])
        
    def play_sfx(self, notes, channel=3):
        if not self.is_ready: return
        if self.mode == "bare_i2s": return # Not supported
        
        if len(notes) > 0 and isinstance(notes[0], tuple):
            if self.mode == "c_module":
                self.c_engine.set_channel_override(channel, True)
            self.tracks[channel] = notes
            self.track_indices[channel] = 0
            self.track_end_times[channel] = time.ticks_ms()
            self.track_state[channel] = "oneshot"
            note = self._fetch_next_note(channel)
            if note:
                self._start_fetched_note(channel, note)
                
    def play_sequence(self, intro_tracks, loop_tracks=None):
        if not self.is_ready: return
        self.stop()
        
        if self.mode == "bare_i2s":
            while self.audio_thread_running:
                time.sleep_ms(10)
                
        # If it's a flat list of tuples (single track), wrap it
        if intro_tracks and len(intro_tracks) > 0 and isinstance(intro_tracks[0], tuple):
            intro_tracks = [intro_tracks]
        if loop_tracks and len(loop_tracks) > 0 and isinstance(loop_tracks[0], tuple):
            loop_tracks = [loop_tracks]
            
        self.intro_tracks = intro_tracks
        self.loop_tracks = loop_tracks
        self.tracks = [None] * 4
        self.track_indices = [0] * 4
        self.track_end_times = [0] * 4
        if not hasattr(self, 'track_state'):
            self.track_state = ["stopped"] * 4
        else:
            for i in range(4): self.track_state[i] = "stopped"
            
        if self.mode == "c_module":
            for i in range(4): self.c_engine.set_channel_override(i, False)
        
        target_tracks = self.intro_tracks if self.intro_tracks and any(t for t in self.intro_tracks) else self.loop_tracks
        state = "intro" if self.intro_tracks and any(t for t in self.intro_tracks) else "loop"
        
        if not target_tracks:
            return
            
        if self.mode == "bare_i2s":
            self.current_sequence = target_tracks[0] if len(target_tracks) > 0 else []
            self.bare_i2s_state = state
            self.current_note_index = 0
            self.stop_request = False
            self.audio_thread_running = True
            _thread.start_new_thread(self._audio_thread, ())
        else:
            notes_to_play = []
            for ch in range(4):
                if ch < len(target_tracks) and target_tracks[ch]:
                    self.tracks[ch] = target_tracks[ch]
                    self.track_indices[ch] = 0
                    self.track_state[ch] = state
                    note = self._fetch_next_note(ch)
                    if note:
                        notes_to_play.append((ch, note))
            
            real_start_time = time.ticks_ms()
            for ch, note in notes_to_play:
                self.track_end_times[ch] = real_start_time
                self._start_fetched_note(ch, note)

    def _audio_thread(self):
        amplitude = 8000
        while not self.stop_request:
            if self.current_note_index >= len(self.current_sequence):
                if self.bare_i2s_state == "intro" and self.loop_tracks and len(self.loop_tracks) > 0 and self.loop_tracks[0]:
                    self.bare_i2s_state = "loop"
                    self.current_sequence = self.loop_tracks[0]
                    self.current_note_index = 0
                elif self.bare_i2s_state == "loop":
                    self.current_note_index = 0
                else:
                    break
                    
            if self.current_note_index >= len(self.current_sequence):
                break
                
            note = self.current_sequence[self.current_note_index]
            freq = note[0]
            duration_ms = note[1]
            
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
                if self.stop_request:
                    break
                self.i2s.write(buf)
            
            self.current_note_index += 1
            
        self.audio_thread_running = False
        if self.i2s:
            self.i2s.write(self.silence_buf)
            
    def _fetch_next_note(self, ch):
        if not self.tracks[ch]:
            return None
            
        idx = self.track_indices[ch]
        if idx >= len(self.tracks[ch]):
            if self.track_state[ch] == "oneshot" and self.mode == "c_module":
                self.c_engine.set_channel_override(ch, False)
            self.tracks[ch] = None
            self.track_state[ch] = "stopped"
            return None
            
        return self.tracks[ch][idx]

    def _start_fetched_note(self, ch, note):
        freq = note[0]
        duration = note[1]
        volume = note[2] if len(note) > 2 else 64
        wave_type = note[3] if len(note) > 3 else 0
        
        self.track_end_times[ch] = time.ticks_add(self.track_end_times[ch], duration)
        
        if self.mode == "c_module":
            self.c_engine.set_channel(ch, freq, wave_type, volume)
        elif self.mode == "m5_speaker" and self.speaker and ch == 0:
            if freq > 0:
                self.speaker.tone(freq, duration)
            
    def play_ubgm_data(self, data):
        if not self.is_ready: return
        self.stop()
        if self.mode == "c_module":
            self.c_engine.play_ubgm(data)
            
    def update(self):
        if self.mode == "bare_i2s": return
        if not self.is_ready: return
        
        now = time.ticks_ms()
        notes_to_play = []
        for ch in range(4):
            if self.tracks[ch]:
                if time.ticks_diff(self.track_end_times[ch], now) <= 0:
                    self.track_indices[ch] += 1
                    note = self._fetch_next_note(ch)
                    if note:
                        notes_to_play.append((ch, note))
                    else:
                        if self.mode == "c_module":
                            self.c_engine.set_channel(ch, 0, 0, 0)
                            
        for ch, note in notes_to_play:
            self._start_fetched_note(ch, note)

    def stop(self):
        self.stop_request = True
        self.tracks = [None] * 4
        if not hasattr(self, 'track_state'):
            self.track_state = ["stopped"] * 4
        else:
            for i in range(4): self.track_state[i] = "stopped"
            
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
