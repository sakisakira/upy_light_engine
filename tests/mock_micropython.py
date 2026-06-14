import sys
import builtins

# Mock framebuf module
class DummyFramebuf:
    RGB565 = "RGB565"
    class FrameBuffer:
        def __init__(self, buffer, width, height, format):
            self.buffer = buffer
            self.width = width
            self.height = height
            self.format = format

        def fill(self, col):
            pass

        def fill_rect(self, x, y, w, h, col):
            pass

        def rect(self, x, y, w, h, col):
            pass

sys.modules['framebuf'] = DummyFramebuf()

# Mock micropython module and decorators
class DummyMicropython:
    @staticmethod
    def viper(func):
        return func

sys.modules['micropython'] = DummyMicropython()

# Mock ptr16 function
def ptr16(buf):
    # In CPython, to simulate Viper ptr16 array access, we can use memoryview
    return memoryview(buf).cast('H')

builtins.ptr16 = ptr16
