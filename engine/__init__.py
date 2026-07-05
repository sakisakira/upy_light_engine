from .palette import colors_api as colors
from . import framebuffer
from . import sound

def update():
    sound.update()

def run(user_update, user_draw, fps=30):
    def wrapped_update():
        user_update()
        update() # calls sound.update()
        
    framebuffer.run(wrapped_update, user_draw, fps=fps)