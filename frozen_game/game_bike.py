import engine.framebuffer as fb
import engine.input as input
import engine.sound as sound
from engine.image import Image
from engine.font import Font
import random
from game_constants import *
from world import *
from physics import *
from utilities import *

class GameBike:
    def __init__(self,
                 bike_body_path,
                 tire_path,
                 chara_body_path,
                 chara_symbol_path,
                 gray_converter = None):
        self.bike = Bike()
        self.width = BikeSpriteWidth
        self.height = BikeSpriteHeight
        if gray_converter:
            self.y_diff = g_world.rival_diff
        else:
            self.y_diff = 0
        self.next_blink_tic = 20
        self.chara_body_index = CharaBodyIndex.Normal
        self.gray_converter = gray_converter
        
        self.bike_body_path = bike_body_path
        self.tire_path = tire_path
        self.chara_body_path = chara_body_path
        self.chara_symbol_path = chara_symbol_path
        
        self.is_loaded = False
        
        # Calculate these once
        w = BikeSpriteWidth
        h = BikeSpriteHeight
        r = h // 4
        self.front_tire_center = Vec2(w / 2 - r, r)
        self.rear_tire_center = Vec2(-w / 2 + r, r)

    def _load_img(self, path):
        return Image.load(path)

    def load(self):
        if self.is_loaded: return
        print("GameBike.load loading...")
        w = BikeSpriteWidth
        h = BikeSpriteHeight
        r = h // 4
        
        # Load sheets
        bike_body_sheet = self._load_img(self.bike_body_path)
        tire_sheet = self._load_img(self.tire_path)
        chara_body_sheet = self._load_img(self.chara_body_path)
        chara_symbol_sheet = self._load_img(self.chara_symbol_path)
        
        ck = g_world.bg_index
        
        self.bike_body_sprite = bike_body_sheet.subimage(0, 0, w, h, colkey=ck)
        self.tire_sprite = tire_sheet.subimage(0, r * 2, r * 2, r * 2, colkey=ck)
        
        self.chara_body_sprite_0 = chara_body_sheet.subimage(0, 0, w, h, colkey=ck)
        self.chara_body_sprite_1 = chara_body_sheet.subimage(0, h, w, h, colkey=ck)
        self.chara_body_sprite_steer = chara_body_sheet.subimage(0, h * 2, w, h, colkey=ck)
        self.chara_body_sprite_cry = chara_body_sheet.subimage(0, h * 3, w, h, colkey=ck)

        self.chara_symbol_sprite_0 = chara_symbol_sheet.subimage(0, 0, w, h, colkey=ck)
        self.chara_symbol_sprite_1 = chara_symbol_sheet.subimage(0, h, w, h, colkey=ck)
        self.chara_symbol_sprite_steer = chara_symbol_sheet.subimage(0, h * 2, w, h, colkey=ck)
        self.chara_symbol_sprite_cry = chara_symbol_sheet.subimage(0, h * 3, w, h, colkey=ck)
        self.is_loaded = True
        
    def unload(self):
        if not self.is_loaded: return
        self.bike_body_sprite = None
        self.tire_sprite = None
        self.chara_body_sprite_0 = None
        self.chara_body_sprite_1 = None
        self.chara_body_sprite_steer = None
        self.chara_body_sprite_cry = None
        self.chara_symbol_sprite_0 = None
        self.chara_symbol_sprite_1 = None
        self.chara_symbol_sprite_steer = None
        self.chara_symbol_sprite_cry = None
        
        Image._cache.pop(self.bike_body_path, None)
        Image._cache.pop(self.tire_path, None)
        Image._cache.pop(self.chara_body_path, None)
        Image._cache.pop(self.chara_symbol_path, None)
        
        import gc
        gc.collect()
        self.is_loaded = False

    def screen_center_xy(self):
        w_loc = self.bike.location
        return g_world.screen_xy(w_loc)

    def rotation_degree(self):
        rotation = self.bike.rotation
        return -180.0 / math.pi * rotation

    def tire_rotation_degree(self):
        r = BikeWorldLen / 6
        l = math.pi * 2 * r
        ratio = (self.bike.location.x % l) / l
        return 180.0 * ratio

    def chara_body_sprite(self):
        if self.chara_body_index == CharaBodyIndex.Succeeded:
            return self.chara_body_sprite_steer
        if self.chara_body_index == CharaBodyIndex.Failed:
            return self.chara_body_sprite_cry
        if self.bike.rotation_velocity < 0:
            return self.chara_body_sprite_0
        else:
            return self.chara_body_sprite_1

    def chara_symbol_sprite(self):
        if self.chara_body_index == CharaBodyIndex.Succeeded:
            return self.chara_symbol_sprite_steer
        if self.chara_body_index == CharaBodyIndex.Failed:
            return self.chara_symbol_sprite_cry
        if self.bike.rotation_velocity < 0:
            return self.chara_symbol_sprite_0
        else:
            return self.chara_symbol_sprite_1
        
    def show(self):
        scale = BikeSpriteScale
        y_d = self.y_diff
        s_c_xy = self.screen_center_xy()
        rot = self.rotation_degree()
        f_rel = self.front_tire_center.rotate(-self.bike.rotation).mul(scale)
        f_c_xy = s_c_xy + f_rel
        rot_rad = rot * math.pi / 180.0
        tire_rot = self.tire_rotation_degree()
        tire_rot_rad = tire_rot * math.pi / 180.0
        fb.screen.sprite(f_c_xy.x, f_c_xy.y + y_d, self.tire_sprite, tire_rot_rad, scale)
        r_rel = self.rear_tire_center.rotate(-self.bike.rotation).mul(scale)
        r_c_xy = s_c_xy + r_rel
        fb.screen.sprite(r_c_xy.x, r_c_xy.y + y_d, self.tire_sprite, tire_rot_rad, scale)
        fb.screen.sprite(s_c_xy.x, s_c_xy.y + y_d, self.bike_body_sprite, rot_rad, scale)
        
        c_body = self.chara_body_sprite()
        fb.screen.sprite(s_c_xy.x, s_c_xy.y + y_d, c_body, rot_rad, scale)
        
        c_sym = self.chara_symbol_sprite()
        fb.screen.sprite(s_c_xy.x, s_c_xy.y + y_d - 20, c_sym, 0, scale)
        
    def update(self, ground, btn_a, btn_b):
        self.bike.update(ground, btn_a, btn_b)
        self.chara_body_index = CharaBodyIndex.Normal

    def update_chara_body_index(self, index):
        self.chara_body_index = index

    def failed(self):
        return self.bike.failed()

    def face_index(self):
        if abs(math.sin(self.bike.rotation)) > 0.65:
            return FaceIndex.Astonish
        if g_world.tic % self.next_blink_tic == 0:
            return FaceIndex.Blink
        elif g_world.tic % self.next_blink_tic == 1:
            self.next_blink_tic = random.randint(10, 30)
            return FaceIndex.Blink
        else:
            return FaceIndex.Normal
