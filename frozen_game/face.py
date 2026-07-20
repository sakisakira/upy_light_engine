import engine.framebuffer as fb
import engine.input as input
import engine.sound as sound
from engine.image import Image
from engine.font import Font
from game_constants import *
from world import *

class Face:
    Size = Vec2(42, 42)
    # Native resolution scale
    Scale = 2.5
    
    def __init__(self, path):
        self.path = path
        self.image = None
        self.is_loaded = False
        self.reset()

    def load(self):
        if self.is_loaded: return
        self.image = Image.load(self.path)
        self.is_loaded = True

    def unload(self):
        if not self.is_loaded: return
        Image._cache.pop(self.path, None)
        self.image = None
        self.is_loaded = False


    def reset(self):
        self.index = FaceIndex.Empty

    def sprite_location(self):
        if self.index == FaceIndex.Empty:
            return False
        i_w = self.image.width
        h_count = i_w // self.Size.x
        x = int(self.index) % h_count
        y = int(self.index) // h_count
        return Vec2(x, y) * self.Size

    def update(self, index):
        self.index = index

    def show(self):
        cx = g_world.screen_size.x - self.Size.x * self.Scale / 2 + 7
        cy = self.Size.y * self.Scale / 2 + 5
        spr_loc = self.sprite_location()
        if spr_loc:
            spr = self.image.subimage(spr_loc.x, spr_loc.y, self.Size.x, self.Size.y, colkey=g_world.bg_index)
            fb.screen.sprite(cx, cy, spr, 0, self.Scale)
