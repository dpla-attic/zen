# -- %< --
# From geo.py

import sys, urllib
import simplejson

GEOLOCATION_SERVICE = 'http://os-content.zepheira.com:8880/geolookup.json'
GEOLOOKUP = 'http://os-content.zepheira.com:8880/geolookup.json?place='

GEOCACHE = {}

def geolookup(place):
    if isinstance(place, unicode):
        place = place.encode('utf-8')
    if place in GEOCACHE:
        return GEOCACHE[place]
    query = urllib.urlencode({'place' : place})
    url = GEOLOCATION_SERVICE + '?' + query
    response = urllib.urlopen(url)
    result = response.read()
    try:
        latlong = simplejson.loads(result).itervalues().next()
        GEOCACHE[place] = latlong
        return latlong
    except ValueError:
        print >> sys.stderr, "Not found:", place
        GEOCACHE[place] = None
        return None

