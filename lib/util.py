#Utilities

import hashlib
from wsgiref.util import request_uri

from amara.lib.iri import absolutize#, split_fragment, relativize, basejoin, join

from akara.util.moin import wiki_normalize

def sign_rulesheet(secret, rsheet):
    rsheet = wiki_normalize(rsheet)
    #Strip all whitespace from *end* of file since moin seems to
    rsheet = rsheet.rstrip()
    signed_parts = [
        '#', hashlib.sha1(secret + rsheet).hexdigest(), '\n', rsheet
        ]
    return ''.join(signed_parts)


from akara.util import find_peer_service, guess_self_uri #for backward compat
