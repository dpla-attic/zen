#!/usr/bin/env python
# encoding: utf-8
"""
Requires: geopy, simplejson, and feedparser

Copyright 2008-2009 Zepheira LLC
"""

#cofigure to set: ipgeo.db 

from __future__ import with_statement
import sys, re, os, time, sqlite3
import socket
import urllib2, urllib
import hashlib
import httplib
from datetime import datetime
from cStringIO import StringIO
from contextlib import closing

import amara
from amara import bindery
import simplejson
import feedparser
from geopy import geocoders

from akara.services import simple_service
from akara.util import status_response
from akara import response
from akara import logger


def state_lookup(s):
    result = US_STATES_GEO.xml_select(u'provinces/*[@abbr="%s"]'%s)
    return unicode(result[0]) if result else None


def ip2geo(addr):
    '''
    See http://hostip.info for more info on the service used
    '''
    rows = g_db.execute("select * from node where ip=?", (addr,))
    try:
        (ip, latlong, city, state, country, updated) = rows.next()
        logger.debug('Found in DB: ' + addr + ":" + latlong)
        state = state_lookup(state) or state
        return {'latlong': latlong, 'city': city, 'state': state, 'country': country}
    except StopIteration:
        pass

    logger.debug('Looking up geolocation for: ' + addr)
    request = "http://api.hostip.info/?ip=" + addr
    result = urllib2.urlopen(request).read()
    result = bindery.parse(result)
    info = result.HostipLookupResultSet.featureMember.Hostip
    try:
        longlat = unicode(info.ipLocation.PointProperty.Point.coordinates)
    except AttributeError:
        longlat = u''
    if longlat:
        long_, lat = longlat.split(',')
        latlong = u','.join((lat, long_))
        country = unicode(info.countryAbbrev)
        try:
            city, state = unicode(info.name).split(', ')
        except ValueError:
            city, state = unicode(info.name), u''
        if city.strip() == '(Unknown City?)': city = u''
    else:
        #Unknown
        latlong = country = city = state = u''
    state = state_lookup(state) or state
    #if USAGE_LIMIT_EXCEEDED: return None
    res = g_db.execute("insert into node values (?, ?, ?, ?, ?, ?)", (addr, latlong, city, state, country, datetime.now(),))
    g_db.commit()
    return {'latlong': latlong, 'city': city, 'state': state, 'country': country}


g_db = None

def check_initdb():
    global g_db
    if g_db is None:
        g_db = sqlite3.connect(DBFILE)
        try:
            g_db.execute("select count(*) from node")
        except sqlite3.OperationalError:
            # Create table
            g_db.execute('''create table node
            (ip text, latlong text, city text, state text, country text, updated timestamp)''')
            g_db.commit()
    return


#DBFILE = os.environ['ZEPHEIRA_AKARA_GEODBFILE']
#print >> sys.stderr, dict(AKARA_MODULE_CONFIG)
#print >> sys.stderr, AKARA_MODULE_CONFIG.server_root_relative('dbfile')
#DBFILE = AKARA.module_config.server_root_relative(AKARA_MODULE_CONFIG['dbfile'])
DBFILE = AKARA.module_config['dbfile']
#dbfile (ServerRoot)/path/to/dbfile
#print 'GRIPPO', DBFILE
#print >> sys.stderr, "DBFILE: ", DBFILE

SERVICE_ID = 'http://purl.org/com/zepheira/services/ipgeo.json'
@simple_service('GET', SERVICE_ID, 'ipgeo.json', 'application/json')
#def excel2json(body, ctype, **params):
def ipgeo_json(addr=None):
    '''
    Transform to return the geolocation of an IP address (or host name), if found
    
    Sample request:
    * curl "http://localhost:8880/ipgeo.json?addr=www.zepheira.com"
    '''
    #import pprint; pprint.pprint(environ)
    #import uuid
    addr = addr
    try:
        ipaddr = unicode(socket.gethostbyname(addr))
    except socket.gaierror:
        response.status = status_response(httplib.NOT_FOUND)
        return ''
    check_initdb()
    result = ip2geo(ipaddr)
    return simplejson.dumps({ipaddr: result}) if result else "{}"


#try:
#    geocache = simplejson.load(open(geocachejsfile))
#except IOError:
#    geocache = {}
GEOCODER = geocoders.Google(resource='maps')
geocache = {}

