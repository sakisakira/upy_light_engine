import machine
import time
import struct
import math

I2C_SDA = 8
I2C_SCL = 9
I2S_BCLK = 41
I2S_LRCK = 43
I2S_DATA = 42
ES8311_ADDR = 0x18

def init_es8311(i2c):
    def write_reg(reg, val):
        i2c.writeto_mem(ES8311_ADDR, reg, bytes([val]))
        
    print("ES8311 Init array from M5Unified...")
    # Exact init array from M5Unified.cpp for Cardputer ADV
    write_reg(0x00, 0x80)  # RESET/ CSM POWER ON
    write_reg(0x01, 0xB5)  # CLOCK_MANAGER/ MCLK=BCLK
    write_reg(0x02, 0x18)  # CLOCK_MANAGER/ MULT_PRE=3
    write_reg(0x0D, 0x01)  # SYSTEM/ Power up analog circuitry
    write_reg(0x12, 0x00)  # SYSTEM/ power-up DAC
    write_reg(0x13, 0x10)  # SYSTEM/ Enable output to HP drive
    write_reg(0x32, 0xBF)  # DAC/ DAC volume (0xBF == 0 dB)
    write_reg(0x37, 0x08)  # DAC/ Bypass DAC equalizer
    print("ES8311 Init complete.")

def play_tone():
    print("Init I2C...")
    i2c = machine.I2C(1, sda=machine.Pin(I2C_SDA), scl=machine.Pin(I2C_SCL), freq=100000)
    
    if ES8311_ADDR not in i2c.scan():
        print("ES8311 not found!")
        return
        
    init_es8311(i2c)
    
    print("Init I2S...")
    audio_out = machine.I2S(
        1,
        sck=machine.Pin(I2S_BCLK),
        ws=machine.Pin(I2S_LRCK),
        sd=machine.Pin(I2S_DATA),
        mode=machine.I2S.TX,
        bits=16,
        format=machine.I2S.STEREO,
        rate=44100,
        ibuf=4096
    )
    
    print("Generating sound...")
    samples = bytearray()
    for i in range(100): # 44100 / 441Hz approx
        val = int(8000 * math.sin(2 * math.pi * i / 100))
        samples += struct.pack("<hh", val, val)
        
    print("Playing...")
    start = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start) < 2000:
        audio_out.write(samples)
        
    print("Done.")
    audio_out.deinit()

if __name__ == "__main__":
    play_tone()
