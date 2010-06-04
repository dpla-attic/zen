# -*- coding: iso-8859-1 -*-
# 
"""
zen.py

Accesses a Moin wiki (via the Akara moinrest wrapper) to use as a source for
authoring and metadata extraction

Based on Moin/CMS (see http://wiki.xml3k.org/Akara/Services/MoinCMS )

@ 2009-2010 by Zepheira LLC

This file is part of the open source Zen project,
provided under the Apache 2.0 license.
See the files LICENSE and NOTICE for details.
Project home, documentation, distributions: http://foundry.zepheira.com/projects/zen

See:

 * http://purl.org/xml3k/akara
 * http://foundry.zepheira.com/projects/zen
 
= Defined REST entry points =

http://purl.org/com/zepheira/services/ct.gov.moin (ct.gov.moin) Handles POST
http://labwiki.semioclinical.com/mywiki/resources/ct.gov/zen (ct.gov.zen.js) Handles GET

= Configuration =

moinrestbase (required) - the base Moin/REST URI for the place where pages should
                          be added/updated
A closer look at moinrestbase.  In the example value: http://localhost:8880/moin/wikiid/

 * http://localhost:8880/... - the URL to the root of an Akara instance
 * ...moin... - the moint point of the Moin/REST wrapper module under Akara (moinrest.py)
 * ...wikiid... - the wiki ID for a specific, wrapped Moin wiki, as defined e.g.
   in a target-xxx config var for moinrest.py e.g. "wikiid" above would correspond to
   "target-wikiid" config var for moinrest

Sample config:

[zen]
moinrestbase = http://localhost:8880/moin/wikiid/

= Notes on security =

To-do

"""
#Sample config
#{"http://purl.org/xml3k/akara/cms/resource-type"}
#endpoints = {"http://purl.org/xml3k/akara/cms/spam": "http://localhost:8880/spam.zen"}

import os
import sys
import re
import cgi
import pprint
import httplib
import urllib, urllib2
import datetime
from itertools import islice
from wsgiref.util import request_uri
from itertools import dropwhile

import httplib2
from dateutil.parser import parse as dateparse

import amara
from amara import _
#from amara.namespaces import *
from amara.lib import inputsource
from amara.bindery.model import examplotron_model, generate_metadata
from amara.writers.struct import *
from amara import bindery
from amara.lib.iri import split_fragment, relativize, absolutize, basejoin, join
from amara.bindery.util import dispatcher, node_handler, property_sequence_getter
from amara.lib.util import first_item
#from amara.lib.date import timezone, UTC

from akara.registry import list_services, _current_registry
from akara.util import copy_auth, extract_auth, read_http_body_to_temp
#from akara.util.moin import node, ORIG_BASE_HEADER, DOCBOOK_IMT, RDF_IMT, HTML_IMT
from akara.util.moin import ORIG_BASE_HEADER, DOCBOOK_IMT, RDF_IMT, HTML_IMT, XML_IMT
from akara.services import simple_service
from akara.services import method_dispatcher
from akara.util import status_response
from akara import logger
from akara import request

from akara.util.moin import wiki_uri

from zenlib.moinmodel import node, rulesheet, moinrest_resolver, parse_moin_xml
from zenlib.util import find_peer_service

#endpoints = AKARA.module_config.get('endpoints')
#node.ENDPOINTS = endpoints and eval(endpoints)
#logger.debug('GRIPPO: ' + repr((endpoints, eval(endpoints))))
#logger.debug('GRIPPO: ' + repr((endpoints, )))

node.SECRET = AKARA.module_config.get('rulesheet-secret', '')

MOINREST_SERVICE_ID = 'http://purl.org/xml3k/akara/services/demo/moinrest'


#aname = partial(property_sequence_getter, u"name")
#aemail = partial(property_sequence_getter, u"email")
#auri = partial(property_sequence_getter, u"uri")

UNSUPPORTED_IN_FILENAME = re.compile('\W')
#SOURCE = AKARA_MODULE_CONFIG['source-wiki-root']
#POST_TO = AKARA_MODULE_CONFIG['post-to']

SELF_END_POINT = None

def zenuri_to_moinrest(environ):
    #self_end_point = environ['SCRIPT_NAME'].rstrip('/') #$ServerPath/zen
    #self_end_point = request_uri(environ, include_query=False).rstrip('/')
    #self_end_point = guess_self_uri(environ)
    #absolutize(environ['SCRIPT_NAME'].rstrip('/'), request_uri(environ, include_query=False))
    #logger.debug('moinrest_uri: ' + repr((self_end_point, MOINREST_SERVICE_ID)))
    moinresttop = find_peer_service(environ, MOINREST_SERVICE_ID)
    #logger.debug('moinrest_uri: ' + repr(moinresttop))
    #logger.debug('moinrest_uri: ' + repr(environ['PATH_INFO']))
    moinrest_uri = join(moinresttop, environ['PATH_INFO'].lstrip('/'))
    logger.debug('moinrest_uri: ' + repr(moinrest_uri))
    return moinrest_uri


