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

def _parse_single_track(mml, initial_tempo, initial_volume):
    mml = mml.lower()
    i = 0
    tempo = initial_tempo
    octave = 4
    default_length = 4
    volume = initial_volume
    wave_type = 0
    
    intro_notes = []
    loop_notes = []
    current_notes = intro_notes
    
    def get_num(default_val):
        nonlocal i
        start = i
        while i < len(mml) and mml[i].isdigit():
            i += 1
        if start == i:
            return default_val
        return int(mml[start:i])
        
    tied = False
    
    while i < len(mml):
        c = mml[i]
        i += 1
        
        if c in (' ', '\t', '\n', '\r'):
            continue
            
        elif c == '&':
            tied = True
            continue
            
        elif c == '$':
            current_notes = loop_notes
            continue
            
        elif c == '@':
            wave_type = get_num(wave_type)
        elif c == 't':
            tempo = get_num(tempo)
        elif c == 'o':
            octave = get_num(octave)
        elif c == 'l':
            default_length = get_num(default_length)
        elif c == 'v':
            volume = get_num(volume)
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
                
            freq_int = int(freq)
            duration_int = int(duration_ms)
            
            if tied and current_notes and current_notes[-1][0] == freq_int and (len(current_notes[-1]) < 4 or current_notes[-1][3] == wave_type):
                prev = current_notes.pop()
                prev_freq, prev_dur, prev_vol = prev[0], prev[1], prev[2]
                current_notes.append((prev_freq, prev_dur + duration_int, prev_vol, wave_type))
            else:
                current_notes.append((freq_int, duration_int, volume, wave_type))
                
            tied = False
            
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
                
            duration_int = int(duration_ms)
            
            if tied and current_notes and current_notes[-1][0] == 0:
                prev = current_notes.pop()
                prev_freq, prev_dur, prev_vol = prev[0], prev[1], prev[2]
                prev_wave = prev[3] if len(prev) > 3 else 0
                current_notes.append((prev_freq, prev_dur + duration_int, prev_vol, prev_wave))
            else:
                current_notes.append((0, duration_int, 0, wave_type))
                
            tied = False
            
    return intro_notes, loop_notes, tempo, volume

def parse_mml(mml):
    """
    Parses an MML string and returns (intro_tracks, loop_tracks).
    Tracks are separated by commas.
    Commands:
      Txxx: Tempo (BPM)
      Ox: Octave (0-8)
      Lxx: Default length
      Vxxx: Volume (0-100)
      @x: Wave type (0=Square, 1=Sawtooth, 2=Triangle, 3=Noise)
      $: Loop marker (notes after this will loop)
      CDEFGAB[#+-][x][.]: Note, optional sharp/flat, optional length, optional dot
      R[x][.]: Rest
      < >: Octave down/up
    """
    intro_tracks = []
    loop_tracks = []
    tempo = 120
    volume = 64
    
    parts = mml.split(',')
    for part in parts:
        intro_notes, loop_notes, tempo, volume = _parse_single_track(part, tempo, volume)
        intro_tracks.append(intro_notes)
        loop_tracks.append(loop_notes)
        
    return intro_tracks, loop_tracks

