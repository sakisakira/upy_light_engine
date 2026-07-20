import engine.framebuffer as fb
import engine.input as input
import engine.sound as sound
from engine.image import Image
from engine.font import Font
class bitarray:
    def __init__(self, endian='big'):
        self.data = bytearray()
        self.length = 0

    def append(self, bit):
        if self.length % 8 == 0:
            self.data.append(0)
        if bit:
            self.data[-1] |= (1 << (7 - (self.length % 8)))
        self.length += 1

    def tobytes(self):
        return bytes(self.data)

    def frombytes(self, data):
        self.data = bytearray(data)
        self.length = len(self.data) * 8

    def __len__(self):
        return self.length

    def __getitem__(self, idx):
        if idx >= self.length or idx < 0:
            raise IndexError()
        byte_idx = idx // 8
        bit_idx = 7 - (idx % 8)
        return bool((self.data[byte_idx] >> bit_idx) & 1)
import binascii
from world import *

class PlayRecord:
    def __init__(self, str_a = None, str_b = None):
        if str_a and str_b:
            self.set_str_a(str_a)
            self.set_str_b(str_b)
        else:
            self.reset()

    def reset(self):
        self.record_a = bitarray(endian='big')
        self.record_b = bitarray(endian='big')
        
    def add(self, a_pressed, b_pressed):
        if a_pressed:
            self.record_a.append(1)
        else:
            self.record_a.append(0)
        if b_pressed:
            self.record_b.append(1)
        else:
            self.record_b.append(0)
        tic = g_world.tic
        if len(self.record_a) != tic: raise
        if len(self.record_b) != tic: raise        

    def str_a(self):
        byte_data = self.record_a.tobytes()
        return binascii.b2a_base64(byte_data).decode('utf-8').strip()
    
    def str_b(self):
        byte_data = self.record_b.tobytes()
        return binascii.b2a_base64(byte_data).decode('utf-8').strip()

    def set_str_a(self, text):
        byte_data = binascii.a2b_base64(text.encode('utf-8'))
        self.record_a = bitarray(endian='big')
        self.record_a.frombytes(byte_data)

    def set_str_b(self, text):
        byte_data = binascii.a2b_base64(text.encode('utf-8'))
        self.record_b = bitarray(endian='big')
        self.record_b.frombytes(byte_data)
        
    def recorded_buttons(self, tic):
        if tic >= len(self.record_a):
            return [False, False]
        else:
            return [self.record_a[tic], self.record_b[tic]]
