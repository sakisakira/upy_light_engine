import unittest
import sys

# Inject micropython mocks before importing HAL
import tests.mock_micropython

# Now we can import the modules safely
from hal import framebuffer
from hal import framebuffer_cpython
from hal import framebuffer_micropython

class TestFramebuffer(unittest.TestCase):
    def test_color_conversion(self):
        # Color: R=255, G=0, B=0, A=255
        c = framebuffer.color(255, 0, 0, 255)
        # Expected ARGB4444: 0xF (A) << 12 | 0xF (R) << 8 | 0x0 (G) << 4 | 0x0 (B)
        self.assertEqual(c, 0xFF00)
        
    def test_cpython_fill(self):
        fb_cpy = framebuffer_cpython.Framebuffer(10, 10)
        fb_cpy.fill(0xFFFF)
        self.assertTrue(all(val != 0 for val in fb_cpy._mv))

    def test_cpython_pset_line(self):
        fb_cpy = framebuffer_cpython.Framebuffer(10, 10)
        # test pset
        fb_cpy.pset(5, 5, 0xFFFF)
        # 5*10 + 5 = 55
        self.assertNotEqual(fb_cpy._mv[55], 0)
        
        # test line (horizontal)
        fb_cpy.line(0, 0, 9, 0, 0xFFFF)
        self.assertNotEqual(fb_cpy._mv[0], 0)
        self.assertNotEqual(fb_cpy._mv[9], 0)
        
        # test line (diagonal) - should raise
        with self.assertRaises(NotImplementedError):
            fb_cpy.line(0, 0, 9, 9, 0xFFFF)

    def test_micropython_init(self):
        # Just verifying it can be initialized without crashing
        fb_mpy = framebuffer_micropython.Framebuffer(10, 10)
        self.assertEqual(fb_mpy.width, 10)
        
if __name__ == '__main__':
    unittest.main()
