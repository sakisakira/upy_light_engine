import unittest
import os
import sys
from PIL import Image as PILImage

# Add the root directory to sys.path to import tools and modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import tools.png2uimg
from image import Image

class TestPng2Uimg(unittest.TestCase):
    def setUp(self):
        os.makedirs("tests/tmp", exist_ok=True)
        self.png_path = "tests/tmp/test_png2uimg_input.png"
        self.uimg_path = "tests/tmp/test_png2uimg_output.uimg"

    def tearDown(self):
        # Remove output UIMG file, but keep input PNG file for inspection per user request
        if os.path.exists(self.uimg_path):
            os.remove(self.uimg_path)

    def test_conversion_and_loading(self):
        # Create a test 16x16 RGBA image
        img = PILImage.new("RGBA", (16, 16), (0, 0, 0, 0))
        pixels = img.load()
        
        # Set specific test colors: radius 8 circle at (8, 8)
        for y in range(16):
            for x in range(16):
                # distance to center (8.5, 8.5) or (8, 8)
                # PIL coordinates are 0-15. center is 8, 8
                if (x - 8)**2 + (y - 8)**2 <= 8**2:
                    if y < 8:
                        pixels[x, y] = (255, 0, 0, 255)  # Red
                    else:
                        pixels[x, y] = (0, 0, 255, 255)  # Blue
        
        img.save(self.png_path)
        
        # Convert PNG to UIMG
        tools.png2uimg.convert_png_to_uimg(self.png_path, self.uimg_path)
        self.assertTrue(os.path.exists(self.uimg_path))
        
        # Load the UIMG back
        loaded = Image.load(self.uimg_path)
        
        # Validate dimensions and format
        self.assertEqual(loaded.width, 16)
        self.assertEqual(loaded.height, 16)
        self.assertEqual(loaded.format, "ARGB4444")
        
        # Verify specific pixel values packed into ARGB4444
        # (8, 4) is top half -> Red (0xFF00)
        self.assertEqual(loaded._mv[4 * 16 + 8], 0xFF00)
        
        # (8, 12) is bottom half -> Blue (a=15, b=15 -> 0xF00F)
        self.assertEqual(loaded._mv[12 * 16 + 8], 0xF00F)
        
        # (0, 0) is outside circle -> Transparent (0x0000)
        self.assertEqual(loaded._mv[0 * 16 + 0], 0x0000)

if __name__ == '__main__':
    unittest.main()
