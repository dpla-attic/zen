# -*- coding: iso-8859-1 -*-
# 
"""
z_zen.py

Accesses a Moin wiki (via the Akara moinrest wrapper) to use as a source for a
authoring and metadata aextraction

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

import simplejson
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

    resource = node.lookup(zenuri_to_moinrest(environ), opener=opener)
    resolver = resource.resolver
    
    accepted_imts = environ.get('HTTP_ACCEPT').split(',')
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
    start_response(status_response(httplib.OK), [("Content-Type", imt), ("Cache-Control", "max-age="+str(handler.ttl))])
    #start_response(status_response(status), [("Content-Type", ctype), (moin.ORIG_BASE_HEADER, moin_base_info)])
    return rendered


@dispatcher.method("PUT")
def put_resource(environ, start_response):
    #Set up to use HTTP auth for all wiki requests
    baseuri = environ['SCRIPT_NAME'].rstrip('/') #$ServerPath/zen
    handler = copy_auth(environ, baseuri)
    creds = extract_auth(environ)
    opener = urllib2.build_opener(handler) if handler else urllib2.build_opener()

    import pprint; logger.debug('GRIPPO: ' + repr(pprint.pformat(environ)))
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
    logger.debug('GRIPPO: ' + repr((wikified,)))

    H = httplib2.Http('.cache')

    if creds:
        user, passwd = creds
        H.add_credentials(user, passwd)
    
    headers = {'Content-Type' : 'text/plain'}
    resp, content = H.request(zenuri_to_moinrest(environ), "PUT", body=wikified.encode('UTF-8'), headers={'Content-Type' : 'text/plain'})

    start_response(status_response(httplib.OK), [("Content-Type", 'text/plain')])
    return 'Updated OK'


#--- %< --- "Classic" Zen interface

TOP_REQUIRED = _("The 'top' query parameter is mandatory.")

BROWSER_UA = 'Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.1.8) Gecko/20100202 Firefox/3.5.8'

SERVICE_ID = 'http://purl.org/com/zepheira/zen/index'
@simple_service('GET', SERVICE_ID, 'zen.index.json', 'application/json')
def zen_index(top=None, maxcount=None):
    '''
    Extract Exhibit JSON [1] from Moin pages according to Zen conventions
    
    top - page on which to start looking for linked Zen resouces
    maxcount - limit to the number of records returned; unlimited by default

    curl "http://localhost:8880/zen.index.json?top=http://example-akara.com/moin/mywiki/zentoppage"

    [1] For more on Exhibit JSON see: http://www.ibm.com/developerworks/web/library/wa-realweb6/ ; see listing 3
    '''
    #Useful: http://www.voidspace.org.uk/python/articles/authentication.shtml
    #curl "http://localhost:8880/zen.index.json?top=http://community.zepheira.com/wiki/loc/LoC/Collections/"
    #top = first_item(top, next=partial(assert_not_equal, None, msg=TOP_REQUIRED))
    this_service = request.environ['SCRIPT_NAME']
    this_service = request_uri(request.environ, include_query=False).rstrip('/')
    if node.ENDPOINTS is None:
        node.ENDPOINTS = dict(
            [ (s.ident, find_peer_service(request.environ, s.ident))
              for (path, s) in _current_registry._registered_services.iteritems()
            ])
        #logger.debug('Node end-points: ' + repr(node.ENDPOINTS))

    #Set up to use HTTP auth for all wiki requests
    handler = copy_auth(request.environ, top)
    opener = urllib2.build_opener(handler) if handler else urllib2.build_opener()

    #Invoke service to get resources for this type
    #FIXME: Use service discovery instead
    url = basejoin(this_service, 'zen.find.resources?type=' + top)
    req = urllib2.Request(url)
    resp = opener.open(req)
    body = resp.read()
    original_base, wrapped_base, original_page, resource_links = simplejson.loads(body)
    logger.debug('HREF2: ' + repr((original_base, wrapped_base, original_page, resource_links)))

    resources = []
    failed = []
    for link in resource_links:
        #print >> sys.stderr, 'LINK:', link
        #uri = split_fragment(item.resource)[0]
        #relative = uri[wikibase_len:]
        #print >> sys.stderr, uri, relative
        #if rewrite:
        #    uri = uri.replace(rewrite, wikibase)
        wrapped_resource, orig_resource = wiki_uri(original_base, wrapped_base, link)
        if logger: logger.debug('Resource URIs: ' + repr((link, wrapped_resource, orig_resource)))
        #rest_uri, moin_link = wrapped_uri(original_wiki_base, link)
        resource = node.lookup(wrapped_resource, opener=opener)
        resources.append(resource)
    handler = resource.resource_type.run_rulesheet('collect', 'application/json')
    rendered = handler(resources)
    return rendered
    #result = {u'items': items}
    #if failed: result[u'failed'] = failed
    return simplejson.dumps(result, indent=4)


#-----------


    items = []
    failed = []
    for link in resources:
        #print >> sys.stderr, 'LINK:', link
        #uri = split_fragment(item.resource)[0]
        #relative = uri[wikibase_len:]
        #print >> sys.stderr, uri, relative
        #if rewrite:
        #    uri = uri.replace(rewrite, wikibase)
        wrapped_resource, orig_resource = wiki_uri(original_base, wrapped_base, link)
        if logger: logger.debug('Resource URIs: ' + repr((link, wrapped_resource, orig_resource)))
        #rest_uri, moin_link = wrapped_uri(original_wiki_base, link)
        resource = node.lookup(wrapped_resource, opener=opener)
        try:
            handler = resource.resource_type.run_rulesheet('collect', 'application/json')
            rendered = handler(resource)
            if rendered:
                items.append(rendered)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception, e:
            logger.info('Exception handling Zen record: ' + wrapped_resource)
            logger.info('Exception info: ' + repr(e))
            import traceback; logger.debug(traceback.format_exc())
            failed.append(wrapped_resource)
    result = {u'items': items}
    if failed: result[u'failed'] = failed
    return simplejson.dumps(result, indent=4)


def resolve_rule_sheet(resource):
    '''
    A Zen rule sheet can be:
    * A full Akara service, indexed by service ID
    * A signed URL referenced from a resource type page (signature not yet implemented)
    * An globally imported node class (deprecated)
    '''
    return rulesheet

#Really just serves as a warning that the following function shadows type builtin, and provides a way to get it back
PYTHON_TYPE_BUILTIN = type

SERVICE_ID = 'http://purl.org/com/zepheira/zen/find-resources'
@simple_service('GET', SERVICE_ID, 'zen.find.resources', 'application/json')
def builtin_get_resources(type=None, limit=None):
    '''
    Find resources from Moin pages according to Zen conventions, returned in simple JSON
    
    rtype - resource type
    limit - max number of records returned; unlimited by default
    
    Note: this method is technically quite brittle because it relies on the HTML rendering skin

    curl "http://localhost:8880/zen.find.resources?type=http://example-akara.com/moin/mywiki/zentoppage"
    '''
    handler = copy_auth(request.environ, type)
    opener = urllib2.build_opener(handler) if handler else urllib2.build_opener()
    resolver = moinrest_resolver(opener=opener)
    #req = urllib2.Request(type, headers={'Accept': XML_IMT, 'User-Agents': BROWSER_UA})
    isrc, resp = parse_moin_xml(type, resolver=resolver)
    doc = bindery.parse(isrc)

    try:
        original_base, wrapped_base, original_page = dict(resp.info())[ORIG_BASE_HEADER].split()
    except KeyError:
        raise RuntimeError('"type" parameter value appears to be a direct link to a Moin instance, rather than its Moin/REST proxy')
    #wikibase, outputdir, rewrite, pattern
    #wikibase_len = len(rewrite)
    hrefs = doc.xml_select(u'//table[@class="navigation"]//@href')
    if limit:
        hrefs = islice(hrefs, 0, int(limit))
    hrefs = list(hrefs); logger.debug('builtin_get_resources HREFS1: ' + repr(hrefs))
    return simplejson.dumps((original_base, wrapped_base, original_page, [ navchild.xml_value for navchild in hrefs ]))


SERVICE_ID = 'http://purl.org/com/zepheira/zen/create'
@simple_service('POST', SERVICE_ID, 'zen.create.json', 'application/json')
def zen_create(body, ctype, rtype=None):
    '''
    Extract Exhibit JSON [1] from Moin pages according to Zen conventions
    
    top - page on which to start looking for linked Zen resouces
    maxcount - limit to the number of records returned; unlimited by default

    curl "http://localhost:8880/zen.index.json?top=http://example-akara.com/moin/mywiki/zentoppage"

    [1] For more on Exhibit JSON see: http://www.ibm.com/developerworks/web/library/wa-realweb6/ ; see listing 3
    '''
    #Useful: http://www.voidspace.org.uk/python/articles/authentication.shtml
    #curl "http://localhost:8880/zen.index.json?top=http://community.zepheira.com/wiki/loc/LoC/Collections/"
    #top = first_item(top, next=partial(assert_not_equal, None, msg=TOP_REQUIRED))
    this_service = request.environ['SCRIPT_NAME']
    this_service = request_uri(request.environ)
    this_service = request_uri(request.environ, include_query=False).rstrip('/')
    if node.ENDPOINTS is None:
        node.ENDPOINTS = dict(
            [ (s.ident, find_peer_service(request.environ, s.id))
              for (path, s.id) in _current_registry._registered_services.iteritems()
            ])
        #logger.debug('Node end-points: ' + repr(node.ENDPOINTS))

    #Set up to use HTTP auth for all wiki requests
    handler = copy_auth(request.environ, top)
    opener = urllib2.build_opener(handler) if handler else urllib2.build_opener()

    node = lookup
    items = []
    failed = []
    for link in resources:
        #print >> sys.stderr, 'LINK:', link
        #uri = split_fragment(item.resource)[0]
        #relative = uri[wikibase_len:]
        #print >> sys.stderr, uri, relative
        #if rewrite:
        #    uri = uri.replace(rewrite, wikibase)
        wrapped_resource, orig_resource = wiki_uri(original_base, wrapped_base, link)
        if logger: logger.debug('Resource URIs: ' + repr((link, wrapped_resource, orig_resource)))
        #rest_uri, moin_link = wrapped_uri(original_wiki_base, link)
        resource = node.lookup(wrapped_resource, opener=opener)
        try:
            rendered = resource.run_rulesheet('GET', 'application/json')
            if rendered:
                items.append(rendered)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception, e:
            logger.info('Exception handling Zen record: ' + wrapped_resource)
            logger.info('Exception info: ' + repr(e))
            import traceback; logger.debug(traceback.format_exc())
            failed.append(wrapped_resource)
    result = {u'items': items}
    if failed: result[u'failed'] = failed
    #XXX Return a Location header
    return simplejson.dumps(result, indent=4)


