import time
import os
import sys

class SoundHAL:
    def __init__(self):
        self.sample_rate = 44100
        self.amplitude = 8000
        self.current_sequence = []
        self.is_playing = False
        self.play_start_time = 0
        self.total_duration = 0
        self.process = None
        
        if sys.platform == 'win32':
            import tempfile
            self.temp_wav = os.path.join(tempfile.gettempdir(), "upy_light_engine_beep.wav")
        else:
            self.temp_wav = "/tmp/upy_light_engine_beep.wav"

    def _play_wav_os(self, path):
        if sys.platform == 'win32':
            import winsound
            winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        elif sys.platform == 'darwin':
            import subprocess
            self.process = subprocess.Popen(["afplay", path])
        elif sys.platform.startswith('linux'):
            import subprocess
            self.process = subprocess.Popen(["aplay", "-q", path])

    def _stop_wav_os(self):
        if sys.platform == 'win32':
            import winsound
            winsound.PlaySound(None, winsound.SND_PURGE)
        else:
            if self.process:
                self.process.kill()
                self.process.wait()
                self.process = None

    def play_tone(self, freq, duration_ms):
        self.play_sequence([(freq, duration_ms, 127)])

    def play_sequence(self, notes):
        if not notes:
            return
            
        # Calculate total duration across all tracks
        max_duration = 0
        if isinstance(notes[0], list):
            for track in notes:
                dur = sum(note[1] for note in track)
                if dur > max_duration: max_duration = dur
        else:
            notes = [notes]
            max_duration = sum(note[1] for note in notes[0])
            
        self.stop()
            
        self.current_sequence = notes
        self.total_duration = max_duration / 1000.0 + 0.5 # Add decay tail
        
        # Generate the entire sequence as a single WAV in memory
        from engine.hal import sound_synth
        wav_content = sound_synth.render_wav(notes)
        
        # Windows locks the file while playing asynchronously.
        # To avoid PermissionError, we generate a unique filename each time.
        if sys.platform == 'win32':
            import tempfile
            self.temp_wav = os.path.join(tempfile.gettempdir(), f"upy_light_engine_beep_{int(time.time()*1000)}.wav")
            
        # Save to temp file
        with open(self.temp_wav, "wb") as f:
            f.write(wav_content)
            
        # OS-specific playback
        self._play_wav_os(self.temp_wav)
            
        self.is_playing = True
        self.play_start_time = time.time()

    def stop(self):
        if self.is_playing:
            self._stop_wav_os()
            self.is_playing = False

    def update(self):
        if self.is_playing:
            if sys.platform != 'win32':
                if self.process and self.process.poll() is not None:
                    self.is_playing = False
                    self.current_sequence = []
            else:
                if time.time() - self.play_start_time > self.total_duration:
                    self.is_playing = False
                    self.current_sequence = []
