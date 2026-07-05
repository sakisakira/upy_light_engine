import struct
import array
import math

class Synth:
    def __init__(self):
        self.sample_rate = 44100
        self.rng_state = 12345
        self.decay_samples = self.sample_rate // 2

    def _next_random(self):
        # Linear Congruential Generator (LCG) using constants from "Numerical Recipes in C"
        # Matching the implementation in sound_engine.c
        self.rng_state = (self.rng_state * 1664525 + 1013904223) & 0xFFFFFFFF
        return self.rng_state

    def render_wav(self, tracks):
        """
        Render a list of tracks to a WAV bytearray.
        tracks: list of track_notes
        track_notes: list of (freq, duration_ms, volume, wave_type)
        """
        # Calculate total duration in samples
        max_duration_ms = 0
        for track in tracks:
            duration = sum(note[1] for note in track)
            if duration > max_duration_ms:
                max_duration_ms = duration
                
        # Add tail for decay of the last note (0.5s = 500ms)
        max_duration_ms += 500
        
        total_samples = int((max_duration_ms / 1000.0) * self.sample_rate)
        
        # Mix buffer initialized to 0
        mix_buf = [0] * total_samples
        
        for ch, track in enumerate(tracks):
            current_sample = 0
            for note in track:
                freq = note[0]
                duration_ms = note[1]
                volume = note[2] if len(note) > 2 else 64
                wave_type = note[3] if len(note) > 3 else 0
                
                note_samples = int((duration_ms / 1000.0) * self.sample_rate)
                
                if freq > 0 and volume > 0:
                    period = self.sample_rate // freq if freq > 0 else 0
                    if period > 0:
                        half_period = period // 2
                        
                        # Generate samples including the decay tail, up to decay_samples 
                        # or until the next note on THIS channel? 
                        # Actually, wait, the decay continues until the NEXT note.
                        # We should just generate note_samples length, BUT the actual decay 
                        # length is decay_samples. If the note is short, the decay stops 
                        # when the NEXT note starts.
                        # So we generate note_samples length.
                        # If it's the LAST note in the track, we can generate up to decay_samples.
                        render_len = note_samples
                        if note == track[-1]:
                            render_len = self.decay_samples
                        
                        phase = 0
                        samples_played = 0
                        
                        for i in range(render_len):
                            idx = current_sample + i
                            if idx >= total_samples:
                                break
                                
                            if samples_played >= self.decay_samples:
                                break
                                
                            decay_factor = 1.0 - (samples_played / self.decay_samples)
                            current_vol = int(volume * decay_factor * 30)
                            
                            pos = phase % period
                            val = 0
                            
                            if wave_type == 0: # Square
                                val = current_vol if pos < half_period else -current_vol
                            elif wave_type == 1: # Sawtooth
                                val = ((pos * current_vol * 2) // period) - current_vol
                            elif wave_type == 2: # Triangle
                                if pos < half_period:
                                    val = ((pos * current_vol * 2) // half_period) - current_vol
                                else:
                                    val = current_vol - (((pos - half_period) * current_vol * 2) // half_period)
                            elif wave_type == 3: # Noise
                                r = self._next_random()
                                mod_val = current_vol * 2
                                if mod_val > 0:
                                    val = (r % mod_val) - current_vol
                                    
                            mix_buf[idx] += val
                            phase += 1
                            samples_played += 1

                current_sample += note_samples

        # Clip and pack
        for i in range(len(mix_buf)):
            v = mix_buf[i]
            if v > 32767: mix_buf[i] = 32767
            elif v < -32768: mix_buf[i] = -32768
            
        out_buf = array.array('h', mix_buf).tobytes()
            
        header = self._build_wav_header(len(out_buf))
        return header + out_buf

    def _build_wav_header(self, data_size):
        channels = 1
        bits_per_sample = 16
        byte_rate = self.sample_rate * channels * (bits_per_sample // 8)
        block_align = channels * (bits_per_sample // 8)
        
        header = b'RIFF'
        header += struct.pack('<I', 36 + data_size)
        header += b'WAVE'
        header += b'fmt '
        header += struct.pack('<I', 16) # Subchunk1Size
        header += struct.pack('<H', 1)  # AudioFormat (PCM)
        header += struct.pack('<H', channels)
        header += struct.pack('<I', self.sample_rate)
        header += struct.pack('<I', byte_rate)
        header += struct.pack('<H', block_align)
        header += struct.pack('<H', bits_per_sample)
        header += b'data'
        header += struct.pack('<I', data_size)
        return header

_synth = Synth()

def render_wav(tracks):
    return _synth.render_wav(tracks)
