# MicroPython Light 2D Game Engine

## What is this?

A thin, 2D sprite-based game engine written in Python, targeting the **M5Stack Cardputer Adv** and **Web Browsers (WebAssembly)**. 
To enable a rapid development loop, it also runs natively on Windows and macOS via CPython. This allows you to write your game logic once and run the exact same `main.py` code across all three platforms without any modifications.

## Prerequisites & Asset Building

Before running the game on any platform, you need to install the **Pillow** library. This library is required both for converting image assets and for rendering the game window on your PC.
```bash
pip install Pillow
```

### How to build assets
You must convert standard images and fonts into the engine's highly optimized proprietary formats (`.uimg` and `.afnt2`) to save memory on the MicroPython heap.
1. **Convert Sprite Images**:
   ```bash
   python tools/png2uimg.py assets/player.png assets/player.uimg
   ```
2. **Convert Fonts** (extracts only the specific characters you need):
   ```bash
   python tools/font_converter.py assets/font.ttf assets/font.afnt --size 16 --chars "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ "
   ```

## How to run

### 1. M5Stack Cardputer Adv (ESP32-S3)
The engine works out-of-the-box on standard MicroPython firmware, so getting started is very easy! However, to achieve full-speed I2S audio playback performance without stuttering, we highly recommend building the custom firmware containing our optimized C-module sound engine.

1. **(Optional) Build and Flash Custom Firmware**:
   First, initialize the MicroPython submodule and apply the required hardware patches (I2S and panic handler fixes) for the Cardputer Adv:
   ```powershell
   git submodule update --init
   .\scripts\mpy_apply_patches.ps1
   ```
   Next, use the provided build script to compile MicroPython with PSRAM support and the custom sound engine.
   ```powershell
   # Windows (Requires WSL/Docker for the build environment)
   .\scripts\mpy_build_firmware.ps1
   
   # Flash the firmware to your Cardputer (Replace COM4 with your port)
   python -m esptool --chip esp32s3 --port COM4 write_flash -z 0 micropython\ports\esp32\build-ESP32_GENERIC_S3\firmware.bin
   ```
2. **Upload Game Files**:
   Upload `main.py`, the `engine/` directory, and any asset folders (`fonts/`, `images/`, etc.) to the root of the Cardputer's flash memory using a tool like `mpremote` or `ampy`.
   ```bash
   mpremote cp -r engine :
   mpremote cp main.py :
   ```
3. Reboot the device to start the game.

### 2. Web Browser (WASM / Pyodide)
The engine runs entirely in the browser using PyScript (Pyodide). No Python installation is required for the player.
1. Start a local HTTP server in the project root:
   ```bash
   python -m http.server 8000
   ```
2. Open your web browser and navigate to:
   [http://localhost:8000/scripts/web/index.html](http://localhost:8000/scripts/web/index.html)
3. Click the game screen or press a key to unlock the Web Audio API and start the game.

### 3. PC (Windows / macOS)
You can run the engine locally using CPython for fast prototyping, debugging, and testing.
1. Run the main script from the project root:
   ```bash
   python main.py
   ```

## Script Pipeline

The `scripts/` directory contains tools organized by their target platform prefix. Here is the typical development pipeline for each platform:

### 1. Cardputer Adv (MicroPython) Pipeline
- **Step 1:** `.\scripts\mpy_apply_patches.ps1` - Applies necessary fixes (I2S, panic handler) to the MicroPython source tree.
- **Step 2:** `.\scripts\mpy_build_firmware.ps1` - Builds the custom firmware (with C modules) using Docker.
- **Step 3:** `.\scripts\cardputer_flash.ps1 -Port COMx` - Flashes the built firmware to the device via esptool.
- **Step 4:** `.\scripts\cardputer_install.ps1 -Port COMx` - Copies the Python engine and game assets to the device.
- **Step 5:** `.\scripts\cardputer_run.ps1 -Port COMx` - Runs the game on the device and streams the logs.
- *(Utility)* `.\scripts\cardputer_clean.ps1` - Erases all user files on the device filesystem.

### 2. Web Browser (WASM) Pipeline
- **Step 1:** `.\scripts\wasm_install_emsdk.ps1` - Installs the Emscripten SDK locally.
- **Step 2:** `.\scripts\wasm_build.ps1` - Compiles the C engine to WebAssembly (`.so` and `.wasm`).
- **Step 3:** `python scripts\wasm_serve.py` - Starts a local HTTP server with caching disabled to test the web build.

### 3. PC (Windows/macOS) Pipeline
- **Step 1:** `.\scripts\pc_build_dll.ps1` - Compiles the C engine into a dynamic library (`core_engine_win.dll`) for the local simulator.
- **Step 2:** `python main.py` - Runs the game using the compiled DLL.
