# -*- encoding: utf-8 -*-
'''
'''
import os, sys, time
import urllib
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

from zen.util import y_serial_memoize as memoize
from zen.linktools import google_backlinks

import y_serial_v060 as y_serial
import pagerank

CACHE_DIR = make_named_cache('akara.pagerank')
if not CACHE_DIR: CACHE_DIR = '/tmp'
CACHE = y_serial.Main(os.path.join(CACHE_DIR, 'cache.sqlite'))

SERVICE_ID = 'http://purl.org/akara/services/demo/pagerank.json'
@simple_service('GET', SERVICE_ID, 'akara.pagerank', 'application/json')
def lookup_pagerank(url=None):
    '''
    See:
    
    http://coreygoldberg.blogspot.com/2010/01/python-lookup-google-pagerank-score.html
    '''
    @memoize(CACHE, 'pagerank', track_exceptions=True, logger=logger)
    def execute_lookup(key):
        rank = pagerank.get_pagerank(key)
        if rank is None:
            logger.debug('Error looking up pagerank for %s'%(key))
            return ''
        return rank
        
    rank = execute_lookup(url)
    return rank

CACHE_DIR = make_named_cache('akara.gbacklinks')
if not CACHE_DIR: CACHE_DIR = '/tmp'
CACHE = y_serial.Main(os.path.join(CACHE_DIR, 'cache.sqlite'))

SERVICE_ID = 'http://purl.org/akara/services/demo/gbacklinks.json'
@simple_service('GET', SERVICE_ID, 'akara.gbacklinks', 'application/json')
def lookup_gbacklinks(url=None):
    '''
    See:
    
    '''
    @memoize(CACHE, 'gbacklinks', logger=logger)
    def execute_lookup(key):
        links = google_backlinks(key)
        return links
        
    links = execute_lookup(url)
    return json.dumps(links)

