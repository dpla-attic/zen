#!/usr/bin/env python
# encoding: utf-8
"""
geocoding.py

Copyright 2008-2011 Zepheira LLC

Services for geocoding

This file is part of the open source Zen project,
provided under the Apache 2.0 license.
See the files LICENSE and NOTICE for details.
Project home, documentation, distributions: http://foundry.zepheira.com/projects/zen

See:

 * http://purl.org/xml3k/akara
 * http://foundry.zepheira.com/projects/zen
 
= Defined REST entry points =


= Configuration =


Sample config:

class geocoding:
    cache_max_age = 86400
    geocoder = 'http://purl.org/com/zepheira/services/geocoders/local-geonames'
    geonames_dbfile = 'path/to/geonames.sqlite3'
    #e.g.: geonames_dbfile = Akara.ConfigRoot+'/caches/geonames.sqlite3'

Another:

class geocoding:
    cache_max_age = 86400
    geocoder = 'http://purl.org/com/zepheira/services/geocoders/geonames-service'
    geonames_service_user = 'myusername'

= Notes on security =

To-do


"""

#See also: [[http://us.pycon.org/2009/tutorials/schedule/1PM4/|"Working with Geographic Information Systems (GIS) in Python"]]
#geohash.org


#configure to set: ipgeo.db 


import sys, re, os, time, sqlite3
import socket
import urllib2, urllib
import hashlib
import httplib
from datetime import datetime
from cStringIO import StringIO

import amara
from amara import bindery
from amara.thirdparty import json

from akara.services import simple_service
from akara.util import status_response
from akara import response
from akara import logger
from akara import module_config

#from zen.latlong import latlong
from zen.geo import local_geonames, geonames_service

LOCAL_GEONAMES = 'http://purl.org/com/zepheira/services/geocoders/local-geonames'
GEONAMES_SERVICE = 'http://purl.org/com/zepheira/services/geocoders/geonames-service'

GEOCODER = module_config().get('geocoder', LOCAL_GEONAMES)

GEONAMES_PLUS_DBFILE = module_config().get('geonames_dbfile')
GEONAMES_SERVICE_USER = module_config().get('geonames_service_user')

# Specifies the default max-age of across-the-board lookups
CACHE_MAX_AGE = str(module_config().get('cache_max_age'))

geocoder_func = None
if GEOCODER == LOCAL_GEONAMES:
    geocoder_func = local_geonames(GEONAMES_PLUS_DBFILE, logger=logger)

if GEOCODER == GEONAMES_SERVICE:
    geocoder_func = geonames_service(user=GEONAMES_SERVICE_USER, logger=logger)


SERVICE_ID = 'http://purl.org/com/zepheira/services/geolookup.json'
@simple_service('GET', SERVICE_ID, 'geolookup.json', 'application/json')
def geolookup_json(place=None):
    '''
    Transform to return the latitude/longitude of a place name, if found
    
    Sample request:
    * curl "http://localhost:8880/geolookup.json?place=Superior,%20CO"
    * curl "http://localhost:8880/geolookup.json?place=1600%20Amphitheatre%20Parkway,%20Mountain%20View,%20VA,%2094043"
    * curl "http://localhost:8880/geolookup.json?place=Cerqueira%20C%C3%A9sar%2C%20Brazil"
    * curl "http://localhost:8880/geolookup.json?place=Georgia"
    '''
    geoquery = place.decode('utf-8')
    logger.debug("geolookup_json (using {0}): {1}".format(GEOCODER, repr(geoquery, )))
    result = geocoder_func(place)
    logger.debug("geolookup_json: " + repr(result))
    if CACHE_MAX_AGE: response.add_header("Cache-Control", "max-age="+CACHE_MAX_AGE)
    return json.dumps(result)

