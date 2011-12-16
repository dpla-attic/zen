#zen.akamod

#Some helper classes for accessing local Zen/Akara services

from akara import logger
from akara import request
from akara.caching import cache
from akara import global_config
from akara.util import find_peer_service

class geolookup_service(object):
    '''
    Convenience for calling the local/peer geolookup service.

    Can only be called from within an Akara module handler.  E.g. the following sample module:
    
    -- %< --
from akara.services import simple_service
from zenlib.akamod import geolookup_service

geolookup = geolookup_service()

@simple_service("GET", "http://testing/report.get")
def s(place):
    return repr(geolookup('Superior,CO'))
    -- %< --

    Then test: curl -i "http://localhost:8880/s?place=Superior,CO"
    '''
    def __init__(self):
        self.GEOLOOKUP_URI = find_peer_service(u'http://purl.org/com/zepheira/services/geolookup.json')
        self.H = httplib2.Http('/tmp/.cache')
        return

    def __call__(self, place):
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


#GEOLOOKUP_CACHE = cache(
#    'http://purl.org/com/zepheira/services/geolookup.json', expires=24*60*60)


