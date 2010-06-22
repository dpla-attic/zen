'''
Tests MODS processing methods at low level, not through Akara
'''

import re
import doctest

from zenlib import mods

def test_docstring():
    doctest.testmod(mods, verbose=True, raise_on_error=True)

