#Utilities

import hashlib
from wsgiref.util import request_uri
from amara.lib.util import first_item
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


def requested_imt(environ):
    # Choose a preferred media type from the Accept header, using application/json as presumed
    # default, and stripping out any wildcard types and type parameters
    #
    # FIXME: Ideally, this should use the q values and pick the best media type, rather than
    # just picking the first non-wildcard type.  Perhaps: http://code.google.com/p/mimeparse/
    accepted_imts = []
    accept_header = environ.get('HTTP_ACCEPT')
    if accept_header:
        accepted_imts = [ type.split(';')[0].strip() for type in accept_header.split(',') ]
    accepted_imts.append('application/json')
    #logger.debug('accepted_imts: ' + repr(accepted_imts))
    imt = first_item(dropwhile(lambda x: '*' in x, accepted_imts))
    return imt


from akara.util import find_peer_service, guess_self_uri #for backward compat
