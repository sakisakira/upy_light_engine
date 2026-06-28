class Sprite:
    """
    High-level logical view of an image (or part of an image) for rendering.
    Holds reference to an Image (texture), clipping region, and color parameters.
    """
    def __init__(self, image, u, v, w, h, colkey=0, tint=None):
        self.image = image
        self.u = int(u)
        self.v = int(v)
        self.w = int(w)
        self.h = int(h)
        self.colkey = colkey
        self.tint = tint
