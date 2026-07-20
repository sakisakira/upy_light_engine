import time
import tkinter as tk
from PIL import Image as PILImage, ImageTk

from .engine_ctypes import FramebufferBase

class Framebuffer(FramebufferBase):
    def __init__(self, width, height, buffer=None):
        super().__init__(width, height, buffer)



screen = Framebuffer(240, 135)
