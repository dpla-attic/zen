'''
Tests data augmentation methods at low level, not through Akara
'''

import re
import doctest

from zen import augmentation

def test_docstring():
    doctest.testmod(augmentation, verbose=True, raise_on_error=True)

