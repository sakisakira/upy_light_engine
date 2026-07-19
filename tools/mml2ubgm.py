import sys
import os
import struct

# Make sure we can import the engine from the parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from engine import mml_parser

def compile_mml_to_ubgm(mml_str, out_path):
    intro_tracks, loop_tracks = mml_parser.parse_mml(mml_str)
    
    num_tracks = max(len(intro_tracks) if intro_tracks else 0, 
                     len(loop_tracks) if loop_tracks else 0)
                     
    if num_tracks == 0 or num_tracks > 4:
        raise ValueError(f"Unsupported number of tracks: {num_tracks}. Must be 1 to 4.")
    
    header = bytearray(64)
    # Magic (4), Version (1), Num Tracks (1)
    struct.pack_into('<4sBB', header, 0, b'UBGM', 1, num_tracks)
    
    data_blocks = bytearray()
    
    for ch in range(4):
        if ch >= num_tracks:
            continue
            
        intro = intro_tracks[ch] if intro_tracks and ch < len(intro_tracks) and intro_tracks[ch] else []
        loop = loop_tracks[ch] if loop_tracks and ch < len(loop_tracks) and loop_tracks[ch] else []
        
        ic = len(intro)
        lc = len(loop)
        
        # 64 is the size of the header (16 bytes global + 4 tracks * 12 bytes)
        io = 64 + len(data_blocks) if ic > 0 else 0
        for note in intro:
            f = int(note[0])
            d = int(note[1])
            v = int(note[2]) if len(note) > 2 else 64
            w = int(note[3]) if len(note) > 3 else 0
            data_blocks.extend(struct.pack('<HHBB', f, d, v, w))
            
        lo = 64 + len(data_blocks) if lc > 0 else 0
        for note in loop:
            f = int(note[0])
            d = int(note[1])
            v = int(note[2]) if len(note) > 2 else 64
            w = int(note[3]) if len(note) > 3 else 0
            data_blocks.extend(struct.pack('<HHBB', f, d, v, w))
            
        # Write metadata for this track
        # intro_count, loop_count, intro_offset, loop_offset
        struct.pack_into('<HHII', header, 16 + ch * 12, ic, lc, io, lo)
        
    with open(out_path, 'wb') as f:
        f.write(header)
        f.write(data_blocks)
    
    print(f"Compiled {out_path} ({num_tracks} tracks, {len(header) + len(data_blocks)} bytes)")

def parse_block_mml(text):
    """
    Parses a block-based .mml text file and converts it into a comma-separated
    MML string that mml_parser.parse_mml can understand.
    """
    intro_tracks = {0: [], 1: [], 2: [], 3: []}
    loop_tracks = {0: [], 1: [], 2: [], 3: []}
    target_tracks = intro_tracks
    has_loop = False
    
    current_ch = 0
    
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('['):
            continue
            
        if line == '$':
            target_tracks = loop_tracks
            has_loop = True
            continue
            
        if ':' in line:
            ch_str, mml_part = line.split(':', 1)
            try:
                current_ch = int(ch_str.strip())
            except ValueError:
                pass
            target_tracks[current_ch].append(mml_part.strip())
        else:
            # Multi-line continuation for the current channel
            target_tracks[current_ch].append(line)
            
    # Combine tracks into a single comma-separated string
    track_strs = []
    max_ch = -1
    for ch in range(4):
        if intro_tracks[ch] or loop_tracks[ch]:
            max_ch = ch
            
    for ch in range(max_ch + 1):
        t_str = " ".join(intro_tracks[ch])
        if has_loop:
            t_str += " $ " + " ".join(loop_tracks[ch])
        track_strs.append(t_str)
        
    return ",".join(track_strs)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python mml2ubgm.py <input.mml> <output.ubgm>")
        print("   or: python mml2ubgm.py -s \"MML_STRING\" <output.ubgm>")
        sys.exit(1)
        
    if sys.argv[1] == '-s':
        mml_str = sys.argv[2]
        out_path = sys.argv[3]
    else:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            text = f.read()
        
        # If it's a block format (contains newlines), parse it
        if '\n' in text and (':' in text or '[' in text):
            mml_str = parse_block_mml(text)
        else:
            mml_str = text
            
        out_path = sys.argv[2]
        
    compile_mml_to_ubgm(mml_str, out_path)
