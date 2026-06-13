import sys

if sys.implementation.name == 'micropython':
    from hal_micropython import *
else:
    from hal_cpython import *
