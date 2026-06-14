import unittest
import os
import tests.mock_micropython
from hal import font

class TestFont(unittest.TestCase):
    def test_font_load(self):
        # Create a dummy afnt file
        dummy_path = "dummy.afnt"
        with open(dummy_path, "wb") as f:
            f.write(b"AFNT")
            f.write(bytes([8, 16, 16, 6])) # 8x16 char, 16x6 grid
            pixel_data = bytearray(8 * 16 * 16 * 6 * 2)
            f.write(pixel_data)
            
        try:
            fnt = font.Font(dummy_path)
            self.assertEqual(fnt.char_w, 8)
            self.assertEqual(fnt.char_h, 16)
            self.assertEqual(fnt.cols, 16)
            self.assertEqual(fnt.rows, 6)
            self.assertEqual(fnt.image.width, 128)
            self.assertEqual(fnt.image.height, 96)
            
            # Test text drawing logic
            import hal.framebuffer_cpython
            fb_cpy = hal.framebuffer_cpython.Framebuffer(100, 100)
            # It shouldn't crash
            font.text(fb_cpy, 0, 0, "HELLO WORLD!\nNEWLINE", fnt)
        finally:
            if os.path.exists(dummy_path):
                os.remove(dummy_path)

if __name__ == '__main__':
    unittest.main()
