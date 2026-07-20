from engine import sound

class Sound:
    def __init__(self, sound_index=0, channel=0):
        self.sound_index = sound_index
        self.channel = channel
        self.is_playing = False

    def register(self, sound):
        pass

    def play(self):
        self.is_playing = True

    def stop(self):
        self.is_playing = False
        if sound._hal and hasattr(sound._hal, 'c_engine'):
            sound._hal.c_engine.set_channel(self.channel, 0, 0, 0)

    def update(self, ratio):
        if not self.is_playing:
            return

        if not ratio:
            if sound._hal and hasattr(sound._hal, 'c_engine'):
                sound._hal.c_engine.set_channel(self.channel, 0, 0, 0)
            return

        ratio = min(max(ratio, 0.0), 0.99)
        # Map ratio to C0-B4 roughly (16.35 Hz to ~500 Hz) to match Pyxel version
        freq = 16.35 * (2 ** (ratio * 5))

        if sound._hal and hasattr(sound._hal, 'c_engine'):
            # wave_type = 0 (Square), volume = 64
            sound._hal.c_engine.set_channel(self.channel, int(freq), 0, 64)
