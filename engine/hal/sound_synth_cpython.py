import struct
import array
import math
import ctypes
from engine.hal import engine_ctypes

class Synth:
    def __init__(self):
        self.sample_rate = 44100
        engine_ctypes.core.sound_synth_init(self.sample_rate)

    def _collect_events(self, tracks):
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
        return events, max_duration_ms

    def _render_segment(self, events, duration_ms, add_tail=False):
        if add_tail:
            duration_ms += 500
        
        total_samples = int((duration_ms / 1000.0) * self.sample_rate)
        if total_samples <= 0:
            return b""
            
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
                next_time_ms = duration_ms
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

    def render_wavs(self, intro_tracks, loop_tracks=None):
        """
        Render intro and loop tracks to WAV bytearrays while preserving oscillator phase.
        Returns: (intro_wav_bytes, loop_wav_bytes, intro_duration_ms, loop_duration_ms)
        """
        engine_ctypes.core.sound_synth_stop_all()
        
        has_intro = any(len(t) > 0 for t in intro_tracks) if intro_tracks else False
        has_loop = any(len(t) > 0 for t in loop_tracks) if loop_tracks else False
        
        intro_wav = None
        loop_wav = None
        intro_dur = 0
        loop_dur = 0
        
        if has_intro:
            intro_events, intro_dur = self._collect_events(intro_tracks)
            # Add tail only if there is no loop following it
            intro_wav = self._render_segment(intro_events, intro_dur, add_tail=not has_loop)
            
        if has_loop:
            # Phase and oscillators continue naturally because we didn't stop_all
            loop_events, loop_dur = self._collect_events(loop_tracks)
            loop_wav = self._render_segment(loop_events, loop_dur, add_tail=False)
            
        return intro_wav, loop_wav, intro_dur, loop_dur

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

def render_wavs(intro_tracks, loop_tracks=None):
    return _synth.render_wavs(intro_tracks, loop_tracks)
