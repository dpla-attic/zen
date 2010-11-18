import sys
import string
from nose.tools import raises

from amara.lib.util import mcompose, first_item
from amara.tools import atomtools
from amara.test.xslt import filesource, stringsource

from zen import exhibit

ENTRY_PIPELINE = {
    u"type": None,
    u"author": None,
    u"updated": None,
    u"title": None,
    u"alternate_link": first_item,
    u"summary": (first_item, exhibit.REQUIRE),
    u"content": None,
    u"published": None,
    u"id": None, #Note: ID is always automatically required
    u"label": None,
}

PIPELINES = { u'atom:entry': ENTRY_PIPELINE, u'atom:feed': None }

def test_pre_simile1():
    obj = atomtools.ejsonize(filesource('rfc4287-1-1-2.atom').source)
    obj[0][u'type'] = u'atom:entry'
    #del obj[0][u'id']
    #import pprint; pprint.pprint(obj, stream=sys.stderr)
    prepped = exhibit.prep(obj, schema=PIPELINES)
    #import pprint; pprint.pprint(prepped, stream=sys.stderr)
    return

    #assert iso_date is not None, reference_date  # could not be parsed
    #assert iso_date == reference_date, (iso_date, reference_date) # did not match

@raises(ValueError)
def test_pre_simile_missing_id():

    obj = atomtools.ejsonize(filesource('rfc4287-1-1-2.atom').source)
    obj[0][u'type'] = u'atom:entry'
    del obj[0][u'id']
    prepped = exhibit.prep(obj, schema=PIPELINES)
    return

@raises(ValueError)
def test_pre_simile_missing_field():
    obj = atomtools.ejsonize(filesource('rfc4287-1-1-2.atom').source)
    obj[0][u'type'] = u'atom:entry'
    #Add a requirement for a "spam" field
    epipelines_plus_spam = {u'spam': (first_item, exhibit.REQUIRE)}
    epipelines_plus_spam.update(ENTRY_PIPELINE)
    new_pipelines = { u'atom:entry': epipelines_plus_spam } #Don't bother with atom:feed; unused in test
    prepped = exhibit.prep(obj, schema=new_pipelines)
    return

