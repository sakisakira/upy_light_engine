import engine.framebuffer as fb
import engine.input as input
import engine.sound as sound
from engine.image import Image
from engine.font import Font
from world import *

class Button:
    TextSize = [5, 7]
    ButtonSize = [40, 40]

    def __init__(self, x, y, lable, colkey = 14):
        self.x0 = x
        self.y0 = y
        self.label = lable
        self.colkey = colkey
        self.font = Font("fonts/font_5x7.afnt")

    def show(self):
        fb.screen.rect(self.x0, self.y0,
                   self.ButtonSize[0], self.ButtonSize[1],
                   self.colkey)
        xd = (self.ButtonSize[0] - self.TextSize[0]) / 2
        yd = (self.ButtonSize[1] - self.TextSize[1]) / 2
        fb.screen.text(self.font, self.label, self.x0 + xd, self.y0 + yd, 1)
        fb.screen.text(self.font, self.label, self.x0 + xd + 1, self.y0 + yd, 1)

    def pressed(self):
        # TODO: implement properly after engine supports mouse event.
        if not input.button(1):
            return False
        return (self.x0 <= 0 and
                0 <= self.x0 + self.ButtonSize[0] and
                self.y0 <= 0 and
                0 <= self.y0 + self.ButtonSize[1])

class Input:
    ButtonMargin = 10

    def __init__(self):
        
        self.init_buttons()
        self.in_game = True
        self.a_pressed = False
        self.b_pressed = False
        self.x_pressed = False
        self.font = Font("fonts/font_5x7.afnt")

    def init_buttons(self):
        margin = self.ButtonMargin
        x0 = margin
        y0 = g_world.screen_size.y - margin - Button.ButtonSize[1]
        self.button_b = Button(x0, y0, "B")
        x0 = g_world.screen_size.x - margin - Button.ButtonSize[0]
        self.button_a = Button(x0, y0, "A")
        x0 = (g_world.screen_size.x - Button.ButtonSize[0]) / 2 - Button.ButtonSize[0]
        self.button_x = Button(x0, y0, "X")
        
    def update(self, in_game):
        self.in_game = in_game
        self.a_pressed = False
        self.b_pressed = False
        self.x_pressed = False
        import engine.constants as const
        if input.button(const.Button_A):
            self.a_pressed = True
        if input.button(const.Button_B):
            self.b_pressed = True
        if input.button(const.Button_X):
            self.x_pressed = True
        if self.button_a.pressed():
            self.a_pressed = True
        if self.button_b.pressed():
            self.b_pressed = True
        if self.button_x.pressed():
            self.x_pressed = True

    def show(self):
        if self.in_game:
            self.button_a.show()
            self.button_b.show()
            self.button_x.show()
            margin = self.ButtonMargin
            x0 = (g_world.screen_size.x - Button.ButtonSize[0]) / 2 + margin
            y0 = g_world.screen_size.y - margin - (Button.ButtonSize[1] - Button.TextSize[1]) / 2 - Button.TextSize[1]
            fb.screen.text(self.font, "Retry", x0, y0, 1)
        else:
            self.button_x.show()
