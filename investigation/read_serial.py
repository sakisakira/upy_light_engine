import serial
import time
import sys

def main():
    print("Connecting to COM4...")
    try:
        ser = serial.Serial('COM4', 115200, timeout=1)
    except Exception as e:
        print(f"Failed to open COM4: {e}")
        return

    # Trigger hard reset (ESP32)
    ser.setDTR(False)
    ser.setRTS(True)
    time.sleep(0.1)
    ser.setDTR(True)
    ser.setRTS(False)
    time.sleep(0.1)
    
    print("Listening to Cardputer output...")
    start = time.time()
    while time.time() - start < 15:
        try:
            line = ser.readline()
            if line:
                print(line.decode('utf-8', errors='replace').rstrip('\r\n'))
        except Exception as e:
            print(f"Serial read error: {e}")
            break
            
    ser.close()

if __name__ == "__main__":
    main()
