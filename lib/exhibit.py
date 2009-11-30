#akara.services
"""

"""

import re

import amara
from amara.lib.util import *
from amara.namespaces import AKARA_NAMESPACE

UNSUPPORTED_IN_EXHIBITKEY = re.compile('\W')

def fixup_keys(ejson):
    mod_list = []
    for k in ejson:
        new_k = UNSUPPORTED_IN_EXHIBITKEY.sub('_', k)
        if k != new_k: mod_list.append((k, new_k))
    
    for (k, new_k) in mod_list:
        ejson[new_k] = ejson[k]
        del ejson[k]
    return


def prep_simile(items, schema=None, strict=False):
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
            for key in schema_for_item:
                if key in item:
                    #result = pipeline_stage(schema_for_item[key], item[key]).next()
                    item[key] = pipeline_stage(schema_for_item[key], item[key])
    for item in remove_list:
        items.remove(item)
    return items


