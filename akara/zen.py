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

rulesheet-secret (optional) - A secret hash used for signing rulesheets, only to be shared with rulesheet developers

Sample config:

[zen]
rulesheet-secret = abcdef

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

from amara.thirdparty import httplib2
from dateutil.parser import parse as dateparse

import amara
from amara import _
#from amara.namespaces import *
from amara.lib import inputsource
from amara.bindery.model import examplotron_model, generate_metadata
from amara import bindery
from amara.lib.iri import split_fragment, relativize, absolutize, is_absolute, join
from amara.bindery.util import dispatcher, node_handler, property_sequence_getter
from amara.lib.util import first_item
#from amara.lib.date import timezone, UTC

from akara.registry import list_services, _current_registry
from akara.util import copy_auth, extract_auth, read_http_body_to_temp, copy_headers_to_dict
#from akara.util.moin import node, ORIG_BASE_HEADER, DOCBOOK_IMT, RDF_IMT, HTML_IMT
from akara.util.moin import ORIG_BASE_HEADER, DOCBOOK_IMT, RDF_IMT, HTML_IMT, XML_IMT
from akara.services import simple_service
from akara.services import method_dispatcher
from akara.util import status_response
from akara import logger
from akara import request

from akara.util.moin import wiki_uri

from zenlib.moinmodel import node, rulesheet, moinrest_resolver, parse_moin_xml, zenuri_to_moinrest, MOINREST_SERVICE_ID
from zenlib.util import find_peer_service

#endpoints = AKARA.module_config.get('endpoints')
#node.ENDPOINTS = endpoints and eval(endpoints)
#logger.debug('GRIPPO: ' + repr((endpoints, eval(endpoints))))
#logger.debug('GRIPPO: ' + repr((endpoints, )))

node.SECRET = AKARA.module_config.get('rulesheet-secret', '')


#aname = partial(property_sequence_getter, u"name")
#aemail = partial(property_sequence_getter, u"email")
#auri = partial(property_sequence_getter, u"uri")

UNSUPPORTED_IN_FILENAME = re.compile('\W')
#SOURCE = AKARA_MODULE_CONFIG['source-wiki-root']
#POST_TO = AKARA_MODULE_CONFIG['post-to']

SELF_END_POINT = None


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
    #FIXME: Needs update to forward cookies, i.e. headers to moinrest (see put_resource)
    #Set up to use HTTP auth for all wiki requests
    baseuri = environ['SCRIPT_NAME'].rstrip('/') #$ServerPath/zen
    handler = copy_auth(environ, baseuri)
    opener = urllib2.build_opener(handler) if handler else urllib2.build_opener()

    resource = node.lookup(zenuri_to_moinrest(environ), opener=opener)
    if not resource:
        start_response(status_response(400),[('Content-Type','text/plain')])
        return( "Unable to access resource\n" )

    resolver = resource.resolver
    
    # Choose a preferred media type from the Accept header, using application/json as presumed
    # default, and stripping out any wildcard types and type parameters
    #
    # FIXME Ideally, this should use the q values and pick the best media type, rather than
    # just picking the first non-wildcard type.  Perhaps: http://code.google.com/p/mimeparse/
    accepted_imts = []
    accept_header = environ.get('HTTP_ACCEPT')
    if accept_header :
        accepted_imts = [ type.split(';')[0] for type in accept_header.split(',') ]
    accepted_imts.append('application/json')
    if logger: logger.debug('accepted_imts: ' + repr(accepted_imts))
    imt = first_item(dropwhile(lambda x: '*' in x, accepted_imts))

    qparams = cgi.parse_qs(environ['QUERY_STRING'])
    rulesheet_override = qparams.get('rulesheet')

    if rulesheet_override:
        handler = rulesheet(rulesheet_override[0], resource.resource_type, resolver=resolver).run(environ, 'GET', imt)
    else:
        handler = resource.resource_type.run_rulesheet(environ, 'GET', imt)
    rendered = handler(resource)

    start_response(status_response(httplib.OK), [("Content-Type", str(handler.imt)), ("Cache-Control", "max-age="+str(handler.ttl))])
    #start_response(status_response(status), [("Content-Type", ctype), (moin.ORIG_BASE_HEADER, moin_base_info)])
    return rendered


