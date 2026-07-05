try:
    import utime
except ImportError:
    import time as utime

class Profiler:
    def __init__(self):
        self.stats = {}
        self.history = {}
        self.history_idx = {}
        self.enabled = False
        self.frame_count = 0
        
    def start(self, name):
        if self.enabled:
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
            
            if name not in self.history:
                self.history[name] = [0.0] * 60
                self.history_idx[name] = 0
                
            idx = self.history_idx[name]
            self.history[name][idx] = duration_ms
            self.history_idx[name] = (idx + 1) % 60
            
            if name == "sync": # Assume sync is the last one called in a frame
                self.frame_count += 1
                if self.frame_count >= 60:
                    out = ["[PROFILE] "]
                    for k, v in self.history.items():
                        avg = sum(v) / 60.0
                        out.append(f"{k}: {avg:.2f}ms ")
                    print("".join(out))
                    self.frame_count = 0

# Global singleton
profiler = Profiler()
