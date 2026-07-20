from engine import sound

class Music:
    TitleMusicIndex = 0
    ResultMusicIndex = 1
    DaytimeMusicIndex = 2
    NighttimeMusicIndex = 3
    MountainMusicIndex = 4
    MidnightMusicIndex = 5
    
    _BGM_MAP = {
        TitleMusicIndex: "musics/title.ubgm",
        ResultMusicIndex: "musics/result.ubgm",
        DaytimeMusicIndex: "musics/daytime.ubgm",
        NighttimeMusicIndex: "musics/nighttime.ubgm",
        MountainMusicIndex: "musics/mountain.ubgm",
        MidnightMusicIndex: "musics/midnight.ubgm",
    }
    
    def __init__(self, sound_index=0, *args, **kwargs):
        self.current_index = None

    def play(self, index):
        if index in self._BGM_MAP:
            import gc
            with open('mem.log', 'a') as f:
                f.write(f"[PLAY] Memory before ubgm: free={gc.mem_free()}, alloc={gc.mem_alloc()}\n")
            # UBGM format automatically handles looping via intro/loop tracks
            sound.play_ubgm(self._BGM_MAP[index])
            self.current_index = index

    def stop(self):
        # Stop all channels
        self.current_index = None
        sound.stop()