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

RULESHEET_SECRET (optional) - A secret hash used for signing rulesheets, only to be shared with rulesheet developers
SPACES - a dictionary of "spaces" over which Zen operates.  An example of a space is a wiki, or an AtomPub endpoint
         the key of the dict is used as a URI component, e.g. the query would be /zen/mywiki
         to access the space configured with key 'mywiki'.  The value of each space config is
         either an Akara service ID, for the slave service, or a tuple of
         (Akara service ID, slave env transform)
         In the latter case the transform is a function that operates on the inbound WSGI
         environment to Zen and returns the appropriate equivalent environ for calling the slave service

Sample config:

class zen:
    RULESHEET_SECRET = 'abcdef'
    SPACES = {
        'mywiki': 'zen.moin.slaveinfo',
    }

= Notes on security =

To-do

"""
#SPACES = {'mywiki': ('http://purl.org/xml3k/akara/services/demo/moinrest', {'wikiid': 'mywiki'})}
#the latter case is used with spaces where the back end service URL uses a query template

import re
import cgi
import pprint
import httplib
import urllib, urllib2
from wsgiref.util import shift_path_info, request_uri
from itertools import dropwhile

import amara
from amara.thirdparty import httplib2
from amara.lib.iri import split_fragment, relativize, absolutize, is_absolute, join
from amara.lib.util import first_item
#from amara.lib.date import timezone, UTC
#from amara import _
#from amara.namespaces import *

from akara.registry import list_services, _current_registry
from akara.util import find_peer_service, extract_auth, read_http_body_to_temp, copy_headers_to_dict
from akara.util import status_response
from akara.util.moin import ORIG_BASE_HEADER, DOCBOOK_IMT, RDF_IMT, HTML_IMT, XML_IMT
#from akara.services import simple_service
from akara.services import method_dispatcher
from akara import request, logger, module_config
from akara.registry import get_a_service_by_id
from akara.opensearch import apply_template

from zen.util import requested_imt
from zen import ZEN_SERVICE_ID

#import zenlib.moinmodel
#from zenlib.moinmodel import node, rulesheet, moinrest_resolver, parse_moin_xml, zenuri_to_moinrest, MOINREST_SERVICE_ID
#from zenlib.util import find_peer_service

SECRET = module_config().get('RULESHEET_SECRET', '')
SPACESDEF = module_config()['SPACES']()
SPACES = {}

UNSUPPORTED_IN_FILENAME = re.compile('\W')

DEFAULT_MOUNT = 'zen'

H = httplib2.Http('/tmp/.cache')

FIRST_REQUEST_FLAG = False
#def module_load():

FIND_PEER_SERVICE_KEY = 'akara.FIND_PEER_SERVICE'

def setup_request(environ):
    '''
    Constants to be set up upon the first request (i.e. need to be run from an Akara worker)
    '''
    global SPACES, FIRST_REQUEST_FLAG
    if not FIRST_REQUEST_FLAG:
        FIRST_REQUEST_FLAG = True

        #Set up spaces
        environ[FIND_PEER_SERVICE_KEY] = find_peer_service
        for space in dir(SPACESDEF):
        #for space, slaveclass in SPACES.items():
            if not space.startswith('__'):
                logger.debug('spaces: ' + repr(space))
                sinfo = getattr(SPACESDEF, space)()
                if isinstance(sinfo, tuple):
                    sclass, sparams = sinfo
                else:
                    sclass, sparams = sinfo, None
                head, tail = sclass.rsplit('.', 1)
                module = __import__(head, {}, {}, [tail])
                sclassobj = getattr(module, tail)
                slaveinstance = sclassobj(environ)
                s = get_a_service_by_id(slaveinstance.SERVICEID)
                #Set up class/instance params based on live Akara environment
                slaveinstance.service = s
                slaveinstance.params = sparams
                slaveinstance.space_tag = space
                slaveinstance.logger = logger
                slaveinstance.SECRET = SECRET
                SPACES[space] = slaveinstance
    return


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
@method_dispatcher(ZEN_SERVICE_ID, DEFAULT_MOUNT)
def dispatcher():
    #__doc__ = SAMPLE_QUERIES_DOC
    return


@dispatcher.method("GET")
def get_resource(environ, start_response):
    #FIXME: Needs update to forward cookies, i.e. headers to moinrest (see put_resource)
    #Set up to use HTTP auth for all wiki requests
    setup_request(environ)
    #space_tag = shift_path_info(environ)
    space_tag = environ['PATH_INFO'].lstrip('/').split('/', 1)[0]

    slaveinfo = SPACES[space_tag]
    
    #Forward the query to the slave, and get the result
    #FIXME: Zen should do some processing in order to assess/override/suppress etc. the rulesheet
    #Though this may be in the form of utility functions for the driver
    rendered = slaveinfo.forward(environ, start_response)
    #slaveinfo.forward should have called start_response already
    return rendered

    #qparams = cgi.parse_qs(environ['QUERY_STRING'])
    #rulesheet_override = qparams.get('rulesheet')

    #if rulesheet_override:
    #    handler = rulesheet(rulesheet_override[0], resource.resource_type, resolver=resolver).run(environ, 'GET', imt)
    #else:
    #    handler = resource.resource_type.run_rulesheet(environ, 'GET', imt)
    #start_response(status_response(status), [("Content-Type", ctype), (moin.ORIG_BASE_HEADER, moin_base_info)])


@dispatcher.method("PUT")
def put_resource(environ, start_response):
    setup_request(environ)
    # Keep inbound headers so we can forward to moinrest
    req_headers = copy_headers_to_dict(environ)

    #Set up to use HTTP auth for all wiki requests
    baseuri = environ['SCRIPT_NAME'].rstrip('/') #$ServerPath/zen
    handler = copy_auth(environ, baseuri)
    creds = extract_auth(environ)
    opener = urllib2.build_opener(handler) if handler else urllib2.build_opener()
    #Pass on the full moinrest and zen base URIs for the resources accessed on this request
    environ['zen.RESOURCE_URI'] = join(zenlib.moinmodel.ZEN_BASEURI, environ['PATH_INFO'].lstrip('/').split('/')[0])
    environ['moinrest.RESOURCE_URI'] = join(zenlib.moinmodel.MOINREST_BASEURI, environ['PATH_INFO'].lstrip('/').split('/')[0])

    H = httplib2.Http('/tmp/.cache')
    zenlib.moinmodel.H = H

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
    resource_type = node.lookup(rtype, opener=opener, environ=environ)
    
    temp_fpath = read_http_body_to_temp(environ, start_response)
    body = open(temp_fpath, "r").read()

    handler = resource_type.run_rulesheet(environ, 'PUT', imt)
    wikified = handler(resource_type, body)
    #logger.debug('put_resource wikified result: ' + repr((wikified,)))

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
    setup_request(environ)
    # Keep inbound headers so we can forward to moinrest
    req_headers = copy_headers_to_dict(environ)

    #Set up to use HTTP auth for all wiki requests
    baseuri = environ['SCRIPT_NAME'].rstrip('/') #'/zen' ; note: does not include $ServerPath
    handler = copy_auth(environ, baseuri)
    creds = extract_auth(environ)
    opener = urllib2.build_opener(handler) if handler else urllib2.build_opener()
    #Pass on the full moinrest and zen base URIs for the resources accessed on this request
    environ['zen.RESOURCE_URI'] = join(zenlib.moinmodel.ZEN_BASEURI, environ['PATH_INFO'].lstrip('/').split('/')[0])
    environ['moinrest.RESOURCE_URI'] = join(zenlib.moinmodel.MOINREST_BASEURI, environ['PATH_INFO'].lstrip('/').split('/')[0])

    H = httplib2.Http('/tmp/.cache')
    zenlib.moinmodel.H = H

    #import pprint; logger.debug('put_resource input environ: ' + repr(pprint.pformat(environ)))
    imt = environ['CONTENT_TYPE']

    resource_type = node.lookup(zenuri_to_moinrest(environ), opener=opener, environ=environ)
    if not resource_type:
        start_response(status_response(400),[('Content-Type','text/plain')])
        return( "Unable to access resource\n" )

    resolver = resource_type.resolver
    
    temp_fpath = read_http_body_to_temp(environ, start_response)
    body = open(temp_fpath, "r").read()

    handler = resource_type.run_rulesheet(environ, 'POST', imt)
    new_uri, wikified = handler(resource_type, body)
    #logger.debug('post_resource wikified result & uri: ' + repr((wikified, new_uri)))

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
    setup_request(environ)
    # Keep inbound headers so we can forward to moinrest
    req_headers = copy_headers_to_dict(environ)

    H = httplib2.Http('/tmp/.cache')
    zenlib.moinmodel.H = H

    H.force_exception_to_status_code = True

    creds = extract_auth(environ)
    if creds:
        user, passwd = creds
        H.add_credentials(user, passwd)

    resp, content = H.request(zenuri_to_moinrest(environ), "DELETE", headers=req_headers)

    start_response(status_response(resp.status), [("Content-Type", resp['content-type'])])
    return content
