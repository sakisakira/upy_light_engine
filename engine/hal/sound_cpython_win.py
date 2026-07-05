import winsound
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

    def play_tone(self, freq, duration_ms):
        self.play_sequence([(freq, duration_ms, 127)])

    def play_sequence(self, notes):
        if not notes:
            return
            
        # Handle multi-track MML (just play track 0 on PC)
        if isinstance(notes[0], list):
            notes = notes[0]

        self.current_sequence = notes
        self.total_duration = sum(note[1] for note in notes) / 1000.0
        
        # Generate the entire sequence as a single WAV in memory
        audio_data = bytearray()
        for note in notes:
            freq = note[0]
            duration_ms = note[1]
            volume = note[2] if len(note) > 2 else 127
            
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
        temp_wav = os.path.join(os.environ.get('TEMP', 'C:\\temp'), "upy_light_engine_beep.wav")
        with open(temp_wav, "wb") as f:
            f.write(wav_content)
            
        # Play asynchronously from file
        winsound.PlaySound(temp_wav, winsound.SND_FILENAME | winsound.SND_ASYNC)
        self.is_playing = True
        self.play_start_time = time.time()

    def stop(self):
        if self.is_playing:
            winsound.PlaySound(None, winsound.SND_PURGE)
            self.is_playing = False

    def update(self):
        if self.is_playing:
            if time.time() - self.play_start_time > self.total_duration:
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
