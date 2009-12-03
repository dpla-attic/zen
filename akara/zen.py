# -*- coding: iso-8859-1 -*-
# 
"""
z_zen.py

Accesses a Moin wiki (via the Akara moinrest wrapper) to use as a source for a
authoring and metadata aextraction

Based on Moin/CMS (see http://wiki.xml3k.org/Akara/Services/MoinCMS )

@copyright: 2009 by Uche ogbuji <uche@ogbuji.net>

This file is part of the open source Akara project,
provided under the Apache 2.0 license.
See the files LICENSE and NOTICE for details.
Project home, documentation, distributions: http://wiki.xml3k.org/Akara

See:

 * http://purl.org/xml3k/akara
 * http://foundry.zepheira.com/projects/zen
 
@ 2009 by Uche ogbuji <uche@ogbuji.net>

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
import pprint
import httplib
import urllib, urllib2
import datetime
from itertools import islice
from wsgiref.util import request_uri

import simplejson
from dateutil.parser import parse as dateparse
import pytz

import amara
from amara import bindery, _
from amara.namespaces import *
from amara.bindery.model import examplotron_model, generate_metadata
from amara.writers.struct import *
from amara.bindery.html import parse as htmlparse
from amara.lib.iri import split_fragment, relativize, absolutize
from amara.bindery.util import dispatcher, node_handler, property_sequence_getter

from akara.registry import list_services, _current_registry
from akara.util import copy_auth
from akara.util.moin import node, ORIG_BASE_HEADER, DOCBOOK_IMT, RDF_IMT, HTML_IMT
from akara.services import simple_service
from akara import logger
from akara import request

#endpoints = AKARA.module_config.get('endpoints')
#node.ENDPOINTS = endpoints and eval(endpoints)
#logger.debug('GRIPPO: ' + repr((endpoints, eval(endpoints))))
#logger.debug('GRIPPO: ' + repr((endpoints, )))

#AKARA is automatically defined at global scope for a module running within Akara
MOINBASE = AKARA.module_config['moinrestbase']
#Make sure the URl ends with a / for graceful URL resolution
MOINBASE = MOINBASE.rstrip('/')+'/'
USER = AKARA.module_config.get('moin-user', None)
PASSWD = AKARA.module_config.get('moin-passwd', None)

#DEFAULT_TZ = pytz.timezone('UTC')
UTC = pytz.timezone('UTC')
DEFAULT_LOCAL_TZ = pytz.timezone('UTC')

#aname = partial(property_sequence_getter, u"name")
#aemail = partial(property_sequence_getter, u"email")
#auri = partial(property_sequence_getter, u"uri")

UNSUPPORTED_IN_FILENAME = re.compile('\W')
#SOURCE = AKARA_MODULE_CONFIG['source-wiki-root']
#POST_TO = AKARA_MODULE_CONFIG['post-to']

SELF_END_POINT = None

def find_peer_service(peer_path):
    global SELF_END_POINT
    if SELF_END_POINT is None:
        SELF_END_POINT = request_uri(request.environ, include_query=False)
    return SELF_END_POINT.rsplit('/', 1)[0] + '/' + peer_path


def wrapped_uri(original_wiki_base, link):
    abs_link = absolutize(link, original_wiki_base)
    #print >> sys.stderr, 'abs_link: ', abs_link
    rel_link = relativize(abs_link, original_wiki_base)
    #print >> sys.stderr, 'rel_link: ', rel_link
    rest_uri = absolutize(rel_link, MOINBASE)
    #print >> sys.stderr, 'rest_uri: ', rest_uri
    return rest_uri, abs_link

TOP_REQUIRED = _("The 'top' query parameter is mandatory.")


SERVICE_ID = 'http://purl.org/akara/services/builtin/zen.index'
@simple_service('GET', SERVICE_ID, 'zen.index.json', 'application/json')
def zen_index(top=None, maxcount=None):
    '''
    top - page on which to start looking for linked Zen resouces
    maxcount - limit to the number of records returned; unlimited by default

    curl "http://localhost:8880/zen.index.json?top=http://example.com"
    '''
    #Useful: http://www.voidspace.org.uk/python/articles/authentication.shtml
    #curl "http://localhost:8880/zen.index.json?top=http://community.zepheira.com/wiki/loc/LoC/Collections/"
    #top = first_item(top, next=partial(assert_not_equal, None, msg=TOP_REQUIRED))
    if node.ENDPOINTS is None:
        node.ENDPOINTS = dict(
            [ (s.ident, find_peer_service(path))
              for (path, s) in _current_registry._registered_services.iteritems()
            ])
        logger.debug('Node end-points: ' + repr(node.ENDPOINTS))

    handler = copy_auth(request.environ, top)
    opener = urllib2.build_opener(handler) if handler else urllib2.build_opener()
    req = urllib2.Request(top, headers={'Accept': HTML_IMT})
    resp = opener.open(req)
    body = resp.read()
    doc = htmlparse(body)
    original_wiki_base = dict(resp.info())[ORIG_BASE_HEADER]
    #wikibase, outputdir, rewrite, pattern
    #wikibase_len = len(rewrite)
    items = []
    hrefs = doc.xml_select(u'//*[@class="navigation"]//@href')
    if maxcount:
        hrefs = islice(hrefs, 0, int(maxcount))
    for navchild in hrefs:
        link = navchild.xml_value
        #print >> sys.stderr, 'LINK:', link
        #uri = split_fragment(item.resource)[0]
        #relative = uri[wikibase_len:]
        #print >> sys.stderr, uri, relative
        #if rewrite:
        #    uri = uri.replace(rewrite, wikibase)
        rest_uri, moin_link = wrapped_uri(original_wiki_base, link)
        jsonizer = node.factory(rest_uri, moin_link, opener)
        if isinstance(jsonizer, node):
            rendered = jsonizer.render()
        else:
            (node_uri, node_type, endpoint, doc, metadata, original_wiki_base) = jsonizer
            #request = urllib2.Request(rest_uri, headers={'Accept': DOCBOOK_IMT})
            #body = opener.open(request).read()
            logger.debug('rest_uri docbook body: ' + body[:200])
            query = urllib.urlencode({'node_uri': node_uri, 'node_type': node_type, 'original_wiki_base': original_wiki_base, 'original_wiki_link': link})
            #XXX this will lead to a re-parse of body/doc
            req = urllib2.Request(endpoint + '?' + query, body)
            rendered = opener.open(req).read()
            logger.debug('jsonizer result: ' + repr(rendered))
        if rendered:
            items.append(rendered)
    return simplejson.dumps({'items': items}, indent=4)

