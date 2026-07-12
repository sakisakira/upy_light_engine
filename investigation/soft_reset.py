import serial
import time

try:
    with serial.Serial('COM4', 115200, timeout=1) as ser:
        print("Connected to COM4. Sending soft reset...")
        ser.write(b'\x03') # Ctrl-C
        time.sleep(0.5)
        ser.write(b'\x04') # Soft Reset
        time.sleep(0.5)
        print("Reset sent.")
except Exception as e:
    print(f"Error: {e}")
