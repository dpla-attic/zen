#Utilities

import hashlib
from wsgiref.util import request_uri

from amara.lib.iri import absolutize#, split_fragment, relativize, basejoin, join

from akara.util.moin import wiki_normalize

def sign_rulesheet(secret, rsheet):
    rsheet = wiki_normalize(rsheet)
    signed_parts = [
        '#', hashlib.sha1(secret + rsheet).hexdigest(), '\n', rsheet
        ]
    return ''.join(signed_parts)


def find_peer_service(environ, peer_id):
    '''
    Fing a peer service endpoint, by ID, mounted on this same Akara instance
    
    Must be caled from a running akara service, and it is highly recommended to call
    at the top of service functions, or at least before the request environ has been manipulated
    '''
    from amara.lib.iri import absolutize, join
    from akara import request
    from akara.registry import _current_registry
    serverbase = guess_self_uri(environ)
    for (path, s) in _current_registry._registered_services.iteritems():
        if s.ident == peer_id:
            return join(serverbase, '..', path)
    return None

def guess_self_uri(environ):
    return absolutize(environ['SCRIPT_NAME'].rstrip('/'), request_uri(environ, include_query=False))

