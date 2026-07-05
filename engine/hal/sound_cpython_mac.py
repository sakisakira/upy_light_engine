import subprocess
import struct
import math
import time
import os

class SoundHAL:
    def __init__(self):
        self.sample_rate = 44100
        self.amplitude = 8000
        self.current_sequence = []
        self.is_playing = False
        self.play_start_time = 0
        self.total_duration = 0
        self.process = None
        self.temp_wav = "/tmp/upy_light_engine_beep.wav"

    def play_tone(self, freq, duration_ms):
        self.play_sequence([(freq, duration_ms)])

    def play_sequence(self, notes):
        if not notes:
            return

        # Handle multi-track MML (just play track 0 on PC)
        if isinstance(notes[0], list):
            notes = notes[0]

        self.stop()
        
        self.current_sequence = notes
        self.total_duration = sum(duration for freq, duration in notes) / 1000.0
        
        # Generate the entire sequence as a single WAV file
        audio_data = bytearray()
        for freq, duration_ms in notes:
            num_samples = int(self.sample_rate * (duration_ms / 1000.0))
            if freq == 0:
                # Rest
                audio_data.extend(b'\x00\x00' * num_samples)
            else:
                # Square wave
                period = self.sample_rate / freq
                half_period = period / 2
                for i in range(num_samples):
                    if (i % period) < half_period:
                        val = self.amplitude
                    else:
                        val = -self.amplitude
                    audio_data += struct.pack("<h", val)
                    
        # Construct WAV header
        header = self._build_wav_header(len(audio_data))
        wav_content = header + audio_data
        
        # Save to temp file
        with open(self.temp_wav, "wb") as f:
            f.write(wav_content)
            
        # Play asynchronously using afplay
        try:
            self.process = subprocess.Popen(["afplay", self.temp_wav])
            self.is_playing = True
            self.play_start_time = time.time()
        except FileNotFoundError:
            print("SoundHAL: afplay command not found. Audio playback is disabled.")

    def stop(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.process.wait()
        self.is_playing = False

    def update(self):
        if self.is_playing:
            if self.process and self.process.poll() is not None:
                self.is_playing = False
                self.current_sequence = []

    def _build_wav_header(self, data_size):
        # 1 channel, 16-bit
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
