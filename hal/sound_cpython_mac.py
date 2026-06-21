import os
import subprocess
import wave
import struct

class SoundHAL:
    def __init__(self):
        self.sample_rate = 44100
        self._counter = 0
        self._processes = []
        
    def _write_notes(self, notes, filename):
        # notes is a list of (freq, duration_ms)
        with wave.open(filename, 'w') as w:
            w.setnchannels(1) # mono
            w.setsampwidth(2) # 16-bit
            w.setframerate(self.sample_rate)
            
            for freq, duration_ms in notes:
                num_samples = int(self.sample_rate * (duration_ms / 1000.0))
                data = bytearray(num_samples * 2)
                
                if freq > 0:
                    period = self.sample_rate / freq
                    for i in range(num_samples):
                        # Simple square wave
                        val = 8000 if (i % period) < (period / 2) else -8000
                        struct.pack_into('<h', data, i * 2, val)
                
                w.writeframesraw(data)

    def play_tone(self, freq, duration_ms):
        self.play_sequence([(freq, duration_ms)])

    def play_sequence(self, notes):
        self._counter = (self._counter + 1) % 16
        filename = f"/tmp/upy_light_engine_snd_{self._counter}.wav"
        
        self._write_notes(notes, filename)
        
        # Cleanup finished processes
        self._processes = [p for p in self._processes if p.poll() is None]
        
        # Spawn afplay asynchronously
        p = subprocess.Popen(['afplay', filename])
        self._processes.append(p)

    def stop(self):
        for p in self._processes:
            if p.poll() is None:
                p.terminate()
        self._processes.clear()
        
    def update(self):
        # On Mac, afplay runs in a separate process asynchronously, 
        # so we don't need to manually advance the sequence here.
        pass
