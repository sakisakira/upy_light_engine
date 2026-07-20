import engine.framebuffer as fb
import engine.input as input
import engine.sound as sound
from engine.image import Image
from engine.font import Font
import random
from world import *
from color_palette import *
from input import Button
from savedata import *
from stages import *

class Title:
    Margin = 5
    ImageSize = Vec2(32, 64)
    # Native resolution for Cardputer is 1/2 of Pyxel original. Scale down from 6 to 3.
    ImageScale = 3
    
    def __init__(self, chara_path, text_path):
        self.chara_path = chara_path
        self.text_path = text_path
        self.text_sprite = None
        self.chara_sprite_normal = None
        self.chara_sprite_blink = None
        self.is_loaded = False
        
        self.font = Font("fonts/font.afnt")
        self.small_font = Font("fonts/font_5x7.afnt")
        x = g_world.screen_size.x / 3 - Button.ButtonSize[0]
        y = g_world.screen_size.y - self.Margin - Button.ButtonSize[1]
        self.start_button = Button(x, y, "X")
        x = g_world.screen_size.x * 5 / 9
        self.reset_button = Button(x, y, "Y", 13)
        self.a_button = None
        self.b_button = None
        self.reset()

    def load(self):
        if self.is_loaded: return
        chara_img = Image.load(self.chara_path)
        text_img = Image.load(self.text_path)
        # Native Cardputer resolution (1/2 of Pyxel)
        self.text_sprite = text_img.subimage(0, 0, 128, 128, g_world.bg_index)
        self.chara_sprite_normal = chara_img.subimage(0, 0, 32, 64, g_world.bg_index)
        self.chara_sprite_blink = chara_img.subimage(32, 0, 32, 64, g_world.bg_index)
        self.is_loaded = True

    def unload(self):
        if not self.is_loaded: return
        self.text_sprite = None
        self.chara_sprite_normal = None
        self.chara_sprite_blink = None
        Image._cache.pop(self.chara_path, None)
        Image._cache.pop(self.text_path, None)
        import gc
        gc.collect()
        self.is_loaded = False

    def reset(self):
        self.tic = 0
        self.base_y = g_world.screen_size.y
        self.next_blink_tic = 20
        self.show_reset_dialog = False

    def fg_color(self):
        return ColorPalette.TitleTextFg

    def bg_color(self):
        return ColorPalette.TitleTextBg

    def start_pressed(self):
        import engine.constants as const
        if self.show_reset_dialog: return False
        return (input.button(const.Button_X) or
                self.start_button.pressed())

    def reset_pressed(self):
        import engine.constants as const
        if self.show_reset_dialog: return False
        return (input.button(const.Button_Y) or
                self.reset_button.pressed())
    
    def update(self):
        import engine.constants as const
        self.tic += 1
        if self.base_y > 0:
            self.base_y -= g_world.screen_size.y / 15
        if self.base_y < 0:
            self.base_y = 0
        if self.reset_pressed():
            self.show_reset_dialog = True
        if self.show_reset_dialog and self.a_button:
            a_pressed = (input.button(const.Button_A) or
                         self.a_button.pressed())
            b_pressed = (input.button(const.Button_B) or
                         self.b_button.pressed())
            if a_pressed:
                g_savedata.clear()
                g_savedata.save()
                for stage in g_stages:
                    stage.best_time = None
            if a_pressed or b_pressed:
                self.show_reset_dialog = False

    def chara_sprite(self):
        if self.tic % self.next_blink_tic == 0:
            return self.chara_sprite_blink
        elif self.tic % self.next_blink_tic == 1:
            self.next_blink_tic = random.randint(30, 90)
            return self.chara_sprite_blink
        else:
            return self.chara_sprite_normal

    def text(self, font, str, x, y):
        fb.screen.text(font, str, x, y - 1, self.bg_color())
        fb.screen.text(font, str, x - 1, y + 1, self.bg_color())
        fb.screen.text(font, str, x + 2, y + 1, self.bg_color())
        fb.screen.text(font, str, x + 1, y + 1, self.bg_color())
        fb.screen.text(font, str, x, y, self.fg_color())

    def show_text_image(self):
        x = g_world.screen_size.x / 12
        y = g_world.screen_size.y / 24 + self.base_y
        # Native resolution scale
        scale = 2
        cx = x + (self.text_sprite.w * scale) / 2
        cy = y + (self.text_sprite.h * scale) / 2
        fb.screen.sprite(cx, cy, self.text_sprite, 0, scale)

    def show_texts(self):
        x = g_world.screen_size.x / 8
        y = g_world.screen_size.y * 2 / 3 + self.base_y
        self.text(self.small_font, "Version {}".format(g_world.Version), x, y)
        x = g_world.screen_size.x / 3 + self.Margin
        y = g_world.screen_size.y - 20 + self.base_y
        self.text(self.small_font, "Start", x, y)
        x = g_world.screen_size.x * 5 / 9 + Button.ButtonSize[0] + self.Margin
        fb.screen.text(self.small_font, "Reset Best Time", x, y, self.fg_color())

    def show_image(self):
        i_w = self.ImageSize.x
        i_h = self.ImageSize.y
        i_s = self.ImageScale
        cx = g_world.screen_size.x - i_w * i_s / 2
        cy = self.base_y + i_h * i_s / 2 - 5
        spr = self.chara_sprite()
        if spr:
            fb.screen.sprite(cx, cy, spr, 0, i_s)

    def _show_reset_dialog(self):
        margin = self.Margin
        w = g_world.screen_size.x
        h = g_world.screen_size.y
        dw = w * 2 / 3
        dh = h / 2
        dx0 = w / 6
        dy0 = h / 4
        fb.screen.rect(dx0, dy0, dw, dh, 12)
        x = w / 6 + margin * 2
        y = h / 4 + margin
        self.text(self.small_font, "Resetting Best Time. Are you sure?", x, y)
        y = dy0 + dh * 3 / 4
        if not self.a_button:
            self.a_button = Button(dx0 + margin * 2, y, "A")
            self.b_button = Button(dx0 + dw / 2 + margin, y, "B")
        self.a_button.show()
        self.b_button.show()
        y += Button.ButtonSize[1] / 2 - Button.TextSize[1] / 2
        self.text(self.small_font, "Yes", dx0 + Button.ButtonSize[0] + margin * 3, y)
        self.text(self.small_font, "No", dx0 + dw / 2 + Button.ButtonSize[0] + margin * 2, y)

    def show(self):
        fb.screen.fill(ColorPalette.TitleBg)
        self.show_text_image()
        self.show_image()
        self.start_button.show()
        self.reset_button.show()
        self.show_texts()
        if self.show_reset_dialog:
            self._show_reset_dialog()