SERVICE_ID = 'http://purl.org/com/zepheira/services/geolookup.json'
@simple_service('GET', SERVICE_ID, 'geolookup.json', 'application/json')
def geolookup_json(place=None):
    '''
    Transform to return the latitude/longitude of a place name, if found
    
    Sample request:
    * curl "http://localhost:8880/geolookup.json?place=Superior,%20CO"
    '''
    geoquery = place
    #geoquery = "%s in %s, %s"%(address_line, city, state_name)
    if geoquery in geocache:
        latlong = geocache[geoquery]
    else:
        try:
            place, (lat, long_) = GEOCODER.geocode(geoquery)
            latlong = "%0.03f,%0.03f"%(lat, long_)
        except ValueError, urllib2.URLError:
            state = US_STATES_GEO.xml_select(u'provinces/*[@abbr="%s"]'%geoquery)
            if state:
                latlong = "%s,%s"%(unicode(state[0].lat), unicode(state[0].long))
            else:
                state = US_STATES_GEO.xml_select(u'provinces/*[.="%s"]'%geoquery)
                if state:
                    latlong = "%s,%s"%(unicode(state[0].lat), unicode(state[0].long))
                else:
                    latlong = None
                    response.status = status_response(httplib.NOT_FOUND)
                    return ''
        geocache[geoquery] = latlong
    return simplejson.dumps({geoquery: latlong}) if latlong else "{}"


geohashcache = {}

SERVICE_ID = 'http://purl.org/com/zepheira/services/geohash.json'
@simple_service('GET', SERVICE_ID, 'geohash.json', 'application/json')
def geohash_json(place=None):
    '''
    Transform to return the geohash of a place name, if found
    
    Sample request:
    * curl "http://localhost:8880/geohash.json?place=Superior,%20CO"
    '''
    geoquery = place[0]
    #geoquery = "%s in %s, %s"%(address_line, city, state_name)
    if geoquery in geohashcache:
        result = geohashcache[geoquery]
    else:
        query = urllib.urlencode({'q' : geoquery})
        url = 'http://geohash.org/?%s' % (query)
        with closing(urllib.urlopen(url)) as search_results:
            json = simplejson.loads(search_results.read())
        results = json['responseData']['results']
        return results[0]['url'].encode('utf-8') + '\n'

        try:
            place, (lat, long_) = GEOCODER.geocode(geoquery)
            latlong = "%0.03f,%0.03f"%(lat, long_)
        except ValueError, urllib2.URLError:
            state = US_STATES_GEO.xml_select(u'provinces/*[@abbr="%s"]'%geoquery)
            if state:
                latlong = "%s,%s"%(unicode(state[0].lat), unicode(state[0].long))
            else:
                state = US_STATES_GEO.xml_select(u'provinces/*[.="%s"]'%geoquery)
                if state:
                    latlong = "%s,%s"%(unicode(state[0].lat), unicode(state[0].long))
                else:
                    latlong = None
                    res = HTTPNotFound()
                    return res(environ, start_response)
        geocache[geoquery] = latlong
    return simplejson.dumps({geoquery: latlong}) if latlong else "{}"


