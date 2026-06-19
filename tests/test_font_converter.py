import unittest
import os
import sys

# Add the root directory to sys.path to import tools
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import tools.font_converter

class TestFontConverter(unittest.TestCase):
    def test_convert_default_font_and_png(self):
        # 1. Test TTF/Default font conversion
        afnt_path = "test_default.afnt"
        try:
            # We use an empty path to trigger ImageFont.load_default() in our tool if it fails loading
            # Actually, our tool calls ImageFont.truetype() which will fail on empty string,
            # so we'll mock ImageFont.load_default() if IOError is raised inside convert_font.
            # Wait, font_converter currently uses ImageFont.load_default() as fallback.
            tools.font_converter.convert_font("non_existent_font.ttf", afnt_path, size=10)
            
            self.assertTrue(os.path.exists(afnt_path))
            preview_path = afnt_path.replace('.afnt', '.png')
            self.assertTrue(os.path.exists(preview_path))
            
            # 2. Test PNG conversion using the generated preview PNG
            png_input = preview_path
            png_output_afnt = "test_from_png.afnt"
            
            tools.font_converter.convert_png(png_input, png_output_afnt)
            self.assertTrue(os.path.exists(png_output_afnt))
            
            # Verify the headers are the same
            with open(afnt_path, "rb") as f1, open(png_output_afnt, "rb") as f2:
                header1 = f1.read(8)
                header2 = f2.read(8)
                self.assertEqual(header1, header2)
                
        finally:
            for p in [afnt_path, afnt_path.replace('.afnt', '.png'), 
                      "test_from_png.afnt", "test_from_png.png"]:
                if os.path.exists(p):
                    os.remove(p)

    def test_convert_png_colkey(self):
        from PIL import Image, ImageDraw
        img = Image.new("RGBA", (160, 60), (0, 0, 0, 255)) # Black background
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, 0, 5, 5], fill=(255, 255, 255, 255))
        
        png_path = "test_colkey_input.png"
        out_path = "test_colkey_output.afnt"
        img.save(png_path)
        
        try:
            tools.font_converter.convert_png(png_path, out_path, colkey=(0, 0, 0))
            self.assertTrue(os.path.exists(out_path))
        finally:
            for p in [png_path, out_path, out_path.replace('.afnt', '.png')]:
                if os.path.exists(p):
                    os.remove(p)

if __name__ == '__main__':
    unittest.main()
