# -*- coding: iso-8859-1 -*-
# 
"""

See: http://wiki.xml3k.org/Akara/Services/MoinCMS

Copyright 2009 Uche Ogbuji
This file is part of the open source Akara project,
provided under the Apache 2.0 license.
See the files LICENSE and NOTICE for details.
Project home, documentation, distributions: http://wiki.xml3k.org/Akara

@copyright: 2009 by Uche ogbuji <uche@ogbuji.net>



T = ''' title::  httplib2 0.6.0 
 last changed:: 2009-12-28T13:06:56-05:00
 link:: http://bitworking.org/news/2009/12/httplib2-0.6.0
= Summary =
None
= akara:metadata =
 akara:type:: http://purl.org/com/zepheira/zen/resource/webfeed
'''

from amara.tools.creoletools import parse
from amara.writers import lookup
from zenlib import moinmodel

doc = parse(T)
#doc.xml_write(lookup('xml-indent'))
n = moinmodel.node(doc, 'http://localhost:8880/moin/mywiki/spam/eggs', 'http://localhost:8080/spam/eggs')
print n.akara_type()

"""

import datetime
import urllib, urllib2
from gettext import gettext as _

from dateutil.parser import parse as dateparse

import amara
from amara import bindery
from amara.lib.util import first_item
from amara.lib import inputsource
#from amara import inputsource as baseinputsource
from amara.lib.irihelpers import resolver as baseresolver
#from amara.namespaces import *
#from amara.xslt import transform
#from amara.writers.struct import *
#from amara.bindery.html import parse as htmlparse
from amara.lib import U
from amara.lib.iri import split_fragment, relativize, absolutize, IriError
#from amara.bindery.model import examplotron_model, generate_metadata, metadata_dict
from amara.bindery.util import dispatcher, node_handler, property_sequence_getter

from akara.util import copy_auth
from akara.util.moin import wiki_uri, ORIG_BASE_HEADER, DOCBOOK_IMT, RDF_IMT, HTML_IMT

try:
    from akara import logger
except ImportError:
    logger = None

def cleanup_text_blocks(text):
    return '\n'.join([line.strip() for line in text.splitlines() ])

#class construct(object):
#    '''
#    A data construct derived from a Moin wiki page
#    '''
#    def load(self):
#        raise NotImplementedError

class resolver(baseresolver):
    """
    Resolver that uses a specialized URL opener
    """
    def __init__(self, authorizations=None, lenient=True, opener=None):
        """
        """
        self.opener = opener or urllib2.build_opener()
        self.last_lookup_headers = None
        baseresolver.__init__(self, authorizations, lenient)

    def resolve(self, uri, base=None):
        if not isinstance(uri, urllib2.Request):
            if base is not None:
                uri = self.absolutize(uri, base)
            req = urllib2.Request(uri)
        else:
            req, uri = uri, uri.get_full_url()
        try:
            #stream = self.opener(uri)
            resp = self.opener.open(req)
            stream = resp
            self.last_lookup_headers = resp.info()
        except IOError, e:
            raise IriError(IriError.RESOURCE_ERROR,
                               uri=uri, loc=uri, msg=str(e))
        return stream


#FIXME: consolidate URIs, opener, etc. into an InputSource derivative
#class inputsource(baseinputsource):
#    def __new__(cls, arg, uri=None, encoding=None, resolver=None, sourcetype=0, opener=None):
#       isrc = baseinputsource.__new__(cls, arg, uri, encoding, resolver, sourcetype)
#        isrc.opener = opener
#        return isrc

#    def __init__(self, arg, uri=None, encoding=None, resolver=None, sourcetype=0, opener=None):
#        baseinputsource.__init__(cls, arg, uri, encoding, resolver, sourcetype)

def akara_type(doc, original_base, wrapped_base, rest_uri):
    #type = U(doc.xml_select(u'//definition_list/item[term = "akara:type"]/defn'))
    if logger: logger.debug('Type: ' + repr(list(doc.xml_select(u'//*[@title="akara:metadata"]/gloss/label[.="akara:type"]/following-sibling::item[1]//@href'))))
    type = U(doc.xml_select(u'//*[@title="akara:metadata"]/gloss/label[.="akara:type"]/following-sibling::item[1]//@href'))
    wrapped_type, orig_type = wiki_uri(original_base, wrapped_base, type, rest_uri)
    if logger: logger.debug('Type URIs: ' + repr((type, wrapped_type, orig_type)))
    return wrapped_type

UNSPECIFIED = object()

