import os
import sys
import subprocess
import glob

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tools_dir = os.path.join(base_dir, "tools")
    assets_dir = os.path.join(base_dir, "assets")

    print("=== Building Assets ===")
    
    # 1. Fonts (Convert .png in assets/fonts/src to .afnt in assets/fonts)
    fonts_src = os.path.join(assets_dir, "fonts", "src")
    fonts_out = os.path.join(assets_dir, "fonts")
    if os.path.exists(fonts_src):
        for in_path in glob.glob(os.path.join(fonts_src, "*.png")):
            filename = os.path.basename(in_path)
            # Remove '_input' if present to match target names
            out_name = filename.replace(".png", ".afnt").replace("_input", "")
            out_path = os.path.join(fonts_out, out_name)
            print(f"Building font: {filename} -> {out_name}")
            subprocess.run([sys.executable, os.path.join(tools_dir, "font_converter.py"), in_path, out_path], check=True)

    # 2. Images (Convert .png in assets/images to INDEX8 .uimg and generate palette)
    images_dir = os.path.join(assets_dir, "images")
    if os.path.exists(images_dir):
        palette_out = os.path.join(images_dir, "palette.bin")
        print(f"Building images in {images_dir} -> INDEX8 + {palette_out}")
        subprocess.run([sys.executable, os.path.join(tools_dir, "convert_assets.py"), images_dir, palette_out], check=True)

    # 3. Sounds (Convert .mml in assets/sounds to .ubgm)
    sounds_dir = os.path.join(assets_dir, "sounds")
    if os.path.exists(sounds_dir):
        for in_path in glob.glob(os.path.join(sounds_dir, "*.mml")):
            filename = os.path.basename(in_path)
            out_name = filename.replace(".mml", ".ubgm")
            out_path = os.path.join(sounds_dir, out_name)
            print(f"Building sound: {filename} -> {out_name}")
            subprocess.run([sys.executable, os.path.join(tools_dir, "mml2ubgm.py"), in_path, out_path], check=True)

    print("=== Asset Build Complete ===")

if __name__ == "__main__":
    main()
