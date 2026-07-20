import engine.framebuffer as fb
import engine.input as input
import engine.sound as sound
from engine.image import Image
from engine.font import Font
import math
import time

class Vec2:
    def __init__(self):
        self.x = False
        self.y = False
    
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, other):
        return Vec2(self.x * other.x, self.y * other.y)

    def __truediv__(self, other):
        return Vec2(self.x / other.x, self.y / other.y)

    def __str__(self):
        return "Vec2(%f,%f)" % (self.x, self.y)

    def mul(self, other):
        return Vec2(self.x * other, self.y * other)
    
    def div(self, other):
        return Vec2(self.x / other, self.y / other)

    def rotate(self, radian):
        sin_a = math.sin(radian)
        cos_a = math.cos(radian)
        x1 = cos_a * self.x - sin_a * self.y
        y1 = sin_a * self.x + cos_a * self.y
        return Vec2(x1, y1)

class Vec2Array:
    def __init__(self, array_f):
        self.array = array_f
        if len(self.array) < 4:
            raise ValueError("Array must have at least 2 points (4 elements)")
        count = (len(self.array) // 2) - 1
        x_len = self.array[-2] - self.array[0]
        self.diff_x_avg = x_len / count
        self.inv_array = self._calc_inv_array()

    # Calculate index s.t.
    #   array[index] <= floor(diff_x / diff_x_avg).
    def _calc_inv_array(self):
        try:
            import array as _array
            inv_array = _array.array('H')
        except ImportError:
            inv_array = []
        for index in range(len(self.array) // 2):
            diff_x = self.array[index * 2] - self.array[0]
            while len(inv_array) <= math.floor(diff_x / self.diff_x_avg):
                inv_array.append(index)
        return inv_array

    def __str__(self):
        return "Vec2Array(len=%d)" % (len(self.array) // 2)

    def find_index(self, x):
        n = len(self.array) // 2
        i = math.floor((x - self.array[0]) / self.diff_x_avg)
        if i < 0: return 0
        if i >= len(self.inv_array): return n - 1
        index = self.inv_array[i]
        while index < n and self.array[index * 2] <= x:
            index += 1
        return index - 1

class Range2:
    def __init__(self):
        self.x = None
        self.y = None
        self.w = None
        self.h = None

    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
