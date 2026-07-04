#include "engine_render.h"
#include <stddef.h>
#include <math.h>
#include <assert.h>
#include <stdlib.h>

void convert_palette_chunk(uint8_t *src, uint16_t *dst, uint16_t *pal, int num_pixels) {
    for (int i = 0; i < num_pixels; i++) {
        dst[i] = pal[src[i]];
    }
}

static void render_clear(EngineFramebuffer *framebuffer, uint16_t color) {
    if (framebuffer->format == kFormatIndex8) {
        uint8_t c8 = (uint8_t)color;
        int total = framebuffer->width * framebuffer->height;
        for (int i = 0; i < total; i++) {
            framebuffer->buffer[i] = c8;
        }
    } else {
        assert(0 && "Unsupported framebuffer format in render_clear");
    }
}

static void render_pset(EngineFramebuffer *framebuffer, int16_t x, int16_t y, uint16_t color) {
    if (framebuffer->format != kFormatIndex8) {
        assert(0 && "Unsupported framebuffer format in render_pset");
        return;
    }
    if (x >= 0 && x < framebuffer->width && y >= 0 && y < framebuffer->height) {
        framebuffer->buffer[y * framebuffer->width + x] = (uint8_t)color;
    }
}

static void render_line(EngineFramebuffer *framebuffer, int16_t x1, int16_t y1, int16_t x2, int16_t y2, uint16_t color) {
    if (framebuffer->format != kFormatIndex8) {
        assert(0 && "Unsupported framebuffer format in render_line");
        return;
    }
    int dx = abs(x2 - x1);
    int sx = x1 < x2 ? 1 : -1;
    int dy = -abs(y2 - y1);
    int sy = y1 < y2 ? 1 : -1;
    int err = dx + dy;
    
    while (1) {
        if (x1 >= 0 && x1 < framebuffer->width && y1 >= 0 && y1 < framebuffer->height) {
            framebuffer->buffer[y1 * framebuffer->width + x1] = (uint8_t)color;
        }
        if (x1 == x2 && y1 == y2) break;
        int e2 = 2 * err;
        if (e2 >= dy) {
            err += dy;
            x1 += sx;
        }
        if (e2 <= dx) {
            err += dx;
            y1 += sy;
        }
    }
}

static void render_fill_rect(EngineFramebuffer *framebuffer, int16_t x, int16_t y,
                             int16_t w, int16_t h, uint16_t color) {
    int start_x = (x < 0) ? 0 : x;
    int end_x = (x + w > framebuffer->width) ? framebuffer->width : x + w;
    int start_y = (y < 0) ? 0 : y;
    int end_y = (y + h > framebuffer->height) ? framebuffer->height : y + h;

    if (start_x >= end_x || start_y >= end_y) return;

    if (framebuffer->format == kFormatIndex8) {
        uint8_t c8 = (uint8_t)color;
        for (int row = start_y; row < end_y; row++) {
            int idx = row * framebuffer->width + start_x;
            for (int col = start_x; col < end_x; col++) {
                framebuffer->buffer[idx++] = c8;
            }
        }
    } else {
        assert(0 && "Unsupported framebuffer format in render_fill_rect");
    }
}

static void render_blt(EngineFramebuffer *framebuffer, int16_t x, int16_t y, EngineImage *img, int16_t u, int16_t v, int16_t w, int16_t h, uint16_t colkey, int tint) {
    if (framebuffer->format != kFormatIndex8 || img->format != kFormatIndex8) {
        assert(0 && "Unsupported format in render_blt");
        return;
    }
    
    int16_t start_x = (x < 0) ? 0 : x;
    int16_t start_y = (y < 0) ? 0 : y;
    int16_t end_x = (x + w > framebuffer->width) ? framebuffer->width : x + w;
    int16_t end_y = (y + h > framebuffer->height) ? framebuffer->height : y + h;
    
    if (start_x >= end_x || start_y >= end_y) return;
    
    for (int i = start_y; i < end_y; i++) {
        int dst_idx_base = i * framebuffer->width + x;
        int src_idx_base = (v + (i - y)) * img->width + u;
        
        for (int j = start_x; j < end_x; j++) {
            uint8_t src_val = img->data[src_idx_base + (j - x)];
            if (src_val != colkey) {
                if (tint >= 0) {
                    framebuffer->buffer[dst_idx_base + (j - x)] = (uint8_t)tint;
                } else {
                    framebuffer->buffer[dst_idx_base + (j - x)] = src_val;
                }
            }
        }
    }
}

