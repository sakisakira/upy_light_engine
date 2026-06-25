# mml_parser.py
# A lightweight Music Macro Language (MML) parser for upy_light_engine

BASE_FREQS = {
    'c': 261.63,
    'c#': 277.18, 'c+': 277.18, 'd-': 277.18,
    'd': 293.66,
    'd#': 311.13, 'd+': 311.13, 'e-': 311.13,
    'e': 329.63,
    'f': 349.23,
    'f#': 369.99, 'f+': 369.99, 'g-': 369.99,
    'g': 392.00,
    'g#': 415.30, 'g+': 415.30, 'a-': 415.30,
    'a': 440.00,
    'a#': 466.16, 'a+': 466.16, 'b-': 466.16,
    'b': 493.88
}

def parse_mml(mml):
    """
    Parses an MML string and returns a list of (frequency_hz, duration_ms) tuples.
    Commands:
      Txxx: Tempo (BPM)
      Ox: Octave (0-8)
      Lxx: Default length
      CDEFGAB[#+-][x][.]: Note, optional sharp/flat, optional length, optional dot
      R[x][.]: Rest
    """
    mml = mml.lower()
    i = 0
    tempo = 120
    octave = 4
    default_length = 4
    
    notes = []
    
    def get_num(default_val):
        nonlocal i
        start = i
        while i < len(mml) and mml[i].isdigit():
            i += 1
        if start == i:
            return default_val
        return int(mml[start:i])
        
    while i < len(mml):
        c = mml[i]
        i += 1
        
        if c in (' ', '\t', '\n', '\r'):
            continue
            
        elif c == 't':
            tempo = get_num(tempo)
        elif c == 'o':
            octave = get_num(octave)
        elif c == 'l':
            default_length = get_num(default_length)
        elif c == '<':
            octave = max(0, octave - 1)
        elif c == '>':
            octave = min(8, octave + 1)
            
        elif c in 'cdefgab':
            note = c
            if i < len(mml) and mml[i] in ('#', '+', '-'):
                note += mml[i]
                i += 1
            length = get_num(default_length)
            
            dotted = False
            if i < len(mml) and mml[i] == '.':
                dotted = True
                i += 1
                
            # calculate freq
            base_f = BASE_FREQS.get(note, 0)
            freq = base_f * (2 ** (octave - 4))
            
            # calculate duration
            quarter_ms = 60000.0 / tempo
            duration_ms = quarter_ms * (4.0 / length)
            if dotted:
                duration_ms *= 1.5
                
            notes.append((int(freq), int(duration_ms)))
            
        elif c == 'r':
            length = get_num(default_length)
            dotted = False
            if i < len(mml) and mml[i] == '.':
                dotted = True
                i += 1
                
            quarter_ms = 60000.0 / tempo
            duration_ms = quarter_ms * (4.0 / length)
            if dotted:
                duration_ms *= 1.5
                
            notes.append((0, int(duration_ms)))
            
    return notes
