# engine/time.py

try:
    import utime as _time
    _ticks_ms = _time.ticks_ms
    _ticks_diff = _time.ticks_diff
except ImportError:
    import time as _time
    def _ticks_ms():
        return int(_time.time() * 1000)
    def _ticks_diff(ticks1, ticks2):
        return ticks1 - ticks2

class Clock:
    def __init__(self):
        self.frame_count = 0
        
        # System ticks
        self._last_tick = _ticks_ms()
        self._current_tick = self._last_tick
        
        # Game time (pausable)
        self.game_time_ms = 0
        self.delta_time_ms = 0
        self.is_paused = False
        
        # FPS tracking
        self.fps = 0
        self._fps_frame_count = 0
        self._last_fps_tick = self._last_tick
        
    def tick(self):
        """Called by the engine's main loop every frame."""
        self._current_tick = _ticks_ms()
        real_dt = _ticks_diff(self._current_tick, self._last_tick)
        self._last_tick = self._current_tick
        
        if not self.is_paused:
            self.delta_time_ms = real_dt
            self.game_time_ms += real_dt
            self.frame_count += 1
        else:
            self.delta_time_ms = 0
            
        # FPS calculation
        self._fps_frame_count += 1
        if _ticks_diff(self._current_tick, self._last_fps_tick) >= 1000:
            self.fps = self._fps_frame_count
            self._fps_frame_count = 0
            self._last_fps_tick = self._current_tick
            from . import logger
            logger.info(f"FPS: {self.fps}")
            
    def pause(self):
        self.is_paused = True
        
    def resume(self):
        self.is_paused = False
        # Reset last_tick so we don't get a huge delta_time jump when resuming
        self._last_tick = _ticks_ms()

# Global instance
clock = Clock()

# Expose useful functions
def ticks_ms():
    return _ticks_ms()

def ticks_diff(ticks1, ticks2):
    return _ticks_diff(ticks1, ticks2)
