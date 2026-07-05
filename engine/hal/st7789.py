import machine
import utime as time

class ST7789:
    """
    Pure Python ST7789 SPI Display Driver for Cardputer (240x135)
    Optimized for high-speed framebuffer transfer.
    """
    def __init__(self, spi_id=1, baudrate=80000000, 
                 mosi=35, sck=36, cs=37, dc=34, rst=33, bl=38, 
                 width=240, height=135):
        import micropython
        self.width = width
        self.height = height
        
        # Hardware SPI initialization via C engine (DMA optimized)
        try:
            import _lightengine
            _lightengine.init_display(spi_id, baudrate, mosi, sck, cs, dc)
            self._le = _lightengine
        except ImportError:
            self._le = None
            print("WARNING: _lightengine not found, ST7789 will not work!")
        
        # Pin initialization (for RST and BL)
        self.rst = machine.Pin(rst, machine.Pin.OUT)
        self.bl = machine.Pin(bl, machine.Pin.OUT)
        
        # Set initial states
        self.bl(1) # Turn on backlight
        
        self.reset()
        self.init_display()
        
    def reset(self):
        """Hardware reset of the display"""
        self.rst(0)
        time.sleep_ms(50)
        self.rst(1)
        time.sleep_ms(50)
        
        self._buf4 = bytearray(4)
        
    def write_cmd(self, cmd):
        """Write a command byte"""
        if self._le:
            self._le.spi_write_cmd(cmd)
        
    def write_data(self, data):
        """Write data bytes"""
        if self._le:
            self._le.spi_write_data(data)
        
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
        
        self.write_cmd(0x2A)
        self._buf4[0] = x0 >> 8
        self._buf4[1] = x0 & 0xFF
        self._buf4[2] = x1 >> 8
        self._buf4[3] = x1 & 0xFF
        self.write_data(self._buf4)
        
        # Row address set
        self.write_cmd(0x2B)
        self._buf4[0] = y0 >> 8
        self._buf4[1] = y0 & 0xFF
        self._buf4[2] = y1 >> 8
        self._buf4[3] = y1 & 0xFF
        self.write_data(self._buf4)
        
        # Memory Write
        self.write_cmd(0x2C)
