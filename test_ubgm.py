import struct
import sys

with open('../motorcycle_cardputer/assets/title.ubgm', 'rb') as f:
    data = f.read()

length = len(data)
print(f'Length: {length}')

for ch in range(4):
    header = 16 + ch * 12
    if header + 12 <= length:
        ic = data[header] | (data[header+1] << 8)
        lc = data[header+2] | (data[header+3] << 8)
        io = data[header+4] | (data[header+5] << 8) | (data[header+6] << 16) | (data[header+7] << 24)
        lo = data[header+8] | (data[header+9] << 8) | (data[header+10] << 16) | (data[header+11] << 24)
        print(f'Track {ch}: ic={ic}, lc={lc}, io={io}, lo={lo}')
        
        if ic > 0:
            if io >= length or io + ic * 6 > length:
                print(f'  ERROR: intro invalid (io={io}, ic={ic}, length={length})')
                sys.exit(1)
        if lc > 0:
            if lo >= length or lo + lc * 6 > length:
                print(f'  ERROR: loop invalid (lo={lo}, lc={lc}, length={length})')
                sys.exit(1)
print('SUCCESS')