static void render_draw_sprite(EngineFramebuffer *framebuffer, int16_t cx, int16_t cy,
                               float scale, EngineSprite *sprite, int tint) {
    if (framebuffer->format != kFormatIndex8) {
        assert(0 && "Unsupported framebuffer format in render_draw_sprite");
        return;
    }
    if (scale <= 0.0f) return;
    if (sprite->image == NULL) return;

    int dst_w = framebuffer->width;
    int dst_h = framebuffer->height;
    int src_w = sprite->image->width;
    int u = sprite->u;
    int v = sprite->v;
    int w = sprite->w;
    int h = sprite->h;
    uint8_t colkey = (uint8_t)sprite->colkey;

    uint8_t *dst = framebuffer->buffer;
    uint8_t *src = sprite->image->data;

    float inv_scale = 1.0f / scale;
    int cos_inv_fp = (int)(inv_scale * 256.0f);
    int sin_inv_fp = 0; // rotation not implemented yet

    int cx_fp = cx << 8;
    int cy_fp = cy << 8;

    int half_w = (int)((w * scale) / 2.0f);
    int half_h = (int)((h * scale) / 2.0f);

    int min_x = cx - half_w;
    int max_x = cx + half_w;
    int min_y = cy - half_h;
    int max_y = cy + half_h;

    if (min_x < 0) min_x = 0;
    if (max_x > dst_w) max_x = dst_w;
    if (min_y < 0) min_y = 0;
    if (max_y > dst_h) max_y = dst_h;

    int w_half_fp = w << 7;
    int h_half_fp = h << 7;
    int uv_base = v * src_w + u;

    for (int dy = min_y; dy < max_y; dy++) {
        int dist_y_fp = (dy << 8) - cy_fp;
        int sx_base_fp = -((dist_y_fp * sin_inv_fp) >> 8) + w_half_fp;
        int sy_base_fp = ((dist_y_fp * cos_inv_fp) >> 8) + h_half_fp;
        int dst_idx_base = dy * dst_w;

        int dist_x_fp_start = (min_x << 8) - cx_fp;
        int sx_fp = ((dist_x_fp_start * cos_inv_fp) >> 8) + sx_base_fp;
        int sy_fp = ((dist_x_fp_start * sin_inv_fp) >> 8) + sy_base_fp;

        for (int dx = min_x; dx < max_x; dx++) {
            int sx = sx_fp >> 8;
            int sy = sy_fp >> 8;
            sx_fp += cos_inv_fp;
            sy_fp += sin_inv_fp;

            if ((unsigned int)sx < (unsigned int)w && (unsigned int)sy < (unsigned int)h) {
                int src_idx = sy * src_w + uv_base + sx;
                uint8_t src_val = src[src_idx];
                if (src_val != colkey) {
                    dst[dst_idx_base + dx] = (tint != -1) ? (uint8_t)tint : src_val;
                }
            }
        }
    }
}

