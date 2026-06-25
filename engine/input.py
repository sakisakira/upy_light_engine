import sys
from engine.constants import *

if sys.platform == 'esp32':
    from engine.hal.input_micropython import set_key_mapping, init, button
else:
    from engine.hal.input_cpython import set_key_mapping, init, button
