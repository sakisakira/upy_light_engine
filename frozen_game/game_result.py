import engine.framebuffer as fb
import engine.input as input
import engine.sound as sound
from engine.image import Image
from engine.font import Font
from world import *
from savedata import *
from color_palette import *
from input import Button
from stages import *

class GameResult:
    SpriteSize = Vec2(32, 64)
    # Native resolution scale
    ImageScale = 2.5

    class CharaStat:
        def __init__(self):
            self.base = 0
            self.tits = 0
            self.head = 0
            self.larm = 0

    def __init__(self, image_path):
        self.image_path = image_path
        self.image = None
        self.base_sprites = None
        self.tits_sprites = None
        self.head_sprites = None
        self.larm_sprites = None
        self.is_loaded = False
        self.max_y = [61, 55]
        
        self.font = Font("fonts/font.afnt")
        self.small_font = Font("fonts/font_5x7.afnt")
        margin = 5
        x = margin
        y = g_world.screen_size.y - Button.ButtonSize[1] - margin
        self.button = Button(x, y, "B")
        self.reset()

    def load(self):
        if self.is_loaded: return
        self.image = Image.load(self.image_path)
        self._set_sprites()
        self.is_loaded = True

    def unload(self):
        if not self.is_loaded: return
        self.base_sprites = None
        self.tits_sprites = None
        self.head_sprites = None
        self.larm_sprites = None
        self.image = None
        Image._cache.pop(self.image_path, None)
        import gc
        gc.collect()
        self.is_loaded = False

    def _set_sprites(self):
        sw = self.SpriteSize.x
        sh = self.SpriteSize.y
        ck = g_world.bg_index
        
        self.base_sprites = [
            self.image.subimage(0, 0, sw, sh, colkey=ck),
            self.image.subimage(0, sh, sw, sh, colkey=ck)
        ]
        self.tits_sprites = [
            self.image.subimage(sw, 0, sw, sh, colkey=ck),
            self.image.subimage(sw, sh, sw, sh, colkey=ck)
        ]
        self.head_sprites = [
            self.image.subimage(sw * 2, 0, sw, sh, colkey=ck),
            self.image.subimage(sw * 2, sh, sw, sh, colkey=ck)
        ]
        self.larm_sprites = [
            self.image.subimage(sw * 3, 0, sw, sh, colkey=ck),
            self.image.subimage(sw * 3, sh, sw, sh, colkey=ck)
        ]

    def reset(self):
        self.tic = 0
        self.chara_base_y = g_world.screen_size.y + self.max_y[0]
        self.chara_stat = self.CharaStat()
        self.text_base_y = g_world.screen_size.y
        self.placed_tic = False
        self.best_total = None

    def fg_color(self):
        return ColorPalette.ResultTextFg

    def bg_color(self):
        return ColorPalette.ResultTextBg

    def update(self):
        self.tic += 1
        self._update_text_position()
        self._update_chara_position()
        if self.text_base_y <= 0 and not self.placed_tic:
            self.placed_tic = self.tic
        if self.best_total == None:
            total = 0
            for stage in g_stages:
                total += stage.last_time
            self._update_best_total(total)

    def _update_best_total(self, total):
        self.best_total = g_savedata.time(Savedata.TagTotal)
        if not self.best_total:
            self.best_total = total
        else:
            self.best_total = min(self.best_total, total)
        g_savedata.set_time(Savedata.TagTotal, self.best_total)
        g_savedata.save()

    def _update_text_position(self):
        if self.text_base_y > 0 and not self.placed_tic:
            self.text_base_y -= g_world.screen_size.y / 15
        if self.placed_tic:
            phase = (self.tic - self.placed_tic) * math.pi / 15
            self.text_base_y = 10 * math.sin(phase)
        
    def _update_chara_position(self):
        if self.chara_base_y > 0 and not self.placed_tic:
            self.chara_base_y -= g_world.screen_size.y / (15 * self.ImageScale)
            self.chara_stat = self.CharaStat()
        if not self.placed_tic: return
        period = 30
        phase = (self.tic - self.placed_tic) % period
        max_h = g_world.screen_size.y - self.SpriteSize.y * self.ImageScale
        h = (1 - ((phase / period * 2 - 1)**2)) * max_h
        if h < 10:
            self.chara_base_y = g_world.screen_size.y - 5
            self.chara_stat.base = 1
            self.chara_stat.tits = 1
            self.chara_stat.larm = 1
        else:
            self.chara_base_y = g_world.screen_size.y - h - 2
            self.chara_stat.base = 0
            if phase % 15 < 7:
                self.chara_stat.tits = 1
            else:
                self.chara_stat.tits = 0
            self.chara_stat.larm = 0
        if phase < period / 2:
            self.chara_stat.head = 1
        else:
            self.chara_stat.head = 0

    def pressed(self):
        import engine.constants as const
        return (input.button(const.Button_B) or
                self.button.pressed())

    def text(self, font, str, x, y):
        fb.screen.text(font, str, x, y - 1, self.bg_color())
        fb.screen.text(font, str, x - 1, y + 1, self.bg_color())
        fb.screen.text(font, str, x + 2, y + 1, self.bg_color())
        fb.screen.text(font, str, x + 1, y + 1, self.bg_color())
        fb.screen.text(font, str, x, y, self.fg_color())

    def show_image(self):
        i_w = self.SpriteSize.x
        i_h = self.SpriteSize.y
        i_s = self.ImageScale
        cx = g_world.screen_size.x - i_w * i_s / 2
        i_h2 = self.max_y[self.chara_stat.base]
        cy = self.chara_base_y + (i_h - i_h2) * i_s - i_h * i_s / 2
        fb.screen.sprite(cx, cy, self.base_sprites[self.chara_stat.base], 0, i_s)
        fb.screen.sprite(cx, cy, self.tits_sprites[self.chara_stat.tits], 0, i_s)
        fb.screen.sprite(cx, cy, self.head_sprites[self.chara_stat.head], 0, i_s)
        fb.screen.sprite(cx, cy, self.larm_sprites[self.chara_stat.larm], 0, i_s)

    def show_text(self):
        x0 = 10
        y0 = 10 + self.text_base_y / 2
        total_time = 0.0
        for index in range(len(g_stages)):
            time = g_stages[index].last_time
            total_time += time
            self.text(self.font,
                      'Stage {}: {:7.2f}'.format(index + 1, time),
                      x0, y0)
            y0 += 17
        y0 += 10
        self.text(self.font,
                  '  Total: {:7.2f}'.format(total_time),
                  x0, y0)
        y0 += 22
        if self.best_total:
            self.text(self.font,
                      'Best Total: {:7.2f}'.format(self.best_total),
                      x0, y0)
        x = g_world.screen_size.x / 16
        y = g_world.screen_size.y - 20
        self.text(self.small_font, "Press B", x, y)


    def show(self):
        fb.screen.fill(ColorPalette.ResultBg)
        self.show_image()
        self.show_text()
        self.button.show()