static void render_draw_text(EngineFramebuffer *framebuffer, int16_t x, int16_t y, EngineImage *font,
                             int char_w, int char_h, int columns,
                             const uint8_t *text, int text_len,
                             int16_t *lookup, int tint) {
    if (framebuffer->format != kFormatIndex8) {
        assert(0 && "Unsupported framebuffer format in render_draw_text");
        return;
    }
    if (font == NULL) return;

    int dst_w = framebuffer->width;
    int dst_h = framebuffer->height;
    int font_w = font->width;
    uint8_t *dst = framebuffer->buffer;
    uint8_t *font_buf = font->data;

    for (int i = 0; i < text_len; i++) {
        uint8_t code = text[i];
        int idx = -1;
        if (lookup != NULL) {
            idx = lookup[code];
        } else {
            if (code >= 32 && code <= 126) {
                idx = code - 32;
            }
        }

        if (idx < 0) continue;

        int u = (idx % columns) * char_w;
        int v = (idx / columns) * char_h;
        int px = x + i * char_w;
        int py = y;

        int draw_start_x = (px < 0) ? -px : 0;
        int draw_end_x = (px + char_w > dst_w) ? dst_w - px : char_w;
        int draw_start_y = (py < 0) ? -py : 0;
        int draw_end_y = (py + char_h > dst_h) ? dst_h - py : char_h;

        if (draw_start_x >= draw_end_x || draw_start_y >= draw_end_y) continue;

        for (int row = draw_start_y; row < draw_end_y; row++) {
            int dst_idx_base = (py + row) * dst_w + px;
            int src_idx_base = (v + row) * font_w + u;
            for (int col = draw_start_x; col < draw_end_x; col++) {
                uint8_t src_val = font_buf[src_idx_base + col];
                if (src_val != 0) { // colkey is 0 for fonts
                    dst[dst_idx_base + col] = (tint != -1) ? (uint8_t)tint : src_val;
                }
            }
        }
    }
}

void render_display_list(EngineFramebuffer *framebuffer, DisplayList *display_list) {
    if (framebuffer == NULL || display_list == NULL) return;
    if (framebuffer->format != kFormatIndex8) {
        assert(0 && "Unsupported framebuffer format in render_display_list");
        return; // Currently only kFormatIndex8 supported for drawing
    }

    for (int i = 0; i < display_list->count; i++) {
        RenderCommand *cmd = &display_list->commands[i];
        switch (cmd->type) {
            case kCmdClear:
                render_clear(framebuffer, cmd->args.clear.color);
                break;
            case kCmdPset:
                render_pset(framebuffer, cmd->args.pset.x, cmd->args.pset.y, cmd->args.pset.color);
                break;
            case kCmdLine:
                render_line(framebuffer, cmd->args.line.x1, cmd->args.line.y1, cmd->args.line.x2, cmd->args.line.y2, cmd->args.line.color);
                break;
            case kCmdFillRect:
                render_fill_rect(framebuffer, cmd->args.fill_rect.x, cmd->args.fill_rect.y,
                                 cmd->args.fill_rect.w, cmd->args.fill_rect.h,
                                 cmd->args.fill_rect.color);
                break;
            case kCmdBlt:
                render_blt(framebuffer, cmd->args.blt.x, cmd->args.blt.y,
                           cmd->args.blt.img, cmd->args.blt.u, cmd->args.blt.v,
                           cmd->args.blt.w, cmd->args.blt.h, cmd->args.blt.colkey, cmd->args.blt.tint);
                break;
            case kCmdDrawSprite:
                render_draw_sprite(framebuffer, cmd->args.draw_sprite.cx, cmd->args.draw_sprite.cy,
                                   cmd->args.draw_sprite.scale, cmd->args.draw_sprite.sprite,
                                   cmd->args.draw_sprite.tint);
                break;
            case kCmdDrawText:
                render_draw_text(framebuffer, cmd->args.draw_text.x, cmd->args.draw_text.y, cmd->args.draw_text.font,
                                 cmd->args.draw_text.char_w, cmd->args.draw_text.char_h, cmd->args.draw_text.columns,
                                 cmd->args.draw_text.text, cmd->args.draw_text.text_len, cmd->args.draw_text.lookup,
                                 cmd->args.draw_text.tint);
                break;
        }
    }
}
