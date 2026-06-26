# sound_wasm.py

class SoundHAL:
    def __init__(self):
        try:
            import js
            from pyodide.ffi import create_proxy
            self.js = js
            self.create_proxy = create_proxy
            self.audio_ctx = None
            self._unlock_proxy = None
        except ImportError:
            self.js = None

    def _init_ctx(self):
        if self.js and not self.audio_ctx:
            # Web Audio API context. Must be created/resumed after a user gesture.
            if hasattr(self.js.window, 'AudioContext'):
                self.audio_ctx = self.js.window.AudioContext.new()
            elif hasattr(self.js.window, 'webkitAudioContext'):
                self.audio_ctx = self.js.window.webkitAudioContext.new()
                
            def unlock(e):
                if self.audio_ctx and self.audio_ctx.state == "suspended":
                    self.audio_ctx.resume()
            
            self._unlock_proxy = self.create_proxy(unlock)
            self.js.window.addEventListener("keydown", self._unlock_proxy)
            self.js.window.addEventListener("mousedown", self._unlock_proxy)
            self.js.window.addEventListener("touchstart", self._unlock_proxy)

    def play_tone(self, freq, duration_ms):
        self._init_ctx()
        if not self.audio_ctx: return
        
        # Resume context if suspended (browser autoplay policy)
        if self.audio_ctx.state == "suspended":
            self.audio_ctx.resume()
            
        t = self.audio_ctx.currentTime
        osc = self.audio_ctx.createOscillator()
        osc.type = "square"
        osc.frequency.setValueAtTime(freq, t)
        
        gain = self.audio_ctx.createGain()
        # envelope: tiny fade out to prevent clicks
        gain.gain.setValueAtTime(0.1, t)
        gain.gain.setTargetAtTime(0, t + (duration_ms / 1000.0) - 0.01, 0.01)
        
        osc.connect(gain)
        gain.connect(self.audio_ctx.destination)
        
        osc.start(t)
        osc.stop(t + duration_ms / 1000.0)

    def play_sequence(self, notes):
        self._init_ctx()
        if not self.audio_ctx: return
        
        if self.audio_ctx.state == "suspended":
            self.audio_ctx.resume()
            
        t = self.audio_ctx.currentTime
        for freq, duration_ms in notes:
            dur_sec = duration_ms / 1000.0
            if freq > 0:
                osc = self.audio_ctx.createOscillator()
                osc.type = "square"
                osc.frequency.setValueAtTime(freq, t)
                
                gain = self.audio_ctx.createGain()
                gain.gain.setValueAtTime(0.1, t)
                # Quick fade out at the end of the note to prevent pop noise
                gain.gain.setTargetAtTime(0, t + dur_sec - 0.01, 0.005)
                
                osc.connect(gain)
                gain.connect(self.audio_ctx.destination)
                
                osc.start(t)
                osc.stop(t + dur_sec)
            
            t += dur_sec

    def stop(self):
        if self.audio_ctx:
            self.audio_ctx.close()
            self.audio_ctx = None

    def update(self):
        # Scheduling is done automatically by Web Audio API
        pass
