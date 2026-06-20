import machine
import time

I2C_ADDR = 0x34

def main():
    print("Initializing I2C...")
    # Cardputer ADV I2C pins: SDA=8, SCL=9
    try:
        i2c = machine.I2C(0, scl=machine.Pin(9), sda=machine.Pin(8), freq=400000)
    except Exception as e:
        print("I2C initialization failed:", e)
        return
        
    devices = i2c.scan()
    print("I2C Scan:", [hex(d) for d in devices])
    if I2C_ADDR not in devices:
        print(f"TCA8418 not found at {hex(I2C_ADDR)}!")
        return

    print("TCA8418 found! Configuring...")
    
    # Register 0x01: CFG (Enable KE_IEN for key events)
    i2c.writeto_mem(I2C_ADDR, 0x01, b'\x01')
    
    # Registers 0x1D to 0x1F: KP_GPIO (Set all pins to keypad matrix)
    i2c.writeto_mem(I2C_ADDR, 0x1D, b'\xFF') # Rows 0-7
    i2c.writeto_mem(I2C_ADDR, 0x1E, b'\xFF') # Cols 0-7
    i2c.writeto_mem(I2C_ADDR, 0x1F, b'\xFF') # Cols 8-9 (only lowest 2 bits are valid but writing FF is fine)
    
    # Read back CFG to verify
    cfg = i2c.readfrom_mem(I2C_ADDR, 0x01, 1)[0]
    print(f"CFG Register: {hex(cfg)}")

    print("==================================================")
    print("Ready! Press keys on the Cardputer ADV keyboard.")
    print("Press Ctrl+C in REPL to stop.")
    print("==================================================")
    
    try:
        while True:
            # KEY_LCK_EC (0x03) holds the number of events in the FIFO (bits 3:0)
            ec_data = i2c.readfrom_mem(I2C_ADDR, 0x03, 1)
            event_count = ec_data[0] & 0x0F
            
            if event_count > 0:
                for _ in range(event_count):
                    # KEY_EVENT_A (0x04) is the FIFO
                    key_event = i2c.readfrom_mem(I2C_ADDR, 0x04, 1)[0]
                    # Bit 7 indicates Pressed (1) or Released (0)
                    pressed = (key_event & 0x80) != 0
                    keycode = key_event & 0x7F
                    
                    if keycode > 0:
                        row = (keycode - 1) // 10
                        col = (keycode - 1) % 10
                        action = "Pressed " if pressed else "Released"
                        print(f"{action}: Keycode={keycode:03d}  -->  Row={row}, Col={col}")
                        
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("Test stopped by user.")

if __name__ == '__main__':
    main()
