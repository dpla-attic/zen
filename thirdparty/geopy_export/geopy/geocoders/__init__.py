#from geopy.geocoders_old import *

GEOCODERS = {}

def register(geocoder_name, cls):
    GEOCODERS[geocoder_name] = cls
    return


def lookup(geocoder_name):
    '''
    Get a Geocoder class given its registered name
    '''
    return GEOCODERS[geocoder_name]


def get_geocoder(geocoder_name, **kwargs):
    '''
    Get a Geocoder instance given its registered name, and initializer params
    '''
    return GEOCODERS[geocoder_name](**kwargs)


#The default geocoders self-register upon import
import geonames
import google
import yahoo
import wiki_semantic

#from google import Google
# TODO, switch geocoders to the new ones in this directory after testing

from geopy.geocoders.bing import Bing
from geopy.geocoders.google import Google
from geopy.geocoders.dot_us import GeocoderDotUS
from geopy.geocoders.geonames import GeoNames
from geopy.geocoders.wiki_gis import MediaWiki
from geopy.geocoders.wiki_semantic import SemanticMediaWiki
from geopy.geocoders.yahoo import Yahoo

