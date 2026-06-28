import math

def draw_blt(dst, dst_w, dst_h, x, y, src, src_w, src_h, u, v, w, h, colkey=0, tint=None):
    """
    Software fallback for blt. (INDEX8 8-bit palette format)
    dst, src: memoryview('B') or bytearray
    """
    start_x = max(0, -x)
    start_y = max(0, -y)
    end_x = min(w, dst_w - x)
    end_y = min(h, dst_h - y)
    
    if start_x >= end_x or start_y >= end_y:
        return

    for i in range(start_y, end_y):
        dst_idx_base = (y + i) * dst_w + x
        src_idx_base = (v + i) * src_w + u
        
        for j in range(start_x, end_x):
            src_val = src[src_idx_base + j]
            if src_val != colkey:
                if tint is not None:
                    dst[dst_idx_base + j] = tint
                else:
                    dst[dst_idx_base + j] = src_val

def draw_sprite(dst, dst_w, dst_h, cx, cy, src, src_w, src_h, u, v, w, h, colkey=0, rotate=0.0, scale=1.0, tint=None):
    """
    Software fallback for sprite rendering. (INDEX8 8-bit palette format)
    """
    if rotate == 0.0:
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
        cos_inv = inv_scale
        sin_inv = 0.0
    else:
        cos_f = math.cos(rotate) * scale
        sin_f = math.sin(rotate) * scale
        hw = w * 0.5
        hh = h * 0.5
        corners = [
            ( hw,  hh),
            ( hw, -hh),
            (-hw,  hh),
            (-hw, -hh),
        ]
        min_cx = max_cx = min_cy = max_cy = 0
        first = True
        for (px, py) in corners:
            rx = px * cos_f - py * sin_f
            ry = px * sin_f + py * cos_f
            if first:
                min_cx, max_cx = rx, rx
                min_cy, max_cy = ry, ry
                first = False
            else:
                if rx < min_cx: min_cx = rx
                elif rx > max_cx: max_cx = rx
                if ry < min_cy: min_cy = ry
                elif ry > max_cy: max_cy = ry
                
        start_x = int(cx + min_cx)
        start_y = int(cy + min_cy)
        end_x = int(cx + max_cx) + 1
        end_y = int(cy + max_cy) + 1
        
        min_x = max(0, start_x)
        min_y = max(0, start_y)
        max_x = min(dst_w, end_x)
        max_y = min(dst_h, end_y)
        
        if min_x >= max_x or min_y >= max_y:
            return
            
        inv_scale = 1.0 / scale
        cos_inv = math.cos(-rotate) * inv_scale
        sin_inv = math.sin(-rotate) * inv_scale

    for dy in range(min_y, max_y):
        dist_y = dy - cy
        sx_base = -dist_y * sin_inv + w * 0.5
        sy_base =  dist_y * cos_inv + h * 0.5
        dst_idx_base = dy * dst_w
        
        for dx in range(min_x, max_x):
            dist_x = dx - cx
            sx = int((dist_x * cos_inv + sx_base) // 1)
            if sx < 0 or sx >= w: continue
            sy = int((dist_x * sin_inv + sy_base) // 1)
            if sy < 0 or sy >= h: continue
            
            src_idx_base = (v + sy) * src_w + u
            src_val = src[src_idx_base + sx]
            
            if src_val != colkey:
                if tint is not None:
                    dst[dst_idx_base + dx] = tint
                else:
                    dst[dst_idx_base + dx] = src_val
