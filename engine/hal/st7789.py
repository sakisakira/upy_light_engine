import machine
import time

class ST7789:
    """
    Pure Python ST7789 SPI Display Driver for Cardputer (240x135)
    Optimized for high-speed framebuffer transfer.
    """
    def __init__(self, spi_id=1, baudrate=40000000, 
                 mosi=35, sck=36, cs=37, dc=34, rst=33, bl=38, 
                 width=240, height=135):
        import micropython
        self.width = width
        self.height = height
        
        # Hardware SPI initialization
        self.spi = machine.SPI(spi_id, baudrate=baudrate, 
                               sck=machine.Pin(sck), mosi=machine.Pin(mosi))
        
        # Pin initialization
        self.cs = machine.Pin(cs, machine.Pin.OUT)
        self.dc = machine.Pin(dc, machine.Pin.OUT)
        self.rst = machine.Pin(rst, machine.Pin.OUT)
        self.bl = machine.Pin(bl, machine.Pin.OUT)
        
        # Set initial states
        self.cs(1)
        self.bl(1) # Turn on backlight
        
        self.reset()
        self.init_display()
        
    def reset(self):
        """Hardware reset of the display"""
        self.rst(0)
        time.sleep_ms(50)
        self.rst(1)
        time.sleep_ms(50)
        
    def write_cmd(self, cmd):
        """Write a command byte"""
        self.cs(0)
        self.dc(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)
        
    def write_data(self, data):
        """Write data bytes"""
        self.cs(0)
        self.dc(1)
        self.spi.write(data)
        self.cs(1)
        
    def init_display(self):
        """Initialize the ST7789 registers"""
        self.write_cmd(0x11) # Sleep out
        time.sleep_ms(120)
        
        # Memory Data Access Control
        self.write_cmd(0x36)
        # 0x70 = MX | MV | RGB (Landscape mode)
        self.write_data(bytearray([0x70]))
        
        # Interface Pixel Format
        self.write_cmd(0x3A)
        self.write_data(bytearray([0x05])) # 16-bit/pixel (RGB565)
        
        # Porch Setting
        self.write_cmd(0xB2)
        self.write_data(bytearray([0x0B, 0x0B, 0x00, 0x33, 0x33]))
        
        # Gate Control
        self.write_cmd(0xB7)
        self.write_data(bytearray([0x35]))
        
        # VCOM Setting
        self.write_cmd(0xBB)
        self.write_data(bytearray([0x19]))
        
        # LCM Control
        self.write_cmd(0xC0)
        self.write_data(bytearray([0x2C]))
        
        # VDV and VRH Command Enable
        self.write_cmd(0xC2)
        self.write_data(bytearray([0x01]))
        
        # VRH Set
        self.write_cmd(0xC3)
        self.write_data(bytearray([0x12]))
        
        # VDV Set
        self.write_cmd(0xC4)
        self.write_data(bytearray([0x20]))
        
        # Frame Rate Control
        self.write_cmd(0xC6)
        self.write_data(bytearray([0x0F]))
        
        # Power Control 1
        self.write_cmd(0xD0)
        self.write_data(bytearray([0xA4, 0xA1]))
        
        # Positive Voltage Gamma Control
        self.write_cmd(0xE0)
        self.write_data(bytearray([0xD0, 0x04, 0x0D, 0x11, 0x13, 0x2B, 0x3F, 0x54, 0x4C, 0x18, 0x0D, 0x0B, 0x1F, 0x23]))
        
        # Negative Voltage Gamma Control
        self.write_cmd(0xE1)
        self.write_data(bytearray([0xD0, 0x04, 0x0C, 0x11, 0x13, 0x2C, 0x3F, 0x44, 0x51, 0x2F, 0x1F, 0x1F, 0x20, 0x23]))
        
        # Inversion On (Some panels need 0x20 INVOFF instead)
        self.write_cmd(0x21)
        
        # Display On
        self.write_cmd(0x29)
        time.sleep_ms(100)

    def set_window(self, x0, y0, x1, y1):
        """Set the drawing window. Includes hardware-specific offsets."""
        # ST7789 1.14" 240x135 Landscape Offsets
        x0 += 40
        x1 += 40
        y0 += 53
        y1 += 53
        
        self.write_cmd(0x2A) # Column Address Set
        self.write_data(bytearray([x0 >> 8, x0 & 0xFF, x1 >> 8, x1 & 0xFF]))
        
        self.write_cmd(0x2B) # Row Address Set
        self.write_data(bytearray([y0 >> 8, y0 & 0xFF, y1 >> 8, y1 & 0xFF]))
        
        self.write_cmd(0x2C) # Memory Write

    def show(self, buffer):
        """Fast transfer of the INDEX8 framebuffer to the display using colors565 palette"""
        from ..palette import colors565
        
        self.set_window(0, 0, self.width - 1, self.height - 1)
        
        self.cs(0)
        self.dc(1)
        
        # Line buffer for 16-bit pixels (width * 2 bytes)
        # Allocate once per show() is very fast
        line_buf = bytearray(self.width * 2)
        
        self._send_lines_viper(buffer, line_buf, colors565, self.width, self.height, self.spi.write)
        
        self.cs(1)
        
    @micropython.viper
    def _send_lines_viper(self, idx_buf, line_buf, pal_buf, w: int, h: int, spi_write):
        src = ptr8(idx_buf)
        dst = ptr8(line_buf)
        pal = ptr8(pal_buf)
        
        idx = 0
        for y in range(h):
            for x in range(w):
                c = src[idx]
                pal_idx = c << 1
                dst[x << 1] = pal[pal_idx]
                dst[(x << 1) + 1] = pal[pal_idx + 1]
                idx += 1
            spi_write(line_buf)
