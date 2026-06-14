import hal_framebuffer as hal

# テスト用のARGB4444スプライト（円形の半透明グラデーション）を生成
def create_test_sprite(width, height):
    buf = bytearray(width * height * 2)
    mv = memoryview(buf).cast('H')
    
    for y in range(height):
        for x in range(width):
            # 中心からの距離でアルファ値を計算（中心が不透明、外側が透明）
            cx = width / 2.0
            cy = height / 2.0
            dist = ((x - cx)**2 + (y - cy)**2)**0.5
            max_dist = width / 2.0
            
            a = max(0, min(15, int(15 * (1 - dist / max_dist))))
            
            # 色はシアン（R:0, G:15, B:15）
            r = 0
            g = 15
            b = 15
            
            # ARGB4444フォーマットにパック
            mv[y * width + x] = (a << 12) | (r << 8) | (g << 4) | b
            
    # スプライトデータのコンテナとして Image クラスを使用
    return hal.Image(width, height, buf)

# --- ゲームの状態 ---
x = 100
y = 50
dx = 2
dy = 2
sprite = None

def update():
    global x, y, dx, dy
    x += dx
    y += dy
    
    # 画面端でバウンド
    if x <= 0 or x >= 240 - 32:
        dx = -dx
    if y <= 0 or y >= 135 - 32:
        dy = -dy

def draw():
    # 背景を暗い青 (ARGB4444: A=15, R=0, G=0, B=2) で塗りつぶす
    hal.screen.fill(0xF002)
    
    # 複数の矩形を描画して、アルファブレンドが機能しているか確認しやすくする
    for i in range(5):
        bx, by, bw, bh = 50 + i*30, 40 + i*10, 40, 40
        bcol = 0xFF00 # 不透明な赤 (A=15, R=15, G=0, B=0)
        hal.screen.rect(bx, by, bw, bh, bcol)

    # スプライトを合成
    hal.screen.blt(x, y, sprite, 0, 0, 32, 32)

if __name__ == "__main__":
    sprite = create_test_sprite(32, 32)
    # 60FPSでゲームループを開始
    hal.run(update, draw, fps=60)
