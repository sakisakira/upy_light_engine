try:
    import utime
except ImportError:
    import time as utime

class Profiler:
    def __init__(self):
        self.stats = {}
        self.enabled = True
        
    def start(self, name):
        if self.enabled:
            # We use time.ticks_us() on MicroPython, fallback to time.time() on CPython
            if hasattr(utime, 'ticks_us'):
                self.stats[name] = utime.ticks_us()
            else:
                self.stats[name] = utime.time() * 1000000
            
    def end(self, name):
        if self.enabled and name in self.stats:
            if hasattr(utime, 'ticks_diff'):
                duration_us = utime.ticks_diff(utime.ticks_us(), self.stats[name])
            else:
                duration_us = (utime.time() * 1000000) - self.stats[name]
                
            duration_ms = duration_us / 1000.0
            print(f"[PROFILE] {name}: {duration_ms:.2f} ms")

# Global singleton
profiler = Profiler()
