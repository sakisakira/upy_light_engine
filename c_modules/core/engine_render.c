#include "engine_render.h"
#include "engine_types.h"
// No longer relying on standard assert directly, but keeping it just in case
#include <assert.h>
#include <math.h>
#include <stddef.h>
#include <stdlib.h>

static void render_clear(EngineFramebuffer *framebuffer, uint16_t color) {
  if (framebuffer->format == kFormatIndex8) {
    uint8_t c8 = (uint8_t)color;
    int total = framebuffer->width * framebuffer->height;
    for (int i = 0; i < total; i++) {
      framebuffer->buffer[i] = c8;
    }
  } else {
    ENGINE_ASSERT_RETURN(0, "Unsupported framebuffer format in render_clear");
  }
}

static void render_pset(EngineFramebuffer *framebuffer, int16_t x, int16_t y,
                        uint16_t color) {
  if (framebuffer->format != kFormatIndex8) {
    ENGINE_ASSERT_RETURN(0, "Unsupported framebuffer format in render_pset");
  }
  if (x >= 0 && x < framebuffer->width && y >= 0 && y < framebuffer->height) {
    framebuffer->buffer[y * framebuffer->width + x] = (uint8_t)color;
  }
}

static void render_line(EngineFramebuffer *framebuffer, int16_t x1, int16_t y1,
                        int16_t x2, int16_t y2, uint16_t color) {
  if (framebuffer->format != kFormatIndex8) {
    ENGINE_ASSERT_RETURN(0, "Unsupported framebuffer format in render_line");
  }
  int dx = abs(x2 - x1);
  int sx = x1 < x2 ? 1 : -1;
  int dy = -abs(y2 - y1);
  int sy = y1 < y2 ? 1 : -1;
  int err = dx + dy;

  while (1) {
    if (x1 >= 0 && x1 < framebuffer->width && y1 >= 0 &&
        y1 < framebuffer->height) {
      framebuffer->buffer[y1 * framebuffer->width + x1] = (uint8_t)color;
    }
    if (x1 == x2 && y1 == y2)
      break;
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

static void render_fill_rect(EngineFramebuffer *framebuffer, int16_t x,
                             int16_t y, int16_t w, int16_t h, uint16_t color) {
  int start_x = (x < 0) ? 0 : x;
  int end_x = (x + w > framebuffer->width) ? framebuffer->width : x + w;
  int start_y = (y < 0) ? 0 : y;
  int end_y = (y + h > framebuffer->height) ? framebuffer->height : y + h;

  if (start_x >= end_x || start_y >= end_y)
    return;

  if (framebuffer->format == kFormatIndex8) {
    uint8_t c8 = (uint8_t)color;
    for (int row = start_y; row < end_y; row++) {
      int idx = row * framebuffer->width + start_x;
      for (int col = start_x; col < end_x; col++) {
        framebuffer->buffer[idx++] = c8;
      }
    }
  } else {
    ENGINE_ASSERT_RETURN(0, "Unsupported framebuffer format in render_fill_rect");
  }
}

static void render_blt(EngineFramebuffer *framebuffer, int16_t x, int16_t y,
                       EngineImage *img, int16_t u, int16_t v, int16_t w,
                       int16_t h, uint16_t colkey, int tint) {
  if (framebuffer->format != kFormatIndex8 || img->format != kFormatIndex8) {
    ENGINE_ASSERT_RETURN(0, "Unsupported format in render_blt");
  }

  int16_t start_x = (x < 0) ? 0 : x;
  int16_t start_y = (y < 0) ? 0 : y;
  int16_t end_x = (x + w > framebuffer->width) ? framebuffer->width : x + w;
  int16_t end_y = (y + h > framebuffer->height) ? framebuffer->height : y + h;

  if (start_x >= end_x || start_y >= end_y)
    return;

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

static void render_draw_sprite(EngineFramebuffer *framebuffer, int16_t cx,
                               int16_t cy, float scale, float angle,
                               EngineImage *img, int16_t u, int16_t v,
                               int16_t w, int16_t h, uint16_t colkey_in,
                               int tint) {
  if (framebuffer->format != kFormatIndex8) {
    ENGINE_ASSERT_RETURN(0, "Unsupported framebuffer format in render_draw_sprite");
  }
  if (scale <= 0.0f)
    return;
  if (img == NULL)
    return;

  int dst_w = framebuffer->width;
  int dst_h = framebuffer->height;
  int src_w = img->width;
  uint8_t colkey = (uint8_t)colkey_in;

  uint8_t *dst = framebuffer->buffer;
  uint8_t *src = img->data;

  float cos_a = cosf(angle);
  float sin_a = sinf(angle);

  float inv_scale = 1.0f / scale;
  // For inverse mapping (screen to texture), we use -angle.
  // cos(-a) = cos(a), sin(-a) = -sin(a)
  float c_val = cos_a * inv_scale;
  float s_val = -sin_a * inv_scale;

  int cos_inv_fp = (int)(c_val * 256.0f);
  int sin_inv_fp = (int)(s_val * 256.0f);

  int cx_fp = cx << 8;
  int cy_fp = cy << 8;

  // Exact bounding box of the rotated rectangle
  float c_fwd = cos_a * scale;
  float s_fwd = sin_a * scale;
  int half_w = (int)(fabsf((w / 2.0f) * c_fwd) + fabsf((h / 2.0f) * s_fwd)) + 1;
  int half_h = (int)(fabsf((w / 2.0f) * s_fwd) + fabsf((h / 2.0f) * c_fwd)) + 1;

  int min_x = cx - half_w;
  int max_x = cx + half_w;
  int min_y = cy - half_h;
  int max_y = cy + half_h;

  if (min_x < 0)
    min_x = 0;
  if (max_x > dst_w)
    max_x = dst_w;
  if (min_y < 0)
    min_y = 0;
  if (max_y > dst_h)
    max_y = dst_h;

  int w_half_fp = w << 7;
  int h_half_fp = h << 7;
  int uv_base = v * src_w + u;

  for (int dy = min_y; dy < max_y; dy++) {
    int dist_y_fp = (dy << 8) - cy_fp;

    // Base coordinates for the start of the scanline (min_x)
    int dist_x_fp = (min_x << 8) - cx_fp;
    int sx_fp = -((dist_y_fp * sin_inv_fp) >> 8) + w_half_fp +
                ((dist_x_fp * cos_inv_fp) >> 8);
    int sy_fp = ((dist_y_fp * cos_inv_fp) >> 8) + h_half_fp +
                ((dist_x_fp * sin_inv_fp) >> 8);

    for (int dx = min_x; dx < max_x; dx++) {
      int sx = sx_fp >> 8;
      int sy = sy_fp >> 8;

      if (sx >= 0 && sx < w && sy >= 0 && sy < h) {
        uint8_t color = src[uv_base + sy * src_w + sx];
        if (color != colkey) {
          if (tint >= 0) {
            dst[dy * dst_w + dx] = (uint8_t)tint;
          } else {
            dst[dy * dst_w + dx] = color;
          }
        }
      }

      // Advance by 1 pixel in X (which corresponds to 1<<8 in FP)
      // So sx_fp increases by cos_inv_fp, sy_fp increases by sin_inv_fp
      sx_fp += cos_inv_fp;
      sy_fp += sin_inv_fp;
    }
  }
}

static void render_draw_text(EngineFramebuffer *framebuffer, int16_t x,
                             int16_t y, EngineImage *font, int char_w,
                             int char_h, int columns, const uint8_t *text,
                             int text_len, int16_t *lookup, int tint) {
  if (framebuffer->format != kFormatIndex8) {
    ENGINE_ASSERT_RETURN(0, "Unsupported framebuffer format in render_draw_text");
  }
  if (font == NULL)
    return;

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

    if (idx < 0)
      continue;

    int u = (idx % columns) * char_w;
    int v = (idx / columns) * char_h;
    int px = x + i * char_w;
    int py = y;

    int draw_start_x = (px < 0) ? -px : 0;
    int draw_end_x = (px + char_w > dst_w) ? dst_w - px : char_w;
    int draw_start_y = (py < 0) ? -py : 0;
    int draw_end_y = (py + char_h > dst_h) ? dst_h - py : char_h;

    if (draw_start_x >= draw_end_x || draw_start_y >= draw_end_y)
      continue;

    if (tint != -1) {
      uint8_t t = (uint8_t)tint;
      for (int row = draw_start_y; row < draw_end_y; row++) {
        int dst_idx_base = (py + row) * dst_w + px;
        int src_idx_base = (v + row) * font_w + u;
        for (int col = draw_start_x; col < draw_end_x; col++) {
          if (font_buf[src_idx_base + col] != 0) {
            dst[dst_idx_base + col] = t;
          }
        }
      }
    } else {
      for (int row = draw_start_y; row < draw_end_y; row++) {
        int dst_idx_base = (py + row) * dst_w + px;
        int src_idx_base = (v + row) * font_w + u;
        for (int col = draw_start_x; col < draw_end_x; col++) {
          uint8_t src_val = font_buf[src_idx_base + col];
          if (src_val != 0) {
            dst[dst_idx_base + col] = src_val;
          }
        }
      }
    }
  }
}

void render_display_list(EngineFramebuffer *framebuffer,
                         DisplayList *display_list) {
  if (framebuffer == NULL || display_list == NULL)
    return;
  if (framebuffer->format != kFormatIndex8) {
    ENGINE_ASSERT_RETURN(0, "Unsupported framebuffer format in render_display_list");
  }

  for (int i = 0; i < display_list->count; i++) {
    RenderCommand *cmd = &display_list->commands[i];
    switch (cmd->type) {
    case kCmdClear:
      render_clear(framebuffer, cmd->args.clear.color);
      break;
    case kCmdPset:
      render_pset(framebuffer, cmd->args.pset.x, cmd->args.pset.y,
                  cmd->args.pset.color);
      break;
    case kCmdLine:
      render_line(framebuffer, cmd->args.line.x1, cmd->args.line.y1,
                  cmd->args.line.x2, cmd->args.line.y2, cmd->args.line.color);
      break;
    case kCmdFillRect:
      render_fill_rect(framebuffer, cmd->args.fill_rect.x,
                       cmd->args.fill_rect.y, cmd->args.fill_rect.w,
                       cmd->args.fill_rect.h, cmd->args.fill_rect.color);
      break;
    case kCmdBlt:
      render_blt(framebuffer, cmd->args.blt.x, cmd->args.blt.y,
                 cmd->args.blt.img, cmd->args.blt.u, cmd->args.blt.v,
                 cmd->args.blt.w, cmd->args.blt.h, cmd->args.blt.colkey,
                 cmd->args.blt.tint);
      break;
    case kCmdDrawSprite:
      render_draw_sprite(framebuffer, cmd->args.draw_sprite.cx,
                         cmd->args.draw_sprite.cy, cmd->args.draw_sprite.scale,
                         cmd->args.draw_sprite.angle, cmd->args.draw_sprite.img,
                         cmd->args.draw_sprite.u, cmd->args.draw_sprite.v,
                         cmd->args.draw_sprite.w, cmd->args.draw_sprite.h,
                         cmd->args.draw_sprite.colkey,
                         cmd->args.draw_sprite.tint);
      break;
    case kCmdDrawText:
      render_draw_text(framebuffer, cmd->args.draw_text.x,
                       cmd->args.draw_text.y, cmd->args.draw_text.font,
                       cmd->args.draw_text.char_w, cmd->args.draw_text.char_h,
                       cmd->args.draw_text.columns, cmd->args.draw_text.text,
                       cmd->args.draw_text.text_len, cmd->args.draw_text.lookup,
                       cmd->args.draw_text.tint);
      break;
    }
  }
}
