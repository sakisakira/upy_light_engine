import engine.framebuffer as fb
import engine.input as input
import engine.sound as sound
from engine.image import Image
from engine.font import Font
class ColorPalette:
    MaxColors = 100
    TitleBg = 0
    TitleTextFg = 0
    TitleTextBg = 0
    DaySky = 0
    NightSky = 0
    StatusBg = 0
    StatusFg = 0
    Star = 0
    DayMountain = 0
    NightMountain = 0
    DayCloud = 0
    NightCloud = 0
    Ground0 = 0
    Ground1 = 0
    GroundSurface = 0
    GroundGoal = 0
    ResultBg = 0
    ResultTextBg = 0
    ResultTextFg = 0
    
    def __init__(self, paths_w_gray, paths):
        ColorPalette.TitleBg       = fb.color(0x4d, 0x65, 0xb4)
        ColorPalette.TitleTextFg   = fb.color(0xf6, 0x81, 0x81)
        ColorPalette.TitleTextBg   = fb.color(0xc3, 0x24, 0x54)
        ColorPalette.DaySky        = fb.color(0x4f, 0xef, 0xff)
        ColorPalette.NightSky      = fb.color(0x19, 0x19, 0x4f)
        ColorPalette.StatusBg      = fb.color(0xa7, 0xfb, 0xff)
        ColorPalette.StatusFg      = fb.color(0xd2, 0x5e, 0x7f)
        ColorPalette.Star          = fb.color(0xed, 0xf3, 0xba)
        ColorPalette.DayMountain   = fb.color(0x42, 0xa5, 0x81)
        ColorPalette.NightMountain = fb.color(0x3e, 0x67, 0x58)
        ColorPalette.DayCloud      = fb.color(0xd3, 0xe3, 0xf2)
        ColorPalette.NightCloud    = fb.color(0x83, 0x90, 0x9f)
        ColorPalette.Ground0       = fb.color(0xc7, 0xb2, 0x72)
        ColorPalette.Ground1       = fb.color(0x8f, 0x73, 0x20)
        ColorPalette.GroundSurface = fb.color(0xaa, 0xca, 0x64)
        ColorPalette.GroundGoal    = fb.color(0xff, 0xff, 0xc0)
        ColorPalette.ResultBg      = fb.color(0x95, 0xb2, 0xff)
        ColorPalette.ResultTextBg  = fb.color(0x8f, 0xf8, 0xe2)
        ColorPalette.ResultTextFg  = fb.color(0x4d, 0x65, 0xb4)

    def gray_converter(self):
        return None
