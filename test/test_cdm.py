import sys
from nose.tools import raises

from amara.test import file_finder
from amara.lib import iri
from amara.test.xslt import filesource, stringsource
from zen.contentdm import read_contentdm

FILE = file_finder(__file__)

def test_cdm1():
    print >> sys.stderr, FILE('data/cdm1.html')
    toppage = iri.os_path_to_uri(FILE('data/cdm1.html'))
    results = read_contentdm(toppage + '?', collection='/jthom', limit=1)
    #read_contentdm(toppage, collection='/jthom', limit=None)
    header = results.next()
    EXPECTED1 = {}
    assert header['basequeryurl'].startswith(toppage), (header, )
    item = results.next()
    EXPECTED2 = {}
    assert item == EXPECTED2, (item, EXPECTED2)
    #import pprint; pprint.pprint(result, stream=sys.stderr)
    return

    #assert iso_date is not None, reference_date  # could not be parsed
    #assert iso_date == reference_date, (iso_date, reference_date) # did not match

