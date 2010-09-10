# -- %< --
# From geo.py

import sys, urllib

from amara.thirdparty import httplib2, json

from akara import logger
from akara.caching import cache

GEOLOOKUP_CACHE = cache(
    'http://purl.org/com/zepheira/services/geolookup.json', expires=24*60*60)

def geolookup(place):
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

geolookup.serviceid = u'http://purl.org/com/zepheira/zen/geolookup'

#GEOLOCATION_SERVICE = 'http://os-content.zepheira.com:8880/geolookup.json'
#GEOLOOKUP = 'http://os-content.zepheira.com:8880/geolookup.json?place='

