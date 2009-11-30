# -*- coding: iso-8859-1 -*-
# 
"""
z_zen.py

Accesses a Moin wiki (via the Akara moinrest wrapper) to use as a source for a
authoring and metadata aextraction

Based on Moin/CMS (see http://wiki.xml3k.org/Akara/Services/MoinCMS )

Copyright 2009 Uche Ogbuji
This file is part of the open source Akara project,
provided under the Apache 2.0 license.
See the files LICENSE and NOTICE for details.
Project home, documentation, distributions: http://wiki.xml3k.org/Akara

@copyright: 2009 by Uche ogbuji <uche@ogbuji.net>
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

from akara.util import copy_auth
from akara.util.moin import node, ORIG_BASE_HEADER, DOCBOOK_IMT, RDF_IMT, HTML_IMT
from akara.services import simple_service
from akara import logger

endpoints = AKARA.module_config.get('endpoints')
node.ENDPOINTS = endpoints and eval(endpoints)
#logger.debug('GRIPPO: ' + repr((endpoints, eval(endpoints))))
logger.debug('GRIPPO: ' + repr((endpoints, )))


#DEFAULT_TZ = pytz.timezone('UTC')
UTC = pytz.timezone('UTC')
DEFAULT_LOCAL_TZ = pytz.timezone('UTC')


#aname = partial(property_sequence_getter, u"name")
#aemail = partial(property_sequence_getter, u"email")
#auri = partial(property_sequence_getter, u"uri")

UNSUPPORTED_IN_FILENAME = re.compile('\W')
#SOURCE = AKARA_MODULE_CONFIG['source-wiki-root']
#POST_TO = AKARA_MODULE_CONFIG['post-to']

class preservationresource(node):
    AKARA_TYPE = 'http://community.zepheira.com/wiki/loc/Portaldata/preservationresource'
    #FIXME: Stupid Moin bug (docbook output links broken)
    AKARA_TYPE = 'http://community.zepheira.com/wiki/loc/wiki/loc/Portaldata/preservationresource#'
    def render(self):
        '''
        '''
        doc, metadata, original_wiki_base = self.cache
        #metadata = doc.article.xml_model.generate_metadata(doc)
        #import pprint
        #pprint.pprint(resources)
        #amara.xml_print(doc, stream=sys.stderr, indent=True)
        #header = doc.article.glosslist[0]
        name = doc.article.xml_select(u'string(section[title = "preservationresource:name"]/para)').strip()
        ejson = {
            'type': self.AKARA_TYPE,
            'id': self.rest_uri,
            'label': name,
            'type_name': 'Preservation Resource',
            'tags': [ unicode(t) for t in doc.article.xml_select(u'section[title = "preservationresource:tags"]//itemizedlist/listitem/para')],
            'link': doc.article.xml_select(u'string(section[title = "preservationresource:link"]/para//ulink/@url)'),
            'description': doc.article.xml_select(u'string(section[title = "preservationresource:description"]/para)'),
            'topic_name': doc.article.xml_select(u'string(section[title = "preservationresource:topic"]/para//ulink)'),
            'topic_link': doc.article.xml_select(u'string(section[title = "preservationresource:topic"]/para//ulink/@url)'),
            'project_name': doc.article.xml_select(u'string(section[title = "preservationresource:project"]/para//ulink)'),
            'project_link': doc.article.xml_select(u'string(section[title = "preservationresource:project"]/para//ulink/@url)'),
            'parent_name': doc.article.xml_select(u'string(section[title = "preservationresource:parent"]/para//ulink)'),
            'parent_link': doc.article.xml_select(u'string(section[title = "preservationresource:parent"]/para//ulink/@url)'),
            #'thumbnail': header.xml_select(u'string(glossentry[glossterm = "thumbnail"]/glossdef//ulink/@url)'),
            #'tags': [ unicode(tag).strip() for tag in doc.article.xml_select(u'section[title = "collection:tags"]//para')],
        }
        #print >> sys.stderr, 'FINFO ', freemix_info
        return ejson

    def meta(self):
        #Create ouput file
        doc = bindery.parse(source, model=AK_DOCBOOK_MODEL)

node.NODES[preservationresource.AKARA_TYPE] = preservationresource


class organization(node):
    AKARA_TYPE = 'http://community.zepheira.com/wiki/loc/Portaldata/organization'
    #FIXME: Stupid Moin bug (docbook output links broken)
    AKARA_TYPE = 'http://community.zepheira.com/wiki/loc/wiki/loc/Portaldata/organization#'
    def render(self):
        '''
        '''
        doc, metadata, original_wiki_base = self.cache
        #metadata = doc.article.xml_model.generate_metadata(doc)
        #import pprint
        #pprint.pprint(resources)
        #amara.xml_print(doc, stream=sys.stderr, indent=True)
        #header = doc.article.glosslist[0]
        name = doc.article.xml_select(u'string(section[title = "organization:name"]/para)').strip()
        ejson = {
            'type': self.AKARA_TYPE,
            'id': self.rest_uri,
            'label': name,
            'type_name': 'Organization',
            'location': doc.article.xml_select(u'string(section[title = "organization:location"]/para)'),
            'homepage': doc.article.xml_select(u'string(section[title = "organization:homepage"]/para//ulink/@url)'),
            'contacts': [ unicode(c) for c in doc.article.xml_select(u'section[title = "organization:contact"]//itemizedlist/listitem/para')],
            'project_name': doc.article.xml_select(u'string(section[title = "organization:project"]/para//ulink)'),
            'project_link': doc.article.xml_select(u'string(section[title = "organization:project"]/para//ulink/@url)'),
            #'id': doc.article.xml_select(u'string(section[title = "organization:id"]/para//ulink/@url)'),
            #'thumbnail': header.xml_select(u'string(glossentry[glossterm = "thumbnail"]/glossdef//ulink/@url)'),
            #'tags': [ unicode(tag).strip() for tag in doc.article.xml_select(u'section[title = "collection:tags"]//para')],
        }
        #print >> sys.stderr, 'FINFO ', freemix_info
        return ejson

    def meta(self):
        #Create ouput file
        doc = bindery.parse(source, model=AK_DOCBOOK_MODEL)

node.NODES[organization.AKARA_TYPE] = organization


class project(node):
    AKARA_TYPE = 'http://community.zepheira.com/wiki/loc/Portaldata/project'
    #FIXME: Stupid Moin bug (docbook output links broken)
    AKARA_TYPE = 'http://community.zepheira.com/wiki/loc/wiki/loc/Portaldata/project#'
    def render(self):
        '''
        '''
        doc, metadata, original_wiki_base = self.cache
        #metadata = doc.article.xml_model.generate_metadata(doc)
        #import pprint
        #pprint.pprint(resources)
        #amara.xml_print(doc, stream=sys.stderr, indent=True)
        #header = doc.article.glosslist[0]
        name = doc.article.xml_select(u'string(section[title = "project:name"]/para)').strip()
        ejson = {
            'type': self.AKARA_TYPE,
            'id': self.rest_uri,
            'label': name,
            'type_name': 'Project',
            'description': doc.article.xml_select(u'string(section[title = "project:description"]/para)'),
            'topic_name': doc.article.xml_select(u'string(section[title = "project:topic"]/para//ulink)'),
            'topic_link': doc.article.xml_select(u'string(section[title = "project:topic"]/para//ulink/@url)'),
            'parent_name': doc.article.xml_select(u'string(section[title = "project:parent"]/para//ulink)'),
            'parent_link': doc.article.xml_select(u'string(section[title = "project:parent"]/para//ulink/@url)'),
            'parentpartners': [ unicode(t) for t in doc.article.xml_select(u'section[title = "project:parentpartners"]//itemizedlist/listitem/para')],
            'thumbnail': doc.article.xml_select(u'string(section[title = "project:thumbnail"]/para//inlinemediaobject/imageobject/imagedata/@fileref)'),
            #'parentpartner_urls': [ t.xml_value for t in doc.article.xml_select(u'section[title = "project:parentpartners"]//itemizedlist/listitem/para//ulink/@url')],
            #'thumbnail': header.xml_select(u'string(glossentry[glossterm = "thumbnail"]/glossdef//ulink/@url)'),
            #'tags': [ unicode(tag).strip() for tag in doc.article.xml_select(u'section[title = "collection:tags"]//para')],
        }
        print >> sys.stderr, doc.article.xml_select(u'string(section[title = "project:thumbnail"]/para//inlinemediaobject/imageobject/imagedata/@fileref)')
        return ejson

    def meta(self):
        #Create ouput file
        doc = bindery.parse(source, model=AK_DOCBOOK_MODEL)

node.NODES[project.AKARA_TYPE] = project


class topic(node):
    AKARA_TYPE = 'http://community.zepheira.com/wiki/loc/Portaldata/topic'
    #FIXME: Stupid Moin bug (docbook output links broken)
    AKARA_TYPE = 'http://community.zepheira.com/wiki/loc/wiki/loc/Portaldata/topic#'
    def render(self):
        '''
        '''
        doc, metadata, original_wiki_base = self.cache
        #metadata = doc.article.xml_model.generate_metadata(doc)
        #import pprint
        #pprint.pprint(resources)
        #amara.xml_print(doc, stream=sys.stderr, indent=True)
        #header = doc.article.glosslist[0]
        name = doc.article.xml_select(u'string(section[title = "topic:name"]/para)').strip()
        ejson = {
            'type': self.AKARA_TYPE,
            'id': self.rest_uri,
            'label': name,
            'type_name': 'Topic',
            'description': doc.article.xml_select(u'string(section[title = "topic:description"]/para)'),
            #'thumbnail': header.xml_select(u'string(glossentry[glossterm = "thumbnail"]/glossdef//ulink/@url)'),
            #'tags': [ unicode(tag).strip() for tag in doc.article.xml_select(u'section[title = "collection:tags"]//para')],
        }
        #print >> sys.stderr, 'FINFO ', freemix_info
        return ejson

    def meta(self):
        #Create ouput file
        doc = bindery.parse(source, model=AK_DOCBOOK_MODEL)

node.NODES[topic.AKARA_TYPE] = topic


class view(node):
    AKARA_TYPE = 'http://community.zepheira.com/wiki/loc/Portaldata/view'
    #FIXME: Stupid Moin bug (docbook output links broken)
    AKARA_TYPE = 'http://community.zepheira.com/wiki/loc/wiki/loc/Portaldata/view#'
    def render(self):
        '''
        '''
        doc, metadata, original_wiki_base = self.cache
        #metadata = doc.article.xml_model.generate_metadata(doc)
        #import pprint
        #pprint.pprint(resources)
        #amara.xml_print(doc, stream=sys.stderr, indent=True)
        #header = doc.article.glosslist[0]
        name = doc.article.xml_select(u'string(section[title = "view:name"]/para)').strip()
        ejson = {
            'type': self.AKARA_TYPE,
            'id': self.rest_uri,
            'label': name,
            'type_name': 'View',
            'date-created': doc.article.xml_select(u'string(section[title = "view:date-created"]/para)'),
            'link': doc.article.xml_select(u'string(section[title = "view:link"]/para//ulink/@url)'),
            #'thumbnail': doc.article.xml_select(u'string(section[title = "view:thumbnail"]/para//inlinemediaobject/imageobject/imagedata/fileref/@url)'),
            'preservationresource_name': doc.article.xml_select(u'string(section[title = "view:preservationresource"]/para//ulink)'),
            'preservationresource_link': doc.article.xml_select(u'string(section[title = "view:preservationresource"]/para//ulink/@url)'),
            'restrictions': doc.article.xml_select(u'string(section[title = "view:restrictions"]/para)'),
            #'tags': [ unicode(tag).strip() for tag in doc.article.xml_select(u'section[title = "collection:tags"]//para')],
        }
        #print >> sys.stderr, 'FINFO ', freemix_info
        return ejson

    def meta(self):
        #Create ouput file
        doc = bindery.parse(source, model=AK_DOCBOOK_MODEL)

node.NODES[view.AKARA_TYPE] = view


class collection(node):
    AKARA_TYPE = 'http://purl.org/dc/gov/loc/recollection/collection'
    def __init__(self, rest_uri, opener):
        self.rest_uri = rest_uri
        self.opener = opener
        #from node.factory
        req = urllib2.Request(rest_uri, headers={'Accept': DOCBOOK_IMT})
        print >> sys.stderr, 'rest_uri: ', rest_uri
        resp = opener.open(req)
        doc = bindery.parse(resp, standalone=True, model=MOIN_DOCBOOK_MODEL)
        original_wiki_base = dict(resp.info())[ORIG_BASE_HEADER]
        #self.original_wiki_base = dict(resp.info())[ORIG_BASE_HEADER]
        #amara.xml_print(self.content_cache)
        metadata = metadata_dict(generate_metadata(doc))
        self.cache=(doc, metadata, original_wiki_base)
        return

    def up_to_date(self, force_update=False):
        '''
        Checks whether there needs to be an update of the output
        '''
        return False

    def render(self):
        '''
        '''
        doc, metadata, original_wiki_base = self.cache
        #metadata = doc.article.xml_model.generate_metadata(doc)
        #import pprint
        #pprint.pprint(resources)
        #amara.xml_print(doc, stream=sys.stderr, indent=True)
        header = doc.article.glosslist[0]
        freemix_info = {
            'id': self.rest_uri,
            'label': self.rest_uri,
            'title': doc.article.xml_select(u'string(section[title = "collection:title"]/para)'),
            'date-created': header.xml_select(u'string(glossentry[glossterm = "date-created"]/glossdef)'),
            'description': doc.article.xml_select(u'string(section[title = "collection:description"]/para)'),
            'link': header.xml_select(u'string(glossentry[glossterm = "link"]/glossdef//ulink/@url)'),
            'original_site': doc.article.xml_select(u'string(section[title = "collection:original site"]/para)'),
            'organization': doc.article.xml_select(u'string(section[title = "collection:organization"]/para)'),
            'restrictions': doc.article.xml_select(u'string(section[title = "collection:restrictions"]/para)'),
            'content': doc.article.xml_select(u'string(section[title = "collection:content"]/para)').strip(),
            'thumbnail': header.xml_select(u'string(glossentry[glossterm = "thumbnail"]/glossdef//ulink/@url)'),
            'tags': [ unicode(tag).strip() for tag in doc.article.xml_select(u'section[title = "collection:tags"]//para')],
            'data': [ unicode(data).strip() for tag in doc.article.xml_select(u'section[title = "collection:data"]//para')],
        }
        #print >> sys.stderr, 'FINFO ', freemix_info
        return freemix_info

    def meta(self):
        #Create ouput file
        doc = bindery.parse(source, model=AK_DOCBOOK_MODEL)

node.NODES[collection.AKARA_TYPE] = collection
#AKARA_TYPES = [page, folder]
#print >> sys.stderr, 'Writing to ', POST_TO

SELF = AKARA.module_config.get('self', 'http://localhost:8880/')
REST_WIKI_BASE = AKARA.module_config.get('rest_wiki_base', 'http://localhost:8880/moin/loc/')


def wrapped_uri(original_wiki_base, link):
    abs_link = absolutize(link, original_wiki_base)
    #print >> sys.stderr, 'abs_link: ', abs_link
    rel_link = relativize(abs_link, original_wiki_base)
    #print >> sys.stderr, 'rel_link: ', rel_link
    rest_uri = absolutize(rel_link, REST_WIKI_BASE)
    #print >> sys.stderr, 'rest_uri: ', rest_uri
    return rest_uri, abs_link

TOP_REQUIRED = _("The 'top' query parameter is mandatory.")


SERVICE_ID = 'http://purl.org/akara/services/builtin/zen.index'
@simple_service('GET', SERVICE_ID, 'zen.index.json', 'application/json')
def zen_index(top=None):
    '''
    curl "http://localhost:8880/zen.index.json?top=http://example.com"
    '''
    #Useful: http://www.voidspace.org.uk/python/articles/authentication.shtml
    #curl "http://localhost:8880/zen.index.json?top=http://community.zepheira.com/wiki/loc/LoC/Collections/"
    from akara import request
    #top = first_item(top, next=partial(assert_not_equal, None, msg=TOP_REQUIRED))
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
    for navchild in doc.xml_select(u'//*[@class="navigation"]//@href'):
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
            request = urllib2.Request(endpoint + '?' + query, body)
            rendered = opener.open(request).read()
            logger.debug('jsonizer result: ' + repr(rendered))
        if rendered:
            items.append(rendered)
    return simplejson.dumps({'items': items}, indent=4)

