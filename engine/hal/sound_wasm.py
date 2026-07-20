import js
import json
from engine.time import ticks_ms, ticks_diff

class SoundHAL:
    def __init__(self):
        self.is_ready = True
        
        self.intro_tracks = None
        self.loop_tracks = None
        
        self.tracks = [None] * 4
        self.track_indices = [0] * 4
        self.track_end_times = [0] * 4
        self.track_state = ["stopped"] * 4
        
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
            self.track_state[channel] = "oneshot"
            self._start_note_for_track(channel)
            
    def play_sequence(self, intro_tracks, loop_tracks=None):
        self.stop()
        
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
        self.track_state = ["stopped"] * 4
        
        now = ticks_ms()
        
        target_tracks = self.intro_tracks if self.intro_tracks and any(t for t in self.intro_tracks) else self.loop_tracks
        state = "intro" if self.intro_tracks and any(t for t in self.intro_tracks) else "loop"
        
        if not target_tracks:
            return
            
        for ch in range(4):
            if ch < len(target_tracks) and target_tracks[ch]:
                self.tracks[ch] = target_tracks[ch]
                self.track_indices[ch] = 0
                self.track_end_times[ch] = now
                self.track_state[ch] = state
                self._start_note_for_track(ch)
                
    def _start_note_for_track(self, ch):
        if not self.tracks[ch]:
            return
            
        idx = self.track_indices[ch]
        if idx >= len(self.tracks[ch]):
            # track finished its current sequence
            if self.track_state[ch] == "intro" and self.loop_tracks and ch < len(self.loop_tracks) and self.loop_tracks[ch]:
                self.track_state[ch] = "loop"
                self.tracks[ch] = self.loop_tracks[ch]
                self.track_indices[ch] = 0
                idx = 0
            elif self.track_state[ch] == "loop":
                self.track_indices[ch] = 0
                idx = 0
            else:
                self._post_message({"type": "set_channel", "ch": ch, "freq": 0, "wave_type": 0, "volume": 0})
                self.tracks[ch] = None
                self.track_state[ch] = "stopped"
                return
                
        note = self.tracks[ch][idx]
        freq = note[0]
        duration = note[1]
        volume = note[2] if len(note) > 2 else 64
        wave_type = note[3] if len(note) > 3 else 0
        
        self.track_end_times[ch] += duration
        
        self._post_message({"type": "set_channel", "ch": ch, "freq": freq, "wave_type": wave_type, "volume": volume})
            
    def play_ubgm_data(self, data):
        if not self.is_ready: return
        self.stop()
        
        # Pass the raw bytearray to WASM AudioWorklet
        # AudioWorklet will receive it and call sound_synth_play_ubgm()
        data_list = list(data)
        self._post_message({"type": "play_ubgm", "data": data_list})
        
    def update(self):
        now = ticks_ms()
        for ch in range(4):
            if self.tracks[ch]:
                if ticks_diff(self.track_end_times[ch], now) <= 0:
                    self.track_indices[ch] += 1
                    self._start_note_for_track(ch)

    def stop(self):
        self.tracks = [None] * 4
        self.track_state = ["stopped"] * 4
        self._post_message({"type": "stop_all"})
        
    def deinit(self):
        self.stop()