@dispatcher.method("PUT")
def put_resource(environ, start_response):
    # Keep inbound headers so we can forward to moinrest
    req_headers = copy_headers_to_dict(environ)

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
        return 'type URL parameter required\n'

    rtype = rtype[0]
    if not is_absolute(rtype):
        moinresttop = find_peer_service(environ, MOINREST_SERVICE_ID)
        rtype = join(moinresttop, environ['PATH_INFO'].lstrip('/').split('/')[0], rtype)
    resource_type = node.lookup(rtype, opener=opener)
    
    temp_fpath = read_http_body_to_temp(environ, start_response)
    body = open(temp_fpath, "r").read()

    handler = resource_type.run_rulesheet(environ, 'PUT', imt)
    wikified = handler(resource_type, body)
    #logger.debug('put_resource wikified result: ' + repr((wikified,)))

    H = httplib2.Http()

    # This was originally always returning 200 even if moinrest failed, so an improvement
    # would be to return the moinrest response as the Zen response.  FIXME Even better would
    # be to decide exactly what this relationship should look like, e.g. how redirects
    # or auth responses are managed, if any content needs URL-rewriting, how other response or
    # entity headers are handled, etc..., plus general be-a-good-proxy behaviour
    #
    # This httplib2 feature permits a single code path for proxying responses
    H.force_exception_to_status_code = True

    headers = req_headers
    headers['Content-Type'] = 'text/plain'

    if creds:
        user, passwd = creds
        H.add_credentials(user, passwd)
    
    resp, content = H.request(zenuri_to_moinrest(environ), "PUT", body=wikified.encode('UTF-8'), headers=headers)

    start_response(status_response(resp.status), [("Content-Type", resp['content-type'])])
    return content


@dispatcher.method("POST")
def post_resource(environ, start_response):
    '''
    Create a new record with a resource type
    '''
    # Keep inbound headers so we can forward to moinrest
    req_headers = copy_headers_to_dict(environ)

    #Set up to use HTTP auth for all wiki requests
    baseuri = environ['SCRIPT_NAME'].rstrip('/') #'/zen' ; note: does not include $ServerPath
    logger.debug('STACEY: ' + repr((baseuri, )))
    handler = copy_auth(environ, baseuri)
    creds = extract_auth(environ)
    opener = urllib2.build_opener(handler) if handler else urllib2.build_opener()

    #import pprint; logger.debug('put_resource input environ: ' + repr(pprint.pformat(environ)))
    imt = environ['CONTENT_TYPE']

    resource_type = node.lookup(zenuri_to_moinrest(environ), opener=opener)
    if not resource_type:
        start_response(status_response(400),[('Content-Type','text/plain')])
        return( "Unable to access resource\n" )

    resolver = resource_type.resolver
    
    temp_fpath = read_http_body_to_temp(environ, start_response)
    body = open(temp_fpath, "r").read()

    handler = resource_type.run_rulesheet(environ, 'POST', imt)
    new_uri, wikified = handler(resource_type, body)
    #logger.debug('post_resource wikified result & uri: ' + repr((wikified, new_uri)))

    H = httplib2.Http()

    # This was originally always returning 200 even if moinrest failed, so an improvement
    # would be to return the moinrest response as the Zen response.  FIXME Even better would
    # be to decide exactly what this relationship should look like, e.g. how redirects
    # or auth responses are managed, if any content needs URL-rewriting, how other response or
    # entity headers are handled, etc..., plus general be-a-good-proxy behaviour
    #
    # This httplib2 feature permits a single code path for proxying responses
    H.force_exception_to_status_code = True

    headers = req_headers
    headers['Content-Type'] = 'text/plain'

    if creds:
        user, passwd = creds
        H.add_credentials(user, passwd)
    
    resp, content = H.request(new_uri, "PUT", body=wikified.encode('UTF-8'), headers=headers)
    original_base, wrapped_base, original_page = resp[ORIG_BASE_HEADER].split()
    rel_new_uri = relativize(new_uri, wrapped_base)

    resp_headers = [("Content-Type", resp['content-type']), ('Location', new_uri), ('X-Wiki-Relative-Location', rel_new_uri)]
    start_response(status_response(resp.status), resp_headers)
    return content


@dispatcher.method("DELETE")
def delete_resource(environ, start_response):
    # Keep inbound headers so we can forward to moinrest
    req_headers = copy_headers_to_dict(environ)

    H = httplib2.Http()
    H.force_exception_to_status_code = True

    creds = extract_auth(environ)
    if creds:
        user, passwd = creds
        H.add_credentials(user, passwd)

    resp, content = H.request(zenuri_to_moinrest(environ), "DELETE", headers=req_headers)

    start_response(status_response(resp.status), [("Content-Type", resp['content-type'])])
    return content
