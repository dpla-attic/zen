# -- %< --
# From geo.py

import sys, urllib

from amara.thirdparty import httplib2, json

from akara import logger
from akara import request
from akara.caching import cache

from zenlib.util import find_peer_service

GEOLOOKUP_URI = None

def setup():
    global GEOLOOKUP_URI, H
    GEOLOOKUP_URI = find_peer_service(request.environ, u'http://purl.org/com/zepheira/services/geolookup.json')
    H = httplib2.Http('/tmp/.cache')
    return

def geolookup(place):
    '''
    A convenience function to call the local/peer geolookup service.

    Can only be called from within an Akara module handler.  E.g. thefollowing sample module:
    
    -- %< --
from akara.services import simple_service
from zenlib.geo import geolookup

@simple_service("GET", "http://testing/report.get")
def s(place):
    return repr(geolookup('Superior,CO'))
    -- %< --
    Then test: curl -i "http://localhost:8880/s?place=Superior,CO"
    '''
    if not place:
        return None
    if isinstance(place, unicode):
        place = place.encode('utf-8')

    if not GEOLOOKUP_URI: setup()
    logger.debug('geolookup' + repr((place, GEOLOOKUP_URI)))
    resp, body = H.request(GEOLOOKUP_URI + '?place=' + urllib.quote(place))
    try:
        latlong = json.loads(body).itervalues().next()
        return latlong
    except (ValueError, StopIteration), e:
        logger.debug("Not found: " + repr(place))
        return None


GEOLOOKUP_CACHE = cache(
    'http://purl.org/com/zepheira/services/geolookup.json', expires=24*60*60)

def old_geolookup(place):
    if not place:
        return None
    if isinstance(place, unicode):
        place = place.encode('utf-8')
    resp = GEOLOOKUP_CACHE.get(place=place)
    result = resp.read()
    try:
        latlong = json.loads(result).itervalues().next()
        return latlong
    except (ValueError, StopIteration), e:
        logger.debug("Not found: " + repr(place))
        return None

