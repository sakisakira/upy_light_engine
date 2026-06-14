"# Feature Enhancements: Font Color & Window Resizing

This plan covers two major engine features requested:
1. **Dynamic Font Color**: Allowing text drawing to be tinted with a custom color instead of the static color stored in the AFNT image.
2. **Window Resizing**: Allowing the CPython PC emulator window to be resized freely while maintaining the 240x135 aspect ratio.

## User Review Required

- **API Change**: `hal.font.text` will accept an optional `color=-1` argument. If omitted or `-1`, it draws the font's original color.
- **API Change**: `framebuffer.blt` will accept an optional `color=-1` argument. For ARGB4444 images, this overrides the RGB channels but keeps the Alpha channel.
- **Window Resizing**: The Tkinter canvas will now expand with the window and automatically calculate the maximum possible integer or float scale to fit the `240x135` game screen, adding letterboxing (black bars) where necessary.

## Proposed Changes

---

### `framebuffer.py`
Update the Facade class to support the new `color` argument for the `blt` method.
#### [MODIFY] `framebuffer.py`
- Change `blt` signature to `def blt(self, x, y, img, u, v, w, h, colkey=-1, color=-1):`
- Pass `color` down to the hal `blt` call.

---

### `hal/font.py`
Pass the color from the `text()` function down to the `blt()` call.
#### [MODIFY] `hal/font.py`
- Change `text` signature to `def text(screen, x, y, text_str, font, color=-1, spacing=1):`
- Add `color=color` argument to the `screen.blt` calls inside the function.

---

### `hal/framebuffer_cpython.py`
Implement the dynamic coloring in the software renderer, and add auto-scaling to the Tkinter canvas.
#### [MODIFY] `hal/framebuffer_cpython.py`
- **Dynamic Color**:
  - Update `blt` signature to include `color=-1`.
  - Inside the `is_argb` block, add logic to check `if color != -1:`. If true, extract the source RGB components (`sr`, `sg`, `sb`) from the `color` argument (which is an RGB565 integer) instead of decoding them from the source pixel.
- **Window R
<truncated 1386 bytes>