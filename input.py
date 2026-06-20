import sys
from constants import *

if sys.implementation.name == 'micropython':
    from hal.input_micropython import set_key_mapping, init, button
else:
    from hal.input_cpython import set_key_mapping, init, button
