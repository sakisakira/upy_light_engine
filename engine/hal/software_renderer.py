def draw_blt(dst, dst_w, dst_h, x, y, src, src_w, src_h, u, v, w, h, is_argb, colkey=-1, byte_swap=False):
    """
    Software fallback for blt.
    dst, src: memoryview('H') if byte_swap=False, else bytearray
    """
    start_x = max(0, -x)
    start_y = max(0, -y)
    end_x = min(w, dst_w - x)
    end_y = min(h, dst_h - y)
    
    if start_x >= end_x or start_y >= end_y:
        return

    if not byte_swap:
        for i in range(start_y, end_y):
            dst_idx_base = (y + i) * dst_w + x
            src_idx_base = (v + i) * src_w + u
            
            for j in range(start_x, end_x):
                src_val = src[src_idx_base + j]
                
                if is_argb:
                    a = (src_val >> 12) & 0xF
                    if a == 0: continue
                    r = (src_val >> 8) & 0xF
                    g = (src_val >> 4) & 0xF
                    b = src_val & 0xF
                    sr = (r << 1) | (r >> 3)
                    sg = (g << 2) | (g >> 2)
                    sb = (b << 1) | (b >> 3)
                    if a == 15:
                        dst[dst_idx_base + j] = (sr << 11) | (sg << 5) | sb
                        continue
                    dst_val = dst[dst_idx_base + j]
                    dr = (dst_val >> 11) & 0x1F
                    dg = (dst_val >> 5) & 0x3F
                    db = dst_val & 0x1F
                    inv_a = 16 - a
                    out_r = (sr * a + dr * inv_a) >> 4
                    out_g = (sg * a + dg * inv_a) >> 4
                    out_b = (sb * a + db * inv_a) >> 4
                    dst[dst_idx_base + j] = (out_r << 11) | (out_g << 5) | out_b
                else:
                    if src_val != colkey:
                        dst[dst_idx_base + j] = src_val
    else:
        for i in range(start_y, end_y):
            dst_idx_base = (y + i) * dst_w + x
            src_idx_base = (v + i) * src_w + u
            
            for j in range(start_x, end_x):
                s_idx = (src_idx_base + j) * 2
                src_val = src[s_idx] | (src[s_idx+1] << 8)
                
                d_idx = (dst_idx_base + j) * 2
                if is_argb:
                    a = (src_val >> 12) & 15
                    if a == 0: continue
                    r = (src_val >> 8) & 15
                    g = (src_val >> 4) & 15
                    b = src_val & 15
                    sr = (r << 1) | (r >> 3)
                    sg = (g << 2) | (g >> 2)
                    sb = (b << 1) | (b >> 3)
                    if a == 15:
                        out_col = (sr << 11) | (sg << 5) | sb
                        swapped = ((out_col & 0xFF) << 8) | (out_col >> 8)
                        dst[d_idx] = swapped & 0xFF
                        dst[d_idx+1] = swapped >> 8
                        continue
                        
                    dst_val = dst[d_idx] | (dst[d_idx+1] << 8)
                    dst_val = ((dst_val & 0xFF) << 8) | (dst_val >> 8)
                    dr = (dst_val >> 11) & 31
                    dg = (dst_val >> 5) & 63
                    db = dst_val & 31
                    inv_a = 16 - a
                    out_r = (sr * a + dr * inv_a) >> 4
                    out_g = (sg * a + dg * inv_a) >> 4
                    out_b = (sb * a + db * inv_a) >> 4
                    out_col = (out_r << 11) | (out_g << 5) | out_b
                    swapped = ((out_col & 0xFF) << 8) | (out_col >> 8)
                    dst[d_idx] = swapped & 0xFF
                    dst[d_idx+1] = swapped >> 8
                else:
                    if src_val != colkey:
                        swapped = ((src_val & 0xFF) << 8) | (src_val >> 8)
                        dst[d_idx] = swapped & 0xFF
                        dst[d_idx+1] = swapped >> 8

