#include "py/dynruntime.h"

// 1. convert_palette_chunk(src_buf, src_offset, dst_chunk, pal_buf, num_pixels)
mp_obj_t convert_palette_chunk(size_t n_args, const mp_obj_t *args) {
    mp_buffer_info_t src_buf, dst_buf, pal_buf;
    mp_get_buffer_raise(args[0], &src_buf, MP_BUFFER_READ);
    mp_get_buffer_raise(args[2], &dst_buf, MP_BUFFER_WRITE);
    mp_get_buffer_raise(args[3], &pal_buf, MP_BUFFER_READ);
    
    int src_offset = mp_obj_get_int(args[1]);
    int num_pixels = mp_obj_get_int(args[4]);
    
    uint8_t *src = (uint8_t *)src_buf.buf + src_offset;
    uint16_t *dst = (uint16_t *)dst_buf.buf;
    uint16_t *pal = (uint16_t *)pal_buf.buf;
    
    for (int i = 0; i < num_pixels; i++) {
        dst[i] = pal[src[i]];
    }
    return mp_const_none;
}
MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(convert_palette_chunk_obj, 5, 5, convert_palette_chunk);

// 2. draw_sprite(dst_buf, dst_w, dst_h, src_buf, src_w, src_h, u, v, w, h, cx_fp, cy_fp, min_x, max_x, min_y, max_y, cos_inv_fp, sin_inv_fp, colkey, tint)
mp_obj_t draw_sprite(size_t n_args, const mp_obj_t *args) {
    mp_buffer_info_t dst_info, src_info;
    mp_get_buffer_raise(args[0], &dst_info, MP_BUFFER_WRITE);
    mp_get_buffer_raise(args[3], &src_info, MP_BUFFER_READ);
    
    uint8_t *dst = (uint8_t *)dst_info.buf;
    uint8_t *src = (uint8_t *)src_info.buf;
    
    int dst_w = mp_obj_get_int(args[1]);
    int src_w = mp_obj_get_int(args[4]);
    int u = mp_obj_get_int(args[6]);
    int v = mp_obj_get_int(args[7]);
    int w = mp_obj_get_int(args[8]);
    int h = mp_obj_get_int(args[9]);
    int cx_fp = mp_obj_get_int(args[10]);
    int cy_fp = mp_obj_get_int(args[11]);
    int min_x = mp_obj_get_int(args[12]);
    int max_x = mp_obj_get_int(args[13]);
    int min_y = mp_obj_get_int(args[14]);
    int max_y = mp_obj_get_int(args[15]);
    int cos_inv_fp = mp_obj_get_int(args[16]);
    int sin_inv_fp = mp_obj_get_int(args[17]);
    int colkey = mp_obj_get_int(args[18]);
    int tint = mp_obj_get_int(args[19]);
    
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
                    dst[dst_idx_base + dx] = (tint != -1) ? tint : src_val;
                }
            }
        }
    }
    return mp_const_none;
}
MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(draw_sprite_obj, 20, 20, draw_sprite);

// 3. draw_text_fast(dst_buf, dst_w, dst_h, font_buf, font_w, char_w, char_h, cols, text_bytes, text_len, lookup_buf, x, y, tint)
mp_obj_t draw_text_fast(size_t n_args, const mp_obj_t *args) {
    mp_buffer_info_t dst_info, font_info, text_info, lookup_info;
    mp_get_buffer_raise(args[0], &dst_info, MP_BUFFER_WRITE);
    mp_get_buffer_raise(args[3], &font_info, MP_BUFFER_READ);
    mp_get_buffer_raise(args[8], &text_info, MP_BUFFER_READ);
    
    int16_t *lookup = NULL;
    if (args[10] != mp_const_none) {
        mp_get_buffer_raise(args[10], &lookup_info, MP_BUFFER_READ);
        lookup = (int16_t*)lookup_info.buf;
    }
    
    int dst_w = mp_obj_get_int(args[1]);
    int dst_h = mp_obj_get_int(args[2]);
    int font_w = mp_obj_get_int(args[4]);
    int char_w = mp_obj_get_int(args[5]);
    int char_h = mp_obj_get_int(args[6]);
    int cols = mp_obj_get_int(args[7]);
    int text_len = mp_obj_get_int(args[9]);
    int start_x = mp_obj_get_int(args[11]);
    int start_y = mp_obj_get_int(args[12]);
    int tint = mp_obj_get_int(args[13]);
    
    uint8_t *dst = (uint8_t*)dst_info.buf;
    uint8_t *font = (uint8_t*)font_info.buf;
    const uint8_t *text = (const uint8_t*)text_info.buf;
    
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
        
        int u = (idx % cols) * char_w;
        int v = (idx / cols) * char_h;
        int px = start_x + i * char_w;
        int py = start_y;
        
        int draw_start_x = (px < 0) ? -px : 0;
        int draw_end_x = (px + char_w > dst_w) ? dst_w - px : char_w;
        int draw_start_y = (py < 0) ? -py : 0;
        int draw_end_y = (py + char_h > dst_h) ? dst_h - py : char_h;
        
        if (draw_start_x >= draw_end_x || draw_start_y >= draw_end_y) continue;
        
        for (int row = draw_start_y; row < draw_end_y; row++) {
            int dst_idx_base = (py + row) * dst_w + px;
            int src_idx_base = (v + row) * font_w + u;
            for (int col = draw_start_x; col < draw_end_x; col++) {
                uint8_t src_val = font[src_idx_base + col];
                if (src_val != 0) { // colkey is 0 for fonts
                    dst[dst_idx_base + col] = (tint != -1) ? tint : src_val;
                }
            }
        }
    }
    return mp_const_none;
}
MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(draw_text_fast_obj, 14, 14, draw_text_fast);

mp_obj_t mpy_init(mp_obj_fun_bc_t *self, size_t n_args, size_t n_kw, mp_obj_t *args) {
    MP_DYNRUNTIME_INIT_ENTRY
    mp_store_global(MP_QSTR_convert_palette_chunk, MP_OBJ_FROM_PTR(&convert_palette_chunk_obj));
    mp_store_global(MP_QSTR_draw_sprite, MP_OBJ_FROM_PTR(&draw_sprite_obj));
    mp_store_global(MP_QSTR_draw_text_fast, MP_OBJ_FROM_PTR(&draw_text_fast_obj));
    MP_DYNRUNTIME_INIT_EXIT
}
