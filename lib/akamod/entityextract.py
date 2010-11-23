# -*- encoding: utf-8 -*-
'''
'''
import os, sys, time
import urllib
import hashlib
import functools
from gettext import gettext as _

# Requires Python 2.6 or http://code.google.com/p/json/
from amara.thirdparty import json

import amara
from amara.lib.util import *
from amara.thirdparty import json, httplib2
from amara.bindery import parse
from amara.lib import inputsource, U

from akara import module_config
from akara.services import simple_service
from akara.caching import cache, make_named_cache
from akara import logger

import y_serial_v060 as y_serial

CACHE_DIR = make_named_cache('akara.yahoo.extract')
if not CACHE_DIR: CACHE_DIR = '/tmp'
CACHE = y_serial.Main(os.path.join(CACHE_DIR, 'cache.sqlite'))

def memoize(table):
    def memoized_wrapper(func):
        @functools.wraps(func)
        def wrapper(key):
            try:
                value = CACHE.select(key, table)
                logger.debug('Value from cache %s: %s'%(table, repr(value)))
                if value: return value
            except IOError:
                pass #Cache file probably not created
            except Exception as e:
                logger.debug('Exception looking up from cache %s, key %s: %s'%(table, key, repr(e)))

            try:
                value = func(key)
            except Exception as e:
                logger.debug('Exception computing from key %s: %s'%(key, repr(e)))
                logger.debug('Will not be cached')
                raise
            else:
                #Only cache if function raised no exceptions
                CACHE.insert(value, key, table)
            return value
        return wrapper
    return memoized_wrapper


SERVICE_ID = 'http://purl.org/akara/services/demo/yahoo.extract.json'
@simple_service('POST', SERVICE_ID, 'akara.yahoo.extract', 'application/json')
def yahoo_extract(body, ctype):
    '''
    See:
    http://developer.yahoo.com/search/content/V1/termExtraction.html
    http://developer.yahoo.com/yql/guide/running-chapt.html
    http://developer.yahoo.com/yql/console/?q=select%20*%20from%20search.termextract%20where%20context%3D%22Italian%20sculptors%20and%20painters%20of%20the%20renaissance%20favored%20the%20Virgin%20Mary%20for%20inspiration%22#h=select%20*%20from%20search.termextract%20where%20context%3D%22%22
    '''
    #Yahoo e.g.
    #resp: {'status': '200', 'content-length': '518', 'content-location': 'http://query.yahooapis.com/v1/public/yql?q=select+%2A+from+search.termextract+where+context%3D%22Referred+from%3A+Library+of+Congress+-+Recorded+Sound%2810047%29+by%3A+Karen+Fishman%28106031%29+to+institution%3A+Library+of+Congress+-+American+Folklife+Center%2810019%29%22', 'transfer-encoding': 'chunked', 'age': '1', 'vary': 'Accept-Encoding', 'server': 'YTS/1.19.4', 'connection': 'keep-alive', '-content-encoding': 'gzip', 'cache-control': 'no-cache', 'date': 'Wed, 10 Nov 2010 16:57:08 GMT', 'access-control-allow-origin': '*', 'content-type': 'text/xml;charset=utf-8'} <?xml version="1.0" encoding="UTF-8"?>
    #body: <query xmlns:yahoo="http://www.yahooapis.com/v1/base.rng" yahoo:count="5" yahoo:created="2010-11-10T16:57:09Z" yahoo:lang="en-US"><results><Result xmlns="urn:yahoo:cate">american folklife center</Result><Result xmlns="urn:yahoo:cate">congress american folklife center</Result><Result xmlns="urn:yahoo:cate">library of congress</Result><Result xmlns="urn:yahoo:cate">institution library</Result><Result xmlns="urn:yahoo:cate">fishman</Result></results></query><!-- total: 136 -->

    m = hashlib.md5(body)
    bodyhash = m.hexdigest()

    @memoize('yahoo')
    def execute_query(key):
        yql = u'select * from search.termextract where context="%s"'%body.replace(u'""', u'')
        query = urllib.urlencode({'q' : yql})
        url = 'http://query.yahooapis.com/v1/public/yql?' + query

        H = httplib2.Http()
        resp, rbody = H.request(url) #headers={'Content-Type' : 'text/plain'})
        entities = []
        value = []
        if resp['status'].startswith('200'):
            doc = parse(rbody)
            try:
                value = [ U(r) for r in list(doc.query.results.Result) ]
                #print doc.query.results.Result
                #print entities
            except AttributeError:
                pass
        return value
        
    entities = execute_query(bodyhash)
    return json.dumps(entities)


#URL_REQUIRED = _("The 'url' query parameter is mandatory.")

#APIKEY = module_config().require("APIKEY", "Open Calais API Key (from semanticproxy.com)")
#CALAIS_URL = 'http://service.semanticproxy.com/processurl/%s/rdf/' % APIKEY
    

SERVICE_ID = 'http://purl.org/akara/services/demo/calais.json'
@simple_service('GET', SERVICE_ID, 'akara.calais.json', 'application/json')
def calais2json(url=None):
    '''
    url - the page to run against Calais
    
    Sample request:
    curl "http://localhost:8880/akara.calais.json?url=http://zepheira.com"
    '''
    doc = amara.parse(CALAIS_URL+url[0])
    relations = doc.xml_children[1].xml_value
    entry = {u'id': url}
    for line in relations.splitlines():
        if not line.strip(): continue
        line = line.split(u':')
        key, values = line[0], u':'.join(line[1:]).strip()
        if not values: continue
        vlist = values.split(',')
        entry[key] = values if len(vlist) == 1 else vlist
    return json.dumps({'items': [entry]}, indent=4)

