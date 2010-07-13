'''
Use GeoNames.org Web services for geolocation http://www.geonames.org/export/ws-overview.html

Uses the "search" endpoint: http://www.geonames.org/export/geonames-search.html
'''

import logging

from urllib import urlencode
from urllib2 import urlopen

import xml
from xml.parsers.expat import ExpatError

from geopy.geocoders.base import Geocoder
from geopy import Point, Location, util

try:
    from akara import logger
except ImportError:
    logger = None

try:
    import json as simplejson
except ImportError:
    try:
        import simplejson
    except ImportError:
        try:
            from django.utils import simplejson
        except ImportError:
            import sys
            print >> sys.stderr, "simplejson was not found. " \
                  "Geocoders relying on JSON parsing will not work."


class GeoNames(Geocoder):
    def __init__(self, format_string='%s', output_format='xml', user=None):
        self.format_string = format_string
        self.output_format = output_format
        self.user = user or ''

    @property
    def url(self):
        domain = "ws.geonames.org"
        if self.user:
            domain = "ba-ws.geonames.net"
            user = 'username=%s&'%self.user
            logger.debug('Using Commercial GeoNames service (ba-ws.geonames.org). Username: ' + self.user)
        output_format = self.output_format.lower()
        append_formats = {'json': 'JSON'}
        resource = "search" + append_formats.get(output_format, '')
        return "http://%(domain)s/%(resource)s?%(user)s%%s" % locals()

    def geocode(self, string, exactly_one=True):
        params = {'q': string}
        url = self.url % urlencode(params)
        #import sys; print >> sys.stderr, (url,)
        return self.geocode_url(url, exactly_one)

    def geocode_url(self, url, exactly_one=True):
        page = urlopen(url)
        dispatch = getattr(self, 'parse_' + self.output_format)
        return dispatch(page, exactly_one)

    def parse_json(self, page, exactly_one):
        if not isinstance(page, basestring):
            page = util.decode_page(page)
        json = simplejson.loads(page)
        codes = json.get('postalCodes', [])
        
        if exactly_one and len(codes) != 1:
            raise ValueError("Didn't find exactly one code! " \
                             "(Found %d.)" % len(codes))
        
        def parse_code(code):
            place = util.join_filter(", ", [code.get('placeName'),
                                             code.get('countryCode')])
            location = util.join_filter(" ", [place,
                                               code.get('postalCode')]) or None
            latitude = code.get('lat')
            longitude = code.get('lng')
            latitude = latitude and float(latitude)
            longitude = longitude and float(longitude)
            return (location, (latitude, longitude))

        if exactly_one:
            return parse_code(codes[0])
        else:
            return (parse_code(code) for code in codes)

    def parse_xml(self, page, exactly_one):
        if not isinstance(page, basestring):
            page = util.decode_page(page)
        doc = xml.dom.minidom.parseString(page)
        codes = doc.getElementsByTagName('geoname')
        
        if exactly_one and len(codes) != 1:
            raise ValueError("Didn't find exactly one geoname! " \
                             "(Found %d.)" % len(codes))

        def parse_code(code):
            place_name = util.get_first_text(code, 'name')
            country_code = util.get_first_text(code, 'countryCode')
            postal_code = util.get_first_text(code, 'postalcode')
            place = util.join_filter(", ", [place_name, country_code])
            location = util.join_filter(" ", [place, postal_code]) or None
            latitude = util.get_first_text(code, 'lat') or None
            longitude = util.get_first_text(code, 'lng') or None
            latitude = latitude and float(latitude)
            longitude = longitude and float(longitude)
            return (location, (latitude, longitude))
        
        if exactly_one:
            return parse_code(codes[0])
        else:
            return (parse_code(code) for code in codes)

from geopy.geocoders import register
register("geonames", GeoNames)

import xml.dom.minidom
from urllib import urlencode
from urllib2 import urlopen

from geopy.geocoders.base import Geocoder


class GeoNames(Geocoder):
    def __init__(self, format_string='%s', output_format='xml'):
        self.format_string = format_string
        self.output_format = output_format

    @property
    def url(self):
        domain = "ws.geonames.org"
        output_format = self.output_format.lower()
        append_formats = {'json': 'JSON'}
        resource = "postalCodeSearch" + append_formats.get(output_format, '')
        return "http://%(domain)s/%(resource)s?%%s" % locals()

    def geocode(self, string, exactly_one=True):
        params = {'placename': string}
        url = self.url % urlencode(params)
        return self.geocode_url(url, exactly_one)

    def geocode_url(self, url, exactly_one=True):
        page = urlopen(url)
        dispatch = getattr(self, 'parse_' + self.output_format)
        return dispatch(page, exactly_one)

    def parse_json(self, page, exactly_one):
        if not isinstance(page, basestring):
            page = self._decode_page(page)
        json = simplejson.loads(page)
        codes = json.get('postalCodes', [])
        
        if exactly_one and len(codes) != 1:
            raise ValueError("Didn't find exactly one code! " \
                             "(Found %d.)" % len(codes))
        
        def parse_code(code):
            place = self._join_filter(", ", [code.get('placeName'),
                                             code.get('countryCode')])
            location = self._join_filter(" ", [place,
                                               code.get('postalCode')]) or None
            latitude = code.get('lat')
            longitude = code.get('lng')
            latitude = latitude and float(latitude)
            longitude = longitude and float(longitude)
            return (location, (latitude, longitude))

        if exactly_one:
            return parse_code(codes[0])
        else:
            return (parse_code(code) for code in codes)

    def parse_xml(self, page, exactly_one):
        if not isinstance(page, basestring):
            page = self._decode_page(page)
        doc = xml.dom.minidom.parseString(page)
        codes = doc.getElementsByTagName('code')
        
        if exactly_one and len(codes) != 1:
            raise ValueError("Didn't find exactly one code! " \
                             "(Found %d.)" % len(codes))

        def parse_code(code):
            place_name = self._get_first_text(code, 'name')
            country_code = self._get_first_text(code, 'countryCode')
            postal_code = self._get_first_text(code, 'postalcode')
            place = self._join_filter(", ", [place_name, country_code])
            location = self._join_filter(" ", [place, postal_code]) or None
            latitude = self._get_first_text(code, 'lat') or None
            longitude = self._get_first_text(code, 'lng') or None
            latitude = latitude and float(latitude)
            longitude = longitude and float(longitude)
            return (location, (latitude, longitude))
        
        if exactly_one:
            return parse_code(codes[0])
        else:
            return (parse_code(code) for code in codes)
