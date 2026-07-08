import struct
import array
import math
import ctypes
from engine.hal import engine_ctypes

class Synth:
    def __init__(self):
        self.sample_rate = 44100
        engine_ctypes.core.sound_synth_init(self.sample_rate)

    def render_wav(self, tracks):
        """
        Render a list of tracks to a WAV bytearray using the C sound engine.
        tracks: list of track_notes
        track_notes: list of (freq, duration_ms, volume, wave_type)
        """
        engine_ctypes.core.sound_synth_stop_all()

        max_duration_ms = 0
        events = []
        for ch, track in enumerate(tracks):
            if ch >= 4: # MAX_CHANNELS in C is 4
                break
            current_time = 0
            for note in track:
                freq = note[0]
                duration_ms = note[1]
                volume = note[2] if len(note) > 2 else 64
                wave_type = note[3] if len(note) > 3 else 0
                
                events.append({
                    "time_ms": current_time,
                    "ch": ch,
                    "freq": freq,
                    "vol": volume,
                    "wave": wave_type
                })
                current_time += duration_ms
            if current_time > max_duration_ms:
                max_duration_ms = current_time

        events.sort(key=lambda x: x["time_ms"])
                
        # Add tail for decay of the last note (0.5s = 500ms)
        max_duration_ms += 500
        
        total_samples = int((max_duration_ms / 1000.0) * self.sample_rate)
        
        # Buffer for interleaved stereo (2 channels, 16-bit)
        out_buf = (ctypes.c_int16 * (total_samples * 2))()
        
        event_idx = 0
        current_time_ms = 0
        current_sample = 0
        
        while current_sample < total_samples:
            # Trigger events that occur at or before current time
            while event_idx < len(events) and events[event_idx]["time_ms"] <= current_time_ms:
                ev = events[event_idx]
                engine_ctypes.core.sound_synth_set_channel(ev["ch"], ev["freq"], ev["wave"], ev["vol"])
                event_idx += 1
            
            if event_idx < len(events):
                next_time_ms = events[event_idx]["time_ms"]
                chunk_samples = int(((next_time_ms - current_time_ms) / 1000.0) * self.sample_rate)
            else:
                next_time_ms = max_duration_ms
                chunk_samples = total_samples - current_sample
                
            if current_sample + chunk_samples > total_samples:
                chunk_samples = total_samples - current_sample
                
            if chunk_samples > 0:
                ptr = ctypes.addressof(out_buf) + (current_sample * 2 * ctypes.sizeof(ctypes.c_int16))
                engine_ctypes.core.sound_synth_render_int16(ptr, chunk_samples)
                current_sample += chunk_samples
            
            if event_idx >= len(events):
                break
                
            current_time_ms = next_time_ms

        data_bytes = bytes(out_buf)
        header = self._build_wav_header(len(data_bytes))
        return header + data_bytes

    def _build_wav_header(self, data_size):
        channels = 2 # Stereo interleaved from C engine
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