US_STATES_GEO = bindery.parse("""<provinces>
    <state lat="61.3850" abbr="AK" long="-152.2683">Alaska</state>
    <state lat="32.7990" abbr="AL" long="-86.8073">Alabama</state>
    <state lat="34.9513" abbr="AR" long="-92.3809">Arkansas</state>
    <state lat="33.7712" abbr="AZ" long="-111.3877">Arizona</state>
    <state lat="36.1700" abbr="CA" long="-119.7462">California</state>
    <state lat="39.0646" abbr="CO" long="-105.3272">Colorado</state>
    <state lat="41.5834" abbr="CT" long="-72.7622">Connecticut</state>
    <state lat="39.3498" abbr="DE" long="-75.5148">Delaware</state>
    <state lat="27.8333" abbr="FL" long="-81.7170">Florida</state>
    <state lat="32.9866" abbr="GA" long="-83.6487">Georgia</state>
    <state lat="21.1098" abbr="HI" long="-157.5311">Hawaii</state>
    <state lat="42.0046" abbr="IA" long="-93.2140">Iowa</state>
    <state lat="44.2394" abbr="ID" long="-114.5103">Idaho</state>
    <state lat="40.3363" abbr="IL" long="-89.0022">Illinois</state>
    <state lat="39.8647" abbr="IN" long="-86.2604">Indiana</state>
    <state lat="38.5111" abbr="KS" long="-96.8005">Kansas</state>
    <state lat="37.6690" abbr="KY" long="-84.6514">Kentucky</state>
    <state lat="31.1801" abbr="LA" long="-91.8749">Louisiana</state>
    <state lat="42.2373" abbr="MA" long="-71.5314">Massachusetts</state>
    <state lat="39.0724" abbr="MD" long="-76.7902">Maryland</state>
    <state lat="44.6074" abbr="ME" long="-69.3977">Maine</state>
    <state lat="43.3504" abbr="MI" long="-84.5603">Michigan</state>
    <state lat="45.7326" abbr="MN" long="-93.9196">Minnesota</state>
    <state lat="38.4623" abbr="MO" long="-92.3020">Missouri</state>
    <state lat="32.7673" abbr="MS" long="-89.6812">Mississippi</state>
    <state lat="46.9048" abbr="MT" long="-110.3261">Montana</state>
    <state lat="35.6411" abbr="NC" long="-79.8431">North Carolina</state>
    <state lat="47.5362" abbr="ND" long="-99.7930">North Dakota</state>
    <state lat="41.1289" abbr="NE" long="-98.2883">Nebraska</state>
    <state lat="43.4108" abbr="NH" long="-71.5653">New Hampshire</state>
    <state lat="40.3140" abbr="NJ" long="-74.5089">New Jersey</state>
    <state lat="34.8375" abbr="NM" long="-106.2371">New Mexico</state>
    <state lat="38.4199" abbr="NV" long="-117.1219">Nevada</state>
    <state lat="42.1497" abbr="NY" long="-74.9384">New York</state>
    <state lat="40.3736" abbr="OH" long="-82.7755">Ohio</state>
    <state lat="35.5376" abbr="OK" long="-96.9247">Oklahoma</state>
    <state lat="44.5672" abbr="OR" long="-122.1269">Oregon</state>
    <state lat="40.5773" abbr="PA" long="-77.2640">Pennsylvania</state>
    <state lat="41.6772" abbr="RI" long="-71.5101">Rhode Island</state>
    <state lat="33.8191" abbr="SC" long="-80.9066">South Carolina</state>
    <state lat="44.2853" abbr="SD" long="-99.4632">South Dakota</state>
    <state lat="35.7449" abbr="TN" long="-86.7489">Tennessee</state>
    <state lat="31.1060" abbr="TX" long="-97.6475">Texas</state>
    <state lat="40.1135" abbr="UT" long="-111.8535">Utah</state>
    <state lat="37.7680" abbr="VA" long="-78.2057">Virginia</state>
    <state lat="44.0407" abbr="VT" long="-72.7093">Vermont</state>
    <state lat="47.3917" abbr="WA" long="-121.5708">Washington</state>
    <state lat="44.2563" abbr="WI" long="-89.6385">Wisconsin</state>
    <state lat="38.4680" abbr="WV" long="-80.9696">West Virginia</state>
    <state lat="42.7475" abbr="WY" long="-107.2085">Wyoming</state>
    <province lat="14.2417" abbr="AS" long="-170.7197"/>
    <province lat="38.8964" abbr="DC" long="-77.0262">District of Columbia</province>
    <province lat="14.8058" abbr="MP" long="145.5505"/>
    <province lat="18.2766" abbr="PR" long="-66.3350">Puerto Rico</province>
    <province lat="18.0001" abbr="VI" long="-64.8199">US Virgin Islands</province>
</provinces>
""")

#Generated by $ python -c "import sys, amara; states=amara.pushbind(sys.argv[1], u'state'); print dict([(unicode(s.abbr), unicode(s.name)) for s in states])" "http://cvs.4suite.org/viewcvs/*checkout*/4Suite/Ft/Server/Share/Data/us-states.xml?content-type=text%2Fplain"
#US_STATES = {u'WA': u'Washington', u'DE': u'Delaware', u'WI': u'Wisconsin', u'WV': u'West Virginia', u'HI': u'Hawaii', u'FL': u'Florida', u'WY': u'Wyoming', u'NH': u'New Hampshire', u'NJ': u'New Jersey', u'NM': u'New Mexico', u'TX': u'Texas', u'LA': u'Louisiana', u'NC': u'North Carolina', u'ND': u'North Dakota', u'NE': u'Nebraska', u'TN': u'Tennessee', u'NY': u'New York', u'PA': u'Pennsylvania', u'CA': u'California', u'NV': u'Nevada', u'VA': u'Virginia', u'CO': u'Colorado', u'AK': u'Alaska', u'AL': u'Alabama', u'AR': u'Arkansas', u'VT': u'Vermont', u'IL': u'Illinois', u'GA': u'Georgia', u'IN': u'Indiana', u'IA': u'Iowa', u'OK': u'Oklahoma', u'AZ': u'Arizona', u'ID': u'Idaho', u'CT': u'Connecticut', u'ME': u'Maine', u'MD': u'Maryland', u'MA': u'Massachusetts', u'OH': u'Ohio', u'UT': u'Utah', u'MO': u'Missouri', u'MN': u'Minnesota', u'MI': u'Michigan', u'RI': u'Rhode Island', u'KS': u'Kansas', u'MT': u'Montana', u'MS': u'Mississippi', u'SC': u'South Carolina', u'KY': u'Kentucky', u'OR': u'Oregon', u'SD': u'South Dakota'}

