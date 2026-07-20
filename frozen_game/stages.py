import math
import random
from world import *
from savedata import *
from physics import *
from music import *

class TimePeriod(Enum):
    Day = auto()
    Night = auto()

class Stage:
    def __init__(self,
                 xy_array,
                 time_period,
                 music,
                 seed,
                 x_diff_max = None,
                 y_diff_max = None):
        self.xy_array = xy_array
        self.x_diff_max = x_diff_max
        self.y_diff_max = y_diff_max
        self.time_period = time_period
        self.music = music
        self.seed = seed
        self.best_time = None
        self.last_time = None
        self._ground = None

    @property
    def ground(self):
        if self._ground is None:
            import gc
            for s in g_stages:
                if s is not self:
                    s._ground = None
            gc.collect()
            
            if self.x_diff_max and self.y_diff_max:
                self._ground = self.gen_ground_random(
                    self.xy_array,
                    self.x_diff_max,
                    self.y_diff_max,
                    self.seed)
            else:
                self._ground = self.gen_ground(self.xy_array)
        return self._ground
        
    def gen_ground(self, xy_array):
        l = len(xy_array)
        if l % 2 != 0: raise
        flat_list = []
        for index in range(l // 2):
            x = xy_array[index * 2 + 0]
            y = xy_array[index * 2 + 1]
            flat_list.append(float(x))
            flat_list.append(float(y))
        try:
            import array as _array
            flat_array = _array.array('f', flat_list)
        except ImportError:
            flat_array = flat_list
        return Ground(flat_array)

    def gen_ground_random(self,
                          xy_array,
                          x_diff_max,
                          y_diff_max,
                          seed):
        base_g = self.gen_ground(xy_array)
        x = float(xy_array[0])
        y = float(xy_array[1])
        random.seed(seed)
        last_base_y = y
        try:
            import array as _array
            flat_array = _array.array('f')
            append = flat_array.append
        except ImportError:
            flat_array = []
            append = flat_array.append

        while x < base_g.goal_x():
            x_diff = random.uniform(0.0, x_diff_max)
            y_diff = random.uniform(-y_diff_max, y_diff_max)
            x += max(x_diff, 0.01) # Ensure x always advances
            base_y = base_g.height(x)
            if base_y is False:
                base_y = last_base_y
            y += (base_y - last_base_y) + y_diff
            append(x)
            append(y)
            last_base_y = base_y
            
        return Ground(flat_array)

    def start(self):
        if self.best_time == None:
            self.best_time = g_savedata.time(g_world.stage_index)

    def update_best_time(self, stage_index, time, play_record):
        self.last_time = time
        updated = (self.best_time == None or time < self.best_time)
        if updated:
            self.best_time = time
            s_i = stage_index
            g_savedata.set_time(s_i, self.best_time)
            g_savedata.set_record_a(s_i, play_record.str_a())
            g_savedata.set_record_b(s_i, play_record.str_b())
            g_savedata.save()

g_stages = []

# stage 1
g_stages.append(Stage([ -3, 0,
                      5, 1,
                      20, 0,
                      100, 1],
                    TimePeriod.Day,
                    Music.DaytimeMusicIndex,
                    0))

# stage 2
g_stages.append(Stage([ -3, 0,
                      10, 1,
                      20, 5,
                      20.1, 0,
                      50, 2,
                      100, 2],
                    TimePeriod.Night,
                    Music.NighttimeMusicIndex,
                    1))

# stage 3
g_stages.append(Stage([-3, 0, 200, 0],
                      TimePeriod.Day,
                      Music.MountainMusicIndex,
                      100,
                      0.2,
                      0.05))

# stage 4
g_stages.append(Stage([ -3, 0,
                        10, 1,
                        20, 5,
                        20.1, -5,
                        27.5, -5,
                        27.6, 2,
                        30, 0,
                        100, 4,
                        101, -2,
                        200, 2],
                      TimePeriod.Night,
                      Music.DaytimeMusicIndex,
                      4))

# stage 5
g_stages.append(Stage([-3, 0,
                       20, 3,
                       25, 0,
                       30, 3,
                       45, 4,
                       46, -5,
                       48, -5,
                       50, 3,
                       60, 0,
                       75, 4,
                       80, 2,
                       85, 3.5,
                       90, 2,
                       90.1, -5,
                       92, -5,
                       93, 2,
                       120, 2,
                       121, 0,
                       122, 2,
                       123, 3,
                       124, 3.5,
                       130, 1,
                       200, 4],
                      TimePeriod.Night,
                      Music.MidnightMusicIndex,
                      5,
                      0.2,
                      0.07))