def draw_sprite(dst, dst_w, dst_h, cx, cy, src, src_w, src_h, u, v, w, h, colkey=-1, rotate=0.0, scale=1.0, byte_swap=False):
    """
    Software fallback for sprite rendering.
    Assumes src is ARGB4444.
    """
    half_w = w * scale * 0.5
    half_h = h * scale * 0.5
    
    start_x = int(cx - half_w)
    start_y = int(cy - half_h)
    end_x = int(cx + half_w) + 1
    end_y = int(cy + half_h) + 1
    
    min_x = max(0, start_x)
    min_y = max(0, start_y)
    max_x = min(dst_w, end_x)
    max_y = min(dst_h, end_y)
    
    if min_x >= max_x or min_y >= max_y:
        return
        
    inv_scale = 1.0 / scale
    
    if not byte_swap:
        for dy in range(min_y, max_y):
            dst_idx_base = dy * dst_w
            sy = int(((dy - cy) * inv_scale + h * 0.5) // 1)
            if sy < 0 or sy >= h: continue
            src_idx_base = (v + sy) * src_w + u
            
            for dx in range(min_x, max_x):
                sx = int(((dx - cx) * inv_scale + w * 0.5) // 1)
                if sx < 0 or sx >= w: continue
                
                src_val = src[src_idx_base + sx]
                
                a = (src_val >> 12) & 0xF
                if a == 0: continue
                r = (src_val >> 8) & 0xF
                g = (src_val >> 4) & 0xF
                b = src_val & 0xF
                sr = (r << 1) | (r >> 3)
                sg = (g << 2) | (g >> 2)
                sb = (b << 1) | (b >> 3)
                if a == 15:
                    dst[dst_idx_base + dx] = (sr << 11) | (sg << 5) | sb
                    continue
                dst_val = dst[dst_idx_base + dx]
                dr = (dst_val >> 11) & 0x1F
                dg = (dst_val >> 5) & 0x3F
                db = dst_val & 0x1F
                inv_a = 16 - a
                out_r = (sr * a + dr * inv_a) >> 4
                out_g = (sg * a + dg * inv_a) >> 4
                out_b = (sb * a + db * inv_a) >> 4
                dst[dst_idx_base + dx] = (out_r << 11) | (out_g << 5) | out_b
    else:
        for dy in range(min_y, max_y):
            dst_idx_base = dy * dst_w
            sy = int(((dy - cy) * inv_scale + h * 0.5) // 1)
            if sy < 0 or sy >= h: continue
            src_idx_base = (v + sy) * src_w + u
            
            for dx in range(min_x, max_x):
                sx = int(((dx - cx) * inv_scale + w * 0.5) // 1)
                if sx < 0 or sx >= w: continue
                
                s_idx = (src_idx_base + sx) * 2
                src_val = src[s_idx] | (src[s_idx+1] << 8)
                
                a = (src_val >> 12) & 15
                if a == 0: continue
                r = (src_val >> 8) & 15
                g = (src_val >> 4) & 15
                b = src_val & 15
                sr = (r << 1) | (r >> 3)
                sg = (g << 2) | (g >> 2)
                sb = (b << 1) | (b >> 3)
                
                d_idx = (dst_idx_base + dx) * 2
                if a == 15:
                    out_col = (sr << 11) | (sg << 5) | sb
                    swapped = ((out_col & 0xFF) << 8) | (out_col >> 8)
                    dst[d_idx] = swapped & 0xFF
                    dst[d_idx+1] = swapped >> 8
                    continue
                    
                dst_val = dst[d_idx] | (dst[d_idx+1] << 8)
                dst_val = ((dst_val & 0xFF) << 8) | (dst_val >> 8)
                dr = (dst_val >> 11) & 31
                dg = (dst_val >> 5) & 63
                db = dst_val & 31
                inv_a = 16 - a
                out_r = (sr * a + dr * inv_a) >> 4
                out_g = (sg * a + dg * inv_a) >> 4
                out_b = (sb * a + db * inv_a) >> 4
                out_col = (out_r << 11) | (out_g << 5) | out_b
                swapped = ((out_col & 0xFF) << 8) | (out_col >> 8)
                dst[d_idx] = swapped & 0xFF
                dst[d_idx+1] = swapped >> 8
