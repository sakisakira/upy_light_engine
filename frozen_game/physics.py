from world import *
import math

try:
    from enum import Enum, auto
except ImportError:
    class Enum:
        pass
    _auto_idx = 0
    def auto():
        global _auto_idx
        _auto_idx += 1
        return _auto_idx

class Wheel(Enum):
    Front = auto()
    Rear = auto()

class Coordinate(Enum):
    World = auto()
    Local = auto()

# -x: forward, +x: backward
# -y: down,  +y: up
class Location(Vec2):
    def __init__(self):
        self.coordinate = False
        self.x = False
        self.y = False

    def __init__(self, coord, x, y):
        self.coordinate = coord
        self.x = x
        self.y = y

    def __str__(self):
        return "Location(%s,%f,%f)" % (self.coordinate, self.x, self.y)

class Bike:
    def __init__(self):
        self.length = BikeWorldLen * BikeSpriteScale
        self.min_height = 0.02
        self.reset()
        self.acceleration = 8.0 # m/s^2
        self.max_speed = 28.0 # m/s
        self.speed_decay = 0.02
        self.reflection = 0.3
        w = self.length
        h = w * BikeSpriteHeight / BikeSpriteWidth
        self.front_wheel_center = Vec2(w * 2 / 6, -h * 3 / 10)
        self.rear_wheel_center = Vec2(-w * 2 / 6, -h * 3 / 10)
        self.wheel_radius = w / 6

    def reset(self):
        self.location = Vec2(0.0, 2.0)
        self.velocity = Vec2(0.0, 0.0)
        self.rotation = 0.0 # radian
        self.rotation_velocity = 0.0
        self.touched = False
        self.last_touched = False
        self.fallen = False
        
    def speed_ratio(self):
        return (self.velocity.x / self.max_speed)

    def to_local(self, location):
        if location.coordinate == Coordinate.Local:
            return location
        if location.coordinate != Coordinate.World:
            raise
        lxy = (location - self.location).rotate(-self.rotation)
        return Location(Coordinate.Local, lxy.x, lxy.y)

    def to_world(self, location):
        if location.coordinate == Coordinate.World:
            return location
        if location.coordinate != Coordinate.Local:
            raise
        rxy = location.rotate(self.rotation)
        wxy = rxy + self.location
        return Location(Coordinate.World, wxy.x, wxy.y)

    def wheel_center(self, wheel):
        if wheel == Wheel.Front:
            wcenter = self.front_wheel_center
        elif wheel == Wheel.Rear:
            wcenter = self.rear_wheel_center
        else:
            raise
        return Location(Coordinate.Local, wcenter.x, wcenter.y)

    def wheel_height(self, wheel, ground):
        wcenter = self.wheel_center(wheel)
        wwcenter = self.to_world(wcenter)
        gh = ground.height(wwcenter.x)
        return (wwcenter.y - self.wheel_radius) - gh
    
    def wheel_is_on_ground(self, wheel, ground):
        return (self.wheel_height(wheel, ground) <= self.min_height)

    def height_from_ground(self, ground):
        h_f = self.wheel_height(Wheel.Front, ground)
        h_r = self.wheel_height(Wheel.Rear, ground)
        return min(h_f, h_r)

    def update_velocity(self, ground, btn_a, btn_b):
        f_h = self.wheel_height(Wheel.Front, ground)
        r_h = self.wheel_height(Wheel.Rear, ground)
        f_touch = (f_h <= self.min_height)
        r_touch = (r_h <= self.min_height)
        if self.last_touched and not (f_touch or r_touch):
            self.last_touched = False
            if f_h < r_h:
                f_touch = True
            else:
                r_touch = True
        dt = g_world.delta_time
        self.touched = (f_touch or r_touch)
        if (f_touch or r_touch):
            self.velocity.y = self.reflection * abs(self.velocity.y)
            theta = math.atan(ground.ramp_rate(self.location.x))
            self.velocity.x += g_world.gravity.y * dt * math.sin(theta) * 0.5
        elif not (f_touch and r_touch):
            self.velocity += g_world.gravity.mul(dt)
        rot_acc = math.pi / 6
        if f_touch and not btn_b:
            self.rotation_velocity += rot_acc * dt
        if r_touch and not btn_a:
            self.rotation_velocity -= rot_acc * dt
        if btn_a and self.velocity.x < self.max_speed and r_touch:
            self.velocity.x += self.acceleration * dt * math.cos(self.rotation)
            self.rotation_velocity += rot_acc *  dt
        if btn_b:
            if f_h > r_h:
                self.rotation_velocity -= rot_acc * dt * 2
            else:
                self.rotation_velocity += rot_acc * dt * 2
            if f_touch or r_touch:
                if self.velocity.x > 0:
                    self.velocity.x -= self.acceleration * dt
                else:
                    self.velocity.x += self.acceleration * dt
        if self.velocity.x > self.speed_decay:
            self.velocity.x -= self.speed_decay
        self.velocity.x = max(-0.5, min(self.max_speed,
                                        self.velocity.x))

    def update(self, ground, btn_a, btn_b):
        self.update_velocity(ground, btn_a, btn_b)
        h = self.height_from_ground(ground)
        self.location += self.velocity.mul(g_world.delta_time)
        self.rotation += self.rotation_velocity * g_world.delta_time
        if h < -1.0:
            self.fallen = True
        elif h < 0.0:
            self.location.y += -h
            self.last_touched = True

    def failed(self):
        return ((self.touched and math.cos(self.rotation) <= 0) or
                self.fallen)
    
class Ground:
    def __init__(self, coords_array):
        self.coords = Vec2Array(coords_array)
        if len(self.coords.array) < 4: raise

    def height(self, x):
        index = self.coords.find_index(x)
        array = self.coords.array
        if (x < array[0]):
            return False
        if index == (len(array) // 2) - 1:
            return array[-1]
        x0 = array[index * 2]
        y0 = array[index * 2 + 1]
        x1 = array[(index + 1) * 2]
        y1 = array[(index + 1) * 2 + 1]
        if not (x0 <= x and x <= x1):
            print('x0:%f x1:%f x:%f' % (x0, x1, x))
            raise
        if x0 == x1: raise
        return y0 + (y1 - y0) / (x1 - x0) * (x - x0)

    def ramp_rate(self, x):
        diff = 0.1 # 10cm
        x0 = x - diff
        x1 = x + diff
        y0 = self.height(x0)
        y1 = self.height(x1)
        return (y1 - y0) / (x1 - x0)

    def goal_x(self):
        return self.coords.array[-2]

    def goal_y(self):
        return self.coords.array[-1]
