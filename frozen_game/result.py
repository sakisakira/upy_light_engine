import engine.framebuffer as fb
import engine.input as input
import engine.sound as sound
from engine.image import Image
from engine.font import Font
from world import *
from stages import *

class Result:
    def __init__(self):
        self.center = g_world.screen_size.div(2.0)
        self.w = 5
        self.h = 7
        self.reset()
        self.font = Font("fonts/font_5x7.afnt")
        self.color = 8
        self.bg_color = 7

    def reset(self):
        self.failed = False
        self.result_time = False

    def text(self, str, x, y):
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if dx == 0 and dy == 0: continue
                fb.screen.text(self.font, str, x + dx, y + dy, self.bg_color)
        fb.screen.text(self.font, str, x, y, self.color)
        
    def show_failed(self):
        str = "FAILED"
        w = self.w * len(str)
        h = self.h
        x0 = self.center.x - w / 2
        y0 = self.center.y - h / 2
        self.text(str, x0, y0)
        str = "Press X to Retry"
        w = self.w * len(str)
        x0 = self.center.x - w / 2
        y0 += self.h * 2
        self.text(str, x0, y0)

    def show_goal(self):
        str = "Goal: {:5.2f} sec.".format(self.result_time)
        w = self.w * len(str)
        h = self.h
        x0 = self.center.x - w / 2
        y0 = self.center.y - h / 2
        self.text(str, x0, y0)
        str = "Press X for Next"
        if g_world.stage_index + 1 == len(g_stages):
            str = "Press X for Game Result"
        w = self.w * len(str)
        x0 = self.center.x - w / 2
        y0 += self.h * 2
        self.text(str, x0, y0)

    def show(self):
        if self.failed:
            self.show_failed()
        elif self.result_time:
            self.show_goal()

    def update(self, failed, result_time):
        self.failed = failed
        self.result_time = result_time
