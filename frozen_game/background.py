import engine.framebuffer as fb
import engine.input as input
import engine.sound as sound
from engine.image import Image
from engine.font import Font
import random
from world import *
from stages import *
from color_palette import ColorPalette

class Background:
    def __init__(self):
        stage = g_stages[g_world.stage_index]
        self.time_period = stage.time_period
        random.seed(stage.seed)
        self.origin_world_x = 0.0
        self.gen_stars()
        self.gen_mountains()
        self.gen_clouds()

    def is_day(self):
        return self.time_period == TimePeriod.Day
        
    def bg_color(self):
        if self.is_day():
            return ColorPalette.DaySky
        else:
            return ColorPalette.NightSky

    def mountain_color(self):
        if self.is_day():
            return ColorPalette.DayMountain
        else:
            return ColorPalette.NightMountain

    def cloud_color(self):
        if self.is_day():
            return ColorPalette.DayCloud
        else:
            return ColorPalette.NightCloud

    def gen_stars(self):
        try:
            import array as _array
            self.stars_array = _array.array('f')
        except ImportError:
            self.stars_array = []
        min_y = 0.3
        max_y = 1.0
        count = 40
        for _ in range(count):
            self.stars_array.append(random.uniform(0.0, 1.0))
            self.stars_array.append(random.uniform(min_y, max_y))

    def gen_mountains(self):
        min_y = 0.2
        max_y = 0.9
        max_x_interval = 0.2
        self.mountains_scale = 3.0
        last_x = 0.0
        last_y = 0.5
        flat_list = []
        while last_x < self.mountains_scale:
            y = last_y + (random.random() - 0.5) * max_x_interval
            y = min(max(y, 0.0), 1.0)
            x = last_x + max(random.random() * max_x_interval, 0.01)
            flat_list.append(x)
            flat_list.append(min_y + y * (max_y - min_y))
            last_x = x
        try:
            import array as _array
            flat_array = _array.array('f', flat_list)
        except ImportError:
            flat_array = flat_list
        self.mountains_xys = Vec2Array(flat_array)

    def gen_clouds(self):
        try:
            import array as _array
            self.clouds_array = _array.array('f')
        except ImportError:
            self.clouds_array = []
        min_y = 0.7
        max_y = 1.0
        min_w = 0.3
        max_w = 0.5
        min_h = 0.02
        max_h = 0.04
        count = 5
        self.clouds_scale = 5
        for _ in range(count):
            self.clouds_array.append(random.uniform(0.0, self.clouds_scale)) # x
            self.clouds_array.append(random.uniform(min_y, max_y)) # y
            self.clouds_array.append(random.uniform(min_w, max_w)) # w
            self.clouds_array.append(random.uniform(min_h, max_h)) # h

    def update(self, origin_world_x):
        self.origin_world_x = origin_world_x

    def calc_y(self, x, scale):
        x = x % scale
        i0 = self.mountains_xys.find_index(x)
        xys = self.mountains_xys.array
        num_points = len(xys) // 2
        i1 = (i0 + 1) % num_points
        x0 = xys[i0 * 2] % scale
        y0 = xys[i0 * 2 + 1]
        x1 = xys[i1 * 2] % scale
        y1 = xys[i1 * 2 + 1]
        return y0 + (y1 - y0) * (x - x0) / (x1 - x0)

    def show_stars(self):
        if self.time_period != TimePeriod.Night:
            return
        s_w = g_world.screen_size.x
        s_h = g_world.screen_size.y
        color = ColorPalette.Star
        for i in range(0, len(self.stars_array), 2):
            sx = self.stars_array[i] * s_w
            sy = (1.0 - self.stars_array[i+1]) * s_h
            # Previously worked around with 1x1 rect() due to suspected crash, 
            # but investigation proved pset() is completely safe.
            fb.screen.pset(sx, sy, color)

    def show_mountains(self):
        scale = self.mountains_scale
        s_w = g_world.screen_size.x
        s_h = g_world.screen_size.y
        origin_x = self.origin_world_x * g_world.scale.x / s_w
        step = 8
        color = self.mountain_color()
        for sx in range(0, s_w, step):
            y = self.calc_y(sx / s_w + origin_x / scale,
                            scale)
            sy = (1 - y) * s_h
            h = max(0, s_h - sy)
            if h > 0:
                fb.screen.rect(sx, sy, step, h, color)
        
    def show_clouds(self):
        color = 7
        scale = self.clouds_scale
        s_w = g_world.screen_size.x
        s_h = g_world.screen_size.y
        origin_x = self.origin_world_x * g_world.scale.x / s_w
        speed = 1.0 / 3.0
        for i in range(0, len(self.clouds_array), 4):
            cx = self.clouds_array[i]
            cy = self.clouds_array[i+1]
            cw = self.clouds_array[i+2]
            ch = self.clouds_array[i+3]
            x = cx - origin_x
            while x * speed + cw < 0.0:
                x += scale
            sx = x * speed * s_w
            sy = (1 - cy) * s_h
            sw = cw * s_w
            sh = ch * s_h
            fb.screen.rect(sx, sy, sw, sh, self.cloud_color())

    def show(self):
        fb.screen.fill(self.bg_color())
        self.show_stars()
        self.show_mountains()
        self.show_clouds()
