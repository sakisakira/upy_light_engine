import engine.framebuffer as fb
import engine.input as input
import engine.sound as sound
from engine.image import Image
from engine.font import Font
from world import *
from stages import *
from color_palette import ColorPalette

class Status:
    def __init__(self):
        self.x0 = 5
        self.y0 = 5
        self.y_diff = 10
        self.font = Font("fonts/font_5x7.afnt")
        self.time = False
        self.speed = 0.0
        self.distance = 0.0

    def fg_color(self):
        return ColorPalette.StatusFg

    def bg_color(self):
        return ColorPalette.StatusBg

    def update(self, bike, ground):
        self.time = g_world.elapsed_time
        self.speed = bike.velocity.x * 60 * 60 / 1000 # km/h
        self.distance = ground.goal_x() - bike.location.x

    def text(self, str, x, y):
        fb.screen.text(self.font, str, x, y - 1, self.bg_color())
        fb.screen.text(self.font, str, x - 1, y + 1, self.bg_color())
        fb.screen.text(self.font, str, x + 1, y + 1, self.bg_color())
        fb.screen.text(self.font, str, x, y, self.fg_color())

    def show(self):
        x = self.x0
        y = self.y0
        self.text('STAGE: {:}'.format(g_world.stage_index + 1), x, y)
        y += self.y_diff * 1.5
        self.text('    Time: {:>7.2f}'.format(self.time), x, y)
        y += self.y_diff
        self.text('   Speed: {:>7.2f}'.format(self.speed), x, y)
        y += self.y_diff
        self.text('Distance: {:>7.2f}'.format(self.distance), x, y)
        best_time = g_stages[g_world.stage_index].best_time
        if best_time:
            y += self.y_diff * 1.5
            self.text('Best Time: {:7.2f}'.format(best_time), x, y)