class node(object):
    '''
    Akara Moin/CMS node, a Moin wiki page that follows a template to direct workflow
    activity, including metadata extraction
    '''
    AKARA_TYPE = u'http://purl.org/xml3k/akara/cms/resource-type'
    NODES = {}
    #Processing priority
    #PRIORITY = 0
    ENDPOINTS = None
    @staticmethod
    def factory(rest_uri, moin_link=None, opener=None):
        '''
        rest_uri - URI of the moinrest-wrapped version of the page
        moin_link - 
        opener - for specializing the HTTP request (e.g. to use auth)
        '''
        r = resolver(opener=opener)
        req = urllib2.Request(rest_uri, headers={'Accept': 'text/xml'})
        isrc = inputsource(req, resolver=r)
        if logger: logger.debug('rest_uri: ' + rest_uri)
        doc = bindery.parse(isrc)
        #doc = bindery.parse(isrc, standalone=True, model=MOIN_DOCBOOK_MODEL)
        if logger: logger.debug('r.last_lookup_headers: ' + repr((r, r.last_lookup_headers)))
        original_base, wrapped_base, original_page = r.last_lookup_headers[ORIG_BASE_HEADER].split()
        #self.original_wiki_base = dict(resp.info())[ORIG_BASE_HEADER]
        #amara.xml_print(self.content_cache)
        #metadata, first_id = metadata_dict(generate_metadata(doc))
        #metadata = metadata[first_id]
        #akara_type = U(metadata[u'ak-type'])
        atype = akara_type(doc, original_base, wrapped_base, rest_uri)
        #akara_type = U(doc.xml_select(u'//*[@title="akara:metadata"]/gloss/label[.="akara:type"]/following-sibling::item[1]//@href'))
        #if logger: logger.debug('Type: ' + akara_type)
        #Older Moin CMS resource types are implemented by registration to the global node.NODES
        #Newer Moin CMS resource types are implemented by discovery of a URL,
        #to which a POST request executes the desired action
        cls = node.NODES.get(atype, node)
        instance = cls(doc, rest_uri, moin_link, original_base, wrapped_base, akara_type=akara_type, resolver=r)
        return instance
        #return node.ENDPOINTS and (rest_uri, akara_type, node.ENDPOINTS[akara_type], doc, metadata, original_wiki_base)

    #FIXME: This cache is to help eliminate unnecessary trips back to moin to get
    #The page body.  It should soon be replaced by the proposed comprehensive caching
    def __init__(self, doc, rest_uri, moin_link, original_base, wrapped_base, akara_type=None, resolver=None):
        '''
        rest_uri - the full URI to the Moin/REST wrapper for this page
        relative - the URI of this page relative to the Wiki base
        '''
        self.doc = doc
        self.rest_uri = rest_uri
        self.moin_link = moin_link
        self.original_base = original_base
        self.wrapped_base = wrapped_base
        self.resolver = resolver
        self.rulesheet = None
        if node.ENDPOINTS and akara_type in node.ENDPOINTS:
            self.endpoint = node.ENDPOINTS[akara_type]
        else:
            self.endpoint = None
        return

    def load(self):
        raise NotImplementedError

    #def render(self):
    #    raise NotImplementedError

    def get_rulesheet(self):
        if self.rulesheet is None:
            #req = urllib2.Request(self.akara_type(), headers={'Accept': 'text/xml'})
            #isrc = inputsource(req, resolver=self.resolver)
            #Stupid Moin XML export uses bogus nbsps, so we can't use the above
            req = urllib2.Request(self.akara_type(), headers={'Accept': 'text/xml'})
            result = urllib2.urlopen(req)
            body = result.read()
            isrc = inputsource(body.replace('&nbsp;', '&#160;'), resolver=self.resolver)
            if logger: logger.debug('akara type rest_uri: ' + self.akara_type())
            #req = urllib2.Request(rest_uri, headers={'Accept': DOCBOOK_IMT})
            doc = bindery.parse(isrc)
            rulesheet = U(doc.xml_select(u'//*[@title="akara:metadata"]/gloss/label[.="akara:rulesheet"]/following-sibling::item[1]//@href'))
            self.rulesheet = rulesheet or UNSPECIFIED
            if logger: logger.debug('RULESHEET: ' + rulesheet)
        return self.rulesheet

    #def run_rulesheet(self, imt='application/json'):
        #FIXME: actually 
        #(node_uri, node_type, endpoint, doc, metadata, original_wiki_base) = jsonizer
        #request = urllib2.Request(rest_uri, headers={'Accept': DOCBOOK_IMT})
        #body = opener.open(request).read()
        #logger.debug('rest_uri docbook body: ' + body[:200])
    #    query = urllib.urlencode({'node_uri': self.rest_uri, 'node_type': node_type, 'original_wiki_base': original_wiki_base, 'original_wiki_link': link})
        #FIXME: ugh. Reserialize and reparse
    #    req = urllib2.Request(endpoint + '?' + query, self.doc.xml_encode())
    #    output = opener.open(req).read()
        #logger.debug('jsonizer result: ' + repr(rendered))
    #    return output

    def run_rulesheet(self, phase='generate-json'):
        if self.endpoint:
            #(node_uri, node_type, endpoint, doc, metadata, original_wiki_base) = jsonizer
            #request = urllib2.Request(rest_uri, headers={'Accept': DOCBOOK_IMT})
            #body = opener.open(request).read()
            #logger.debug('rest_uri docbook body: ' + body[:200])
            query = urllib.urlencode({'node_uri': node_uri, 'node_type': node_type, 'original_wiki_base': original_wiki_base, 'original_wiki_link': link})
            #XXX this will lead to a re-parse of body/doc
            req = urllib2.Request(endpoint + '?' + query, body)
            output = opener.open(req).read()
            logger.debug('jsonizer result: ' + repr(rendered))
        else:
            #e.g. you can sign a rulesheet as follows:
            #python -c "import sys, hashlib; print hashlib.sha1('MYSECRET' + sys.stdin.read()).hexdigest()" < rsheet.py 
            #Make sure the rulesheet has not already been signed (i.e. does not have a hash on the first line)
            import hashlib
            rulesheet = self.get_rulesheet()
            rs = inputsource(rulesheet, resolver=self.resolver)
            token = rs.stream.readline().strip()
            #logger.debug('Token: ' + repr((token, self.SECRET)))
            body = rs.stream.read()
            if token != hashlib.sha1(self.SECRET + body).hexdigest():
                raise RuntimeError('Security token verification failed')
            #chunks = []
            def U1(text): return U(text, noneok=True)
            #def write(text):
            #    chunks.append(text)
            #env = {'write': write, 'resource': self, 'service': service, 'U': U1}
            env = {'resource': self, 'service': service, 'U': U1}
            exec body in env
            output = None
            if 'record' in env:
                output = env['record']()
            #output = ''.join(chunks)
        return output

    def up_to_date(self, force_update=False):
        '''
        Checks whether there needs to be an update of the output
        '''
        #By default just always update
        return False

    def akara_type(self):
        #metadata_section = doc.xml_xpath(u'header[. = "akara:metadata"]')
        #if metadata_section:
        #return doc.metadata_section
        return akara_type(self.doc, self.original_base, self.wrapped_base, self.rest_uri)
        #type = U(doc.xml_select(u'//definition_list/item[term = "akara:type"]/defn'))
        #return type

    def section(self, title):
        '''
        Helper to extract content from a specific section within the page
        '''
        #FIXME: rethink this "caching" business
        logger.debug("section_titled: " + repr(title))
        return first_item(self.doc.xml_select(u'//*[@title = "%s"]'%title))

    def definition_list(self, list_path, contextnode=None, patterns=None):
        '''
        Helper to construct a dictionary from an indicated definition list on the page
        '''
        #FIXME: rethink this "caching" business
        #Use defaultdict instead, for performance
        #patterns = patterns or {None: lambda x: U(x) if x else None}
        patterns = patterns or {None: lambda x: x}
        contextnode = contextnode or self.doc.s1
        top = contextnode.xml_select(list_path)
        if not top:
            return None
        #Go over the glossentries, and map from term to def, applying the matching
        #Unit transform function from the patterns dict
        result = dict((U(l), patterns.get(U(l), patterns[None])(first_item(l.xml_select(u'following-sibling::item'))))
                      for l in top[0].label)
        logger.debug("definition_list: " + repr(result))
        return result

    def definition_section(self, title, patterns=None):
        '''
        Helper to extract the first definition list from a named section
        '''
        return self.definition_list(u'.//gloss', contextnode=self.section(title), patterns=patterns)


node.NODES[node.AKARA_TYPE] = node

from zenlib import SERVICES

def service(url):
    return SERVICES[url]


#XXX: do we really need this function indirection for simple global dict assignment?
def register_node_type(type_id, nclass):
    node.NODES[type_id] = nclass

#

from zenlib import register_service

#Services for processing Moin pages
def get_link_urls(node):
    links = [ attr.xml_value for attr in node.xml_select(u'.//@href') ]
    return links
get_link_urls.serviceid = u'http://purl.org/com/zepheira/zen/moinmodel/get-link-urls'

register_service(get_link_urls)

def get_obj_urls(node):
    links = [ attr.xml_value for attr in node.xml_select(u'.//@src') ]
    return links
get_obj_urls.serviceid = u'http://purl.org/com/zepheira/zen/moinmodel/get-obj-urls'

register_service(get_obj_urls)

def jsonize(obj):
    import simplejson
    return simplejson.dumps(obj)
jsonize.serviceid = u'http://purl.org/com/zepheira/zen/exhibit/jsonize'

register_service(jsonize)

