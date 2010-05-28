#zenlib.exhibit
"""

"""

import re

import amara
from amara.lib.util import pipeline_stage
from amara.lib.util import mcompose, first_item

UNSUPPORTED_IN_EXHIBITKEY = re.compile('\W')

def fixup(ejson):
    fixup_keys(ejson)
    for k, val in ejson.items():
        if not val: del ejson[k]
    return


def fixup_keys(ejson):
    #Cannot use for k in ejson because we're mutating as we go
    for k in ejson.keys():
        new_k = UNSUPPORTED_IN_EXHIBITKEY.sub('_', k)
        if k != new_k:
            ejson[new_k] = ejson[k]
            del ejson[k]
    return


REQUIRE = lambda x: x

def prep(items, schema=None, strict=False):
    '''
    Prep a raw JSON set of items so it's more useful for simile
    
    schema is a description in code of the expectations for items, including
    descriptions to be applied to keys or values

    import string
    from amara.lib.util import mcompose, first_item
    from zenlib import exhibit

    PIPELINES = { u'atom:entry': {
        u"type": None,
        u"author": None,
        u"updated": None,
        #u"title": mcompose(first_item, string.strip),
        u"title": None,
        u"alternate_link": first_item,
        u"summary": (first_item, exhibit.REQUIRE),
        u"content": None,
        u"published": None,
        u"id": None, #Note: ID is always automatically required
        u"label": None,
    }, u'atom:feed': None }
    prepped = exhibit.prep(obj, schema=PIPELINES)
    '''
    remove_list = []
    for item in items:
        #print item
        if not u'id' in item:
            raise ValueError('Missing ID')
        if schema:
            match = schema.get(first_item(item.get(u'type')))
            if strict and match is None:
                remove_list.append(item)
                continue
            schema_for_item = match or {}
            #print schema_for_item
            for key in schema_for_item.keys():
                #Extract the unit transforms for the entry key and entry value
                if isinstance(schema_for_item[key], tuple):
                    value_unit, key_unit = schema_for_item[key]
                else:
                    value_unit, key_unit = schema_for_item[key], None
                #import sys; print >> sys.stderr, (key, value_unit, key_unit)
                if key_unit and key_unit is REQUIRE:
                    if key not in item:
                        raise ValueError('Missing required field: %s'%key)
                if key in item:
                    #result = pipeline_stage(schema_for_item[key], item[key]).next()
                    value = pipeline_stage(value_unit, item[key])
                    #FIXME: Now supports either REQUIRE *or* transformation, and not both. Maybe make a 3-tuple
                    if key_unit and key_unit is not REQUIRE:
                        new_key = pipeline_stage(key_unit, key)
                        del item[key]
                        key = new_key
                    item[key] = value
    for item in remove_list:
        items.remove(item)
    return items