DEFAULT_MOUNT = 'zen'
SERVICE_ID = 'http://purl.org/com/zepheira/zen/main'

# ----------------------------------------------------------------------
#                       HTTP Method Handlers
# ----------------------------------------------------------------------
# The following functions implement versions of the various HTTP methods 
# (GET, HEAD, POST, PUT).  Each method is actually implemented as a
# a pair of functions.  One is a private implementation (e.g., _get_page).  
# The other function is a wrapper that encloses each handler with the error 
# handling function above (moin_error_handler).   Again, this is to avoid
# excessive duplication of error handling code.

#@method_dispatcher(SERVICE_ID, DEFAULT_MOUNT, wsgi_wrapper=moin_error_wrapper)
@method_dispatcher(SERVICE_ID, DEFAULT_MOUNT)
def dispatcher():
    #__doc__ = SAMPLE_QUERIES_DOC
    return


@dispatcher.method("GET")
def get_resource(environ, start_response):
    #Set up to use HTTP auth for all wiki requests
    baseuri = environ['SCRIPT_NAME'].rstrip('/') #$ServerPath/zen
    handler = copy_auth(environ, baseuri)
    opener = urllib2.build_opener(handler) if handler else urllib2.build_opener()

    try :
        resource = node.lookup(zenuri_to_moinrest(environ), opener=opener)
    except urllib2.HTTPError as he :
        start_response(status_response(he.code),[('Content-Type','text/plain')])
        return( "%(code)d %(msg)s\n" % {'code':he.code,'msg':he.msg} )

    resolver = resource.resolver
    
    # Choose a preferred media type from the Accept header, using application/json as presumed
    # default, and stripping out any wildcard types and type parameters
    #
    # FIXME Ideally, this should use the q values and pick the best media type, rather than
    # just picking the first non-wildcard type.  Perhaps: http://code.google.com/p/mimeparse/
    accepted_imts = [ type.split(';')[0] for type in environ.get('HTTP_ACCEPT').split(',') ]
    accepted_imts.append('application/json')
    logger.debug('accepted_imts: ' + repr(accepted_imts))
    imt = first_item(dropwhile(lambda x: '*' in x, accepted_imts))

    qparams = cgi.parse_qs(environ['QUERY_STRING'])
    rulesheet_override = qparams.get('rulesheet')

    if rulesheet_override:
        handler = rulesheet(rulesheet_override[0]).run(resource, 'GET', imt)
    else:
        handler = resource.resource_type.run_rulesheet('GET', imt)
    rendered = handler(resource)

    start_response(status_response(httplib.OK), [("Content-Type", str(handler.imt)), ("Cache-Control", "max-age="+str(handler.ttl))])
    #start_response(status_response(status), [("Content-Type", ctype), (moin.ORIG_BASE_HEADER, moin_base_info)])
    return rendered


@dispatcher.method("PUT")
def put_resource(environ, start_response):
    #Set up to use HTTP auth for all wiki requests
    baseuri = environ['SCRIPT_NAME'].rstrip('/') #$ServerPath/zen
    handler = copy_auth(environ, baseuri)
    creds = extract_auth(environ)
    opener = urllib2.build_opener(handler) if handler else urllib2.build_opener()

    #import pprint; logger.debug('put_resource input environ: ' + repr(pprint.pformat(environ)))
    imt = environ['CONTENT_TYPE']
    qparams = cgi.parse_qs(environ['QUERY_STRING'])
    rtype = qparams.get('type')
    if not rtype:
        status = httplib.BAD_REQUEST
        start_response(status_response(status), [("Content-Type", 'text/plain')])
        return 'type URL parameter required'

    resource_type = node.lookup(rtype[0], opener=opener)
    resolver = resource_type.resource_type
    
    temp_fpath = read_http_body_to_temp(environ, start_response)
    body = open(temp_fpath, "r").read()

    handler = resource_type.run_rulesheet('PUT', imt)
    wikified = handler(resource_type, body)
    #logger.debug('put_resource wikified result: ' + repr((wikified,)))

    H = httplib2.Http('.cache')

    if creds:
        user, passwd = creds
        H.add_credentials(user, passwd)
    
    headers = {'Content-Type' : 'text/plain'}
    resp, content = H.request(zenuri_to_moinrest(environ), "PUT", body=wikified.encode('UTF-8'), headers={'Content-Type' : 'text/plain'})

    start_response(status_response(httplib.OK), [("Content-Type", 'text/plain')])
    return 'Updated OK'


