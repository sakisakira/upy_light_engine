import js
import json
from engine.time import ticks_ms, ticks_diff

class SoundHAL:
    def __init__(self):
        self.is_ready = True
        
        self.tracks = [None] * 4
        self.track_indices = [0] * 4
        self.track_end_times = [0] * 4
        
    def _post_message(self, msg):
        if hasattr(js.window, "soundWorkletNode") and js.window.soundWorkletNode:
            js_msg = js.JSON.parse(json.dumps(msg))
            js.window.soundWorkletNode.port.postMessage(js_msg)

    def play_tone(self, freq, duration_ms):
        self.play_sequence([[(freq, duration_ms, 64)]])
        
    def play_sfx(self, notes, channel=3):
        if len(notes) > 0 and isinstance(notes[0], tuple):
            self.tracks[channel] = notes
            self.track_indices[channel] = 0
            self.track_end_times[channel] = ticks_ms()
            self._start_note_for_track(channel)
            
    def play_sequence(self, tracks):
        self.stop()
        
        # If it's a flat list of tuples (single track), wrap it
        if len(tracks) > 0 and isinstance(tracks[0], tuple):
            tracks = [tracks]
            
        self.tracks = [None] * 4
        self.track_indices = [0] * 4
        self.track_end_times = [0] * 4
        
        now = ticks_ms()
        for ch in range(4):
            if ch < len(tracks):
                self.tracks[ch] = tracks[ch]
                self.track_indices[ch] = 0
                self.track_end_times[ch] = now
                self._start_note_for_track(ch)
                
    def _start_note_for_track(self, ch):
        if not self.tracks[ch]:
            return
            
        idx = self.track_indices[ch]
        if idx >= len(self.tracks[ch]):
            self._post_message({"type": "set_channel", "ch": ch, "freq": 0, "wave_type": 0, "volume": 0})
            self.tracks[ch] = None
            return
            
        note = self.tracks[ch][idx]
        freq = note[0]
        duration = note[1]
        volume = note[2] if len(note) > 2 else 64
        wave_type = note[3] if len(note) > 3 else 0
        
        self.track_end_times[ch] = ticks_ms() + duration
        
        self._post_message({"type": "set_channel", "ch": ch, "freq": freq, "wave_type": wave_type, "volume": volume})
            
    def update(self):
        now = ticks_ms()
        for ch in range(4):
            if self.tracks[ch]:
                if ticks_diff(self.track_end_times[ch], now) <= 0:
                    self.track_indices[ch] += 1
                    self._start_note_for_track(ch)

    def stop(self):
        self.tracks = [None] * 4
        self._post_message({"type": "stop_all"})
        
    def deinit(self):
        self.stop()
