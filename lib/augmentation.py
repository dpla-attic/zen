'''
Data augmentation services supplied with Zen

>>> from zenlib import augmentation
>>> source = [{u"id": u"_1", u"label": u"_1", u"orig": u"text, text, text"}]
>>> propinfo = {u"delimiter": u",", u"extract": u"orig", u"property": u"shredded", u"enabled": True, u"label": "shredded result", u"tags": [u"property:type=text"]}
>>> result = {}
>>> augmentation.augment_shredded_list(source, propinfo, result)
>>> result
{u'_1': {u'shredded': [u'text', u'text', u'text'], u'id': u'_1', u'label': u'_1'}}

>>> source = [{u"id": u"_1", u"label": u"_1", u"orig": u"text, text and text"}]
>>> propinfo = {u"pattern": u"(,)|(and)", u"extract": u"orig", u"property": u"shredded", u"enabled": True, u"label": "shredded result", u"tags": [u"property:type=text"]}
>>> result = {}
>>> augmentation.augment_shredded_list(source, propinfo, result)
>>> result
{u'_1': {u'shredded': [u'text', u'text', u'text'], u'id': u'_1', u'label': u'_1'}}

'''

import re

from amara.lib import U
from amara.lib.date import timezone, UTC
from amara.thirdparty import json

try:
    from akara import logger
except ImportError:
    logger = None

from zenlib import register_service, zservice
from zenlib.temporal import smart_parse_date
from zenlib.geo import geolookup

#def UU(obj, k): return U(obj[k]) if k in obj and obj[k] is not None and U(k).strip() else u''
def UU(obj, k):
    result = U(obj.get(k), noneok=True)
    if result is None:
        return u''
    else:
        return result.strip()


@zservice(u'http://purl.org/com/zepheira/augmentation/location')
def augment_location(source, propertyinfo, items_dict):
    '''
    Sample propertyinfo
    {
        "property": "latlong",
        "enabled": true,
        "label": "Mapped place",
        "tags": ["property:type=location"],
        "composite": [
            "street_address",
            "city",
            "state",
            "zip"
        ]
    }
    '''
    composite = propertyinfo[u"composite"]
    pname = propertyinfo.get(u"property", u'location_latlong')
    for obj in source:
        try:
            location = u', '.join([ UU(obj, k) for k in composite ])
            if logger: logger.debug("location input: " + repr(location))
            location_latlong = geolookup(location)
            if location_latlong:
                objid = obj[u'id']
                val = items_dict.setdefault(objid, {u'id': objid, u'label': obj[u'label']})
                val[pname] = location_latlong
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception, e:
            if logger: logger.info('Exception in augment_location: ' + repr(e))
    return


LEN_BASE_ISOFORMAT = 19

@zservice(u'http://purl.org/com/zepheira/augmentation/datetime')
def augment_date(source, propertyinfo, items_dict):
    '''
    Sample propertyinfo
    {
        "property": "start_date",
        "enabled": true,
        "label": "Start date",
        "tags": ["property:type=datetime"],
        "composite": [
            "start"
        ]
    }
    '''
    composite = propertyinfo[u"composite"]
    pname = propertyinfo.get(u"property", u'iso_datetime')
    for obj in source:
        try:
            #Excel will sometimes give us dates as integers, which reflects in the data set coming back.
            #Hence the extra unicode conv.
            #FIXME: should fix in freemix.json endpoint and remove from here
            date = u', '.join([ unicode(obj[k]) for k in composite if unicode(obj.get(k, u'')).strip() ])
            if logger: logger.debug("date input: " + repr(date))
            #FIXME: Think clearly about timezone here.  Consider defaults to come from user profile
            clean_date = smart_parse_date(date)
            if clean_date:
                objid = obj[u'id']
                val = items_dict.setdefault(objid, {u'id': objid, u'label': obj[u'label']})
                try:
                    val[pname] = isobase(clean_date.utctimetuple()) + UTC.name
                except ValueError:
                    #strftime cannot handle dates prior to 1900.  See: http://docs.python.org/library/datetime.html#strftime-and-strptime-behavior
                    val[pname] = clean_date.isoformat()[:LEN_BASE_ISOFORMAT] + UTC.name
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception, e:
            if logger: logger.info('Exception in augment_date: ' + repr(e))
    return


@zservice(u'http://purl.org/com/zepheira/augmentation/luckygoogle')
def augment_luckygoogle(source, propertyinfo, items_dict):
    '''
    '''
    #logger.debug("Not found: " + place)
    composite = propertyinfo[u"composite"]
    pname = propertyinfo.get(u"property", u'luckygoogle')
    for obj in source:
        #Excel will sometimes give us dates as integers, which reflects in the data set coming back.
        #Hence the extra unicode conv.
        #FIXME: should fix in freemix.json endpoint and remove from here
        item = u', '.join([ unicode(obj[k]) for k in composite if unicode(obj.get(k, u'')).strip() ])
        link = luckygoogle(item)
        if link:
            objid = obj[u'id']
            val = items_dict.setdefault(objid, {u'id': objid, u'label': obj[u'label']})
            val[pname] = link
    return


@zservice(u'http://purl.org/com/zepheira/augmentation/shredded-list')
def augment_shredded_list(source, propertyinfo, items_dict):
    '''
    See: http://community.zepheira.com/wiki/loc/ValidPatternsList
    '''
    extract = propertyinfo[u"extract"]
    pname = propertyinfo.get(u"property", u'shreddedlist')
    pattern = propertyinfo.get(u"pattern")
    if pattern: pattern = re.compile(pattern)
    delim = propertyinfo.get(u"delimiter", u',')
    for obj in source:
        try:
            if pattern:
                #FIXME: Needs to be better spec'ed
                result = pattern.split(obj[extract])
            else:
                result = [ item.strip() for item in obj[extract].split(delim) ]
            if logger: logger.debug("augment_shredded_list: " + repr((obj[extract], pattern, delim)))
            if logger: logger.debug("result: " + repr(result))
            if result:
                objid = obj[u'id']
                val = items_dict.setdefault(objid, {u'id': objid, u'label': obj[u'label']})
                val[pname] = result
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception, e:
            if logger: logger.info('Exception in augment_shredded_list: ' + repr(e))
    return


