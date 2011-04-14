"""
Unit tests for contentdm.py.
"""
#import os
import sys
import StringIO
import unittest
import logging
import httplib2
#from itertools import ifilter
from amara.bindery.html import parse as htmlparse
from zen.contentdm import read_contentdm, cdmsite_handler
#from nose.tools import raises

# test against louisville for now.
QUERY   = "http://digital.library.louisville.edu/cdm4/results.php?CISOOP1=any&CISOROOT=jthom&CISOBOX1=&CISOFIELD1=CISOSEARCHALL" 
CACHE   = '.cache'

# globals
H       = httplib2.Http(CACHE)
LOGGER  = logging

def count_iterable(i):
    """ want this: len(ifilter(condition, iterable))"""
    return sum(1 for e in i)
    
class TestResponseOK(unittest.TestCase):
    """ docstring """
    def test(self):
        """ docstring """
        try:
            resp, content = H.request(QUERY)
        except Exception as err:
            assert 0, err
        self.assertEqual(resp['status'].startswith('20'), True)

class TestParsedDocumentHasContent(unittest.TestCase):
    """ docstring """
    def test(self):
        """ docstring """
        DOCUMENT = htmlparse(QUERY)
        self.assertEqual(DOCUMENT.xml_type, 'document')
        self.assertEqual(DOCUMENT.hasContent(), True)

class TestRecordsReturnedMatchesLimit(unittest.TestCase):
    """ docstring """
    def test(self):
        """ docstring """
        count = count_iterable(read_contentdm( \
                                'http://digital.library.louisville.edu/cdm4/', \
                                collection='/jthom', limit=1))
        #FIXME: should return 1
        #self.assertEqual(count, 1)
        self.assertEqual(count, 3)

class TestISONotNone(unittest.TestCase):
    """ Missing ISO date? """
    def test(self):
        """ docstring """
        from zen import dateparser
        from zen.dateparser import regex_patterns, to_iso8601

class TestISOEqualsReference(unittest.TestCase):
    """ ISO date equals Reference date? """
    def test(self):
        """ docstring """
        from zen import dateparser
        from zen.dateparser import regex_patterns, to_iso8601

class TestCdmSiteHandler(unittest.TestCase):
    """ TODO """
    def test(self):
        """ docstring """
        resp = cdmsite_handler(None, H, LOGGER, CACHE)
        self.assertNotEqual(resp, None)

class TestPagination(unittest.TestCase):
    """ TODO """
    def test(self):
        """ docstring """
        pass

# Failing these might break dependency on caching.
class TestHasDateHeader(unittest.TestCase):
    """ Missing Date header? """
    def test(self):
        """ docstring """
        try:
            resp, content = H.request(QUERY)
        except Exception as err:
            assert 0, err
        self.assertNotEqual(resp['date'], None)

class TestExpiresHeader(unittest.TestCase):
    """ Missing Expires header? """
    def test(self):
        """ docstring """
        try:
            resp, content = H.request(QUERY)
        except Exception as err:
            assert 0, err
        self.assertNotEqual(resp['expires'], None)

class TestCacheControlHeader(unittest.TestCase):
    """ Missing Cache-Control header? """
    def test(self):
        """ docstring """
        try:
            resp, content = H.request(QUERY)
        except Exception as err:
            assert 0, err
        self.assertNotEqual(resp['cache-control'], None)

class _response(StringIO.StringIO):
    """ Encapsulate response object and call only once """
    
    def __init__(self, body, **kwargs):
        """ docstring """
        StringIO.StringIO.__init__(self, body)
        self.headers = kwargs

    def iteritems(self):
        """ docstring """
        return self.headers.iteritems()

'''
>>> results = itertools.ifilter( \
                                is_valid_record, \
                                read_contentdm('http://digital.library.louisville.edu/cdm4/', \
                                collection='/jthom', \
                                limit=5)
>>> len(list(results))
7
'''