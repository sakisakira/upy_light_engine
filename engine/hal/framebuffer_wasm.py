import sys

# WASM environment needs 'js' and 'pyodide'
try:
    import js
    from pyodide.ffi import to_js
except ImportError:
    pass

from .engine_ctypes import FramebufferBase

class Framebuffer(FramebufferBase):
    def __init__(self, width, height, buffer=None):
        super().__init__(width, height, buffer)
        
        js.eval("""
        window.drawFramebufferWasm = function(canvasId, buffer8, palette24, w, h) {
            const canvas = document.getElementById(canvasId);
            if (!canvas) return;
            const ctx = canvas.getContext("2d");
            
            // Re-create image data if dimensions don't match
            if (!window._wasmImgData || window._wasmImgData.width !== w || window._wasmImgData.height !== h) {
                window._wasmImgData = ctx.createImageData(w, h);
                // Also resize the canvas to match the framebuffer exactly (optional, but good for scaling)
                canvas.width = w;
                canvas.height = h;
            }
            const imgData = window._wasmImgData;
            const data32 = new Uint32Array(imgData.data.buffer);
            const data8 = buffer8.toJs();
            const pal24 = palette24.toJs();
            for (let i = 0; i < data8.length; i++) {
                const c_idx = data8[i];
                const col24 = pal24[c_idx];
                const r = (col24 >> 16) & 0xFF;
                const g = (col24 >> 8) & 0xFF;
                const b = col24 & 0xFF;
                data32[i] = (255 << 24) | (b << 16) | (g << 8) | r;
            }
            ctx.putImageData(imgData, 0, 0);
        }
        """)

screen = Framebuffer(240, 135)
