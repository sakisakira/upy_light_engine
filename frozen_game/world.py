import math
import time
from utilities import *

BikeWorldLen = 1.5 # [m]
# Assets are natively at 1/2 size of original Pyxel version to fit Cardputer.
BikeSpriteWidth = 64 # [pixel]
BikeSpriteHeight = 48 # [pixel]
BikeSpriteScale = 1

class World:
    Version = "0.01"
    # Based on Pyxel version 1.04.

    def __init__(self):
        self.gravity = Vec2(0.0, -9.8)
        self.scale = Vec2(BikeSpriteWidth / BikeWorldLen,
                          -BikeSpriteWidth / BikeWorldLen)
        self.screen_size = Vec2(240, 135)
        self.title = "Bumpy Flippy Bikey"
        self.fps = 30
        self.bg_index = 0
        self.origin_world = Vec2(0.0, 0.0)
        self.origin_screen = Vec2(self.screen_size.x * 0.3,
                                  self.screen_size.y * 0.9)
        self.rival_diff = -15
        self.stage_index = 0

    def start(self):
        self.tic = 0
        self.start_time = 0.0
        self.last_time = self.start_time
        self.elapsed_time = 0.0
        self.delta_time = 0.0

    def update(self, world_origin):
        self.tic += 1
        self.delta_time = 1.0 / self.fps
        self.elapsed_time = self.tic / self.fps
        self.last_time = self.elapsed_time - self.start_time
        self.origin_world = world_origin

    def screen_xy(self, world_xy):
        w_diff = world_xy - self.origin_world
        s_diff = w_diff * self.scale
        return self.origin_screen + s_diff

    def world_xy(self, screen_xy):
        s_diff = screen_xy - self.origin_screen
        w_diff = s_diff / self.scale
        return self.origin_world + w_diff

    def world_x_index(self, world_x):
        return int(round(world_x * self.scale.x))

g_world = World()
