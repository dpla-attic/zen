# -- %< --
# From geo.py

import sys, urllib
import simplejson

from akara import logger
from akara.caching import cache

GEOLOOKUP_CACHE = cache('http://purl.org/com/zepheira/services/geolookup.json', expires=24*60*60)

def geolookup(place):
    #Is this check necessary?  Should the cache handle that?
    if isinstance(place, unicode):
        place = place.encode('utf-8')
    resp = GEOLOOKUP_CACHE.get(place=place)
    result = resp.read()
    try:
        latlong = simplejson.loads(result).itervalues().next()
        GEOCACHE[place] = latlong
        return latlong
    except ValueError:
        logger.debug("Not found: " + place)
        return None


#GEOLOCATION_SERVICE = 'http://os-content.zepheira.com:8880/geolookup.json'
#GEOLOOKUP = 'http://os-content.zepheira.com:8880/geolookup.json?place='

