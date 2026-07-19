import time
import os
import sys

class SoundHAL:
    def __init__(self):
        self.sample_rate = 44100
        self.play_state = "stopped"
        self.play_start_time = 0
        self.total_duration = 0
        self.process = None
        self.intro_wav_file = None
        self.loop_wav_file = None
        self.sfx_aliases = []

    def _play_wav_os(self, path, loop=False):
        if sys.platform == 'win32':
            import winsound
            flags = winsound.SND_FILENAME | winsound.SND_ASYNC
            if loop:
                flags |= winsound.SND_LOOP
            winsound.PlaySound(path, flags)
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
        self.play_sequence([[(freq, duration_ms, 127)]])

    def play_sfx(self, notes, channel=3):
        if not notes:
            return
            
        # Wrap single track if needed
        if len(notes) > 0 and isinstance(notes[0], tuple):
            notes = [notes]
            
        from engine.hal import sound_synth_cpython
        sfx_wav, _, _, _ = sound_synth_cpython.render_wavs(notes)
        
        if not sfx_wav:
            return
            
        import tempfile
        tmp = tempfile.gettempdir()
        timestamp = int(time.time() * 1000)
        sfx_path = os.path.join(tmp, f"upy_light_sfx_{timestamp}.wav")
        
        with open(sfx_path, "wb") as f:
            f.write(sfx_wav)
            
        if sys.platform == 'win32':
            import ctypes
            alias = f"sfx_{timestamp}"
            cmd_open = f'open "{sfx_path}" type waveaudio alias {alias}'
            ctypes.windll.winmm.mciSendStringW(cmd_open, None, 0, None)
            cmd_play = f'play {alias} from 0'
            ctypes.windll.winmm.mciSendStringW(cmd_play, None, 0, None)
            
            # Store alias to clean up in update()
            duration = sum(n[1] for n in notes[0]) / 1000.0 + 0.5
            self.sfx_aliases.append((alias, time.time(), duration, sfx_path))
        elif sys.platform == 'darwin':
            import subprocess
            subprocess.Popen(["afplay", sfx_path])
        elif sys.platform.startswith('linux'):
            import subprocess
            subprocess.Popen(["aplay", "-q", sfx_path])

    def play_sequence(self, intro_tracks, loop_tracks=None):
        if not intro_tracks and not loop_tracks:
            return
            
        # If it's a flat list of tuples (single track), wrap it
        if intro_tracks and len(intro_tracks) > 0 and isinstance(intro_tracks[0], tuple):
            intro_tracks = [intro_tracks]
        if loop_tracks and len(loop_tracks) > 0 and isinstance(loop_tracks[0], tuple):
            loop_tracks = [loop_tracks]
            
        self.stop()
        
        # Generate the sequence as WAV in memory
        from engine.hal import sound_synth_cpython
        intro_wav, loop_wav, intro_dur, loop_dur = sound_synth_cpython.render_wavs(intro_tracks, loop_tracks)
        
        import tempfile
        tmp = tempfile.gettempdir()
        timestamp = int(time.time() * 1000)
        self.intro_wav_file = os.path.join(tmp, f"upy_light_intro_{timestamp}.wav") if intro_wav else None
        self.loop_wav_file = os.path.join(tmp, f"upy_light_loop_{timestamp}.wav") if loop_wav else None
        
        if intro_wav:
            with open(self.intro_wav_file, "wb") as f:
                f.write(intro_wav)
        if loop_wav:
            with open(self.loop_wav_file, "wb") as f:
                f.write(loop_wav)
                
        self.play_start_time = time.time()
        
        if intro_wav:
            self._play_wav_os(self.intro_wav_file, loop=False)
            self.play_state = "intro"
            self.total_duration = intro_dur / 1000.0
        elif loop_wav:
            self._play_wav_os(self.loop_wav_file, loop=True)
            self.play_state = "loop"
            self.total_duration = loop_dur / 1000.0

    def stop(self):
        if self.play_state != "stopped":
            self._stop_wav_os()
            self.play_state = "stopped"

    def update(self):
        # Cleanup old sfx aliases on win32
        if sys.platform == 'win32' and hasattr(self, 'sfx_aliases'):
            now = time.time()
            alive = []
            import ctypes
            for alias, start_t, dur, path in self.sfx_aliases:
                if now - start_t > dur:
                    ctypes.windll.winmm.mciSendStringW(f'close {alias}', None, 0, None)
                    try:
                        os.remove(path)
                    except:
                        pass
                else:
                    alive.append((alias, start_t, dur, path))
            self.sfx_aliases = alive

        if self.play_state == "intro":
            intro_done = False
            if sys.platform != 'win32':
                if self.process and self.process.poll() is not None:
                    intro_done = True
            else:
                if time.time() - self.play_start_time >= self.total_duration:
                    intro_done = True
                    
            if intro_done:
                if self.loop_wav_file:
                    self._play_wav_os(self.loop_wav_file, loop=True)
                    self.play_state = "loop"
                    self.play_start_time = time.time()
                else:
                    self.play_state = "stopped"
                    
        elif self.play_state == "loop":
            # For non-win32, we must manually restart the loop process if it ends
            if sys.platform != 'win32':
                if self.process and self.process.poll() is not None:
                    self._play_wav_os(self.loop_wav_file, loop=True)
                    self.play_start_time = time.time()
