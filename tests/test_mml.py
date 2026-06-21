import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import mml_parser

class TestMMLParser(unittest.TestCase):
    def test_basic_notes(self):
        notes = mml_parser.parse_mml("T120 O4 C4 D4")
        # tempo 120 = 500ms per quarter note
        # O4 C = 261.63, D = 293.66
        self.assertEqual(len(notes), 2)
        
        freq_c, dur_c = notes[0]
        self.assertEqual(freq_c, 261)
        self.assertEqual(dur_c, 500)
        
        freq_d, dur_d = notes[1]
        self.assertEqual(freq_d, 293)
        self.assertEqual(dur_d, 500)
        
    def test_octave_shift(self):
        notes = mml_parser.parse_mml("O4 C4 > C4 < C4")
        self.assertEqual(len(notes), 3)
        self.assertEqual(notes[0][0], 261)  # O4
        self.assertEqual(notes[1][0], 523)  # O5
        self.assertEqual(notes[2][0], 261)  # O4
        
    def test_length_and_dots(self):
        notes = mml_parser.parse_mml("T120 L8 C C.")
        # L8 = 250ms
        # C. = 250 * 1.5 = 375ms
        self.assertEqual(len(notes), 2)
        self.assertEqual(notes[0][1], 250)
        self.assertEqual(notes[1][1], 375)
        
    def test_rest(self):
        notes = mml_parser.parse_mml("T120 R4 R8.")
        self.assertEqual(len(notes), 2)
        self.assertEqual(notes[0][0], 0)
        self.assertEqual(notes[0][1], 500)
        self.assertEqual(notes[1][0], 0)
        self.assertEqual(notes[1][1], int(250 * 1.5))

if __name__ == '__main__':
    unittest.main()
