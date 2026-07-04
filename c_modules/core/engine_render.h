#ifndef ENGINE_RENDER_H
#define ENGINE_RENDER_H

#include "engine_types.h"

// Execute a display list onto the framebuffer
void render_display_list(EngineFramebuffer *framebuffer,
                         DisplayList *display_list);

// Utility for sending palettes to ST7789
void convert_palette_chunk(uint8_t *src, uint16_t *dst, uint16_t *pal,
                           int num_pixels);

#endif // ENGINE_RENDER_H
