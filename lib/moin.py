# -*- coding: iso-8859-1 -*-
# 
"""

"""

#Other ideas: http://textalyser.net/
# https://digitalresearchtools.pbworks.com/w/page/17801708/Text-Analysis-Tools
# 

import hashlib
import datetime
from gettext import gettext as _

from functools import partial
from itertools import islice, dropwhile

from amara.thirdparty import json, httplib2

from akara.util import status_response, requested_imt, header_credentials, extract_auth
#from akara.util.moin import wiki_uri, wiki_normalize, WSGI_ORIG_BASE_HEADER, XML_IMT
from akara.util.moin import wiki_uri, wiki_normalize, ORIG_BASE_HEADER, XML_IMT
from akara.services import convert_body, service_method_dispatcher

try:
    from akara import logger
except ImportError:
    logger = None

from zen import ZEN_SERVICE_ID

MOINREST_SERVICE_ID = 'http://purl.org/xml3k/akara/services/demo/moinrest'
#WSGI_ORIG_BASE_HEADER = 'HTTP_X_AKARA_WRAPPED_MOIN'
FIND_PEER_SERVICE_KEY = 'akara.FIND_PEER_SERVICE'

RESOURCE_TYPE_TYPE = u'http://purl.org/xml3k/akara/cms/resource-type'


class space(object):
    SERVICEID = 'http://purl.org/xml3k/akara/services/demo/moinrest'
    def __init__(self, initial_environ=None, **kwargs):
        '''
        initial_environ is the environment used from the first call to Zen for this space, which causes
        this space to be set up
        '''
        #Use akara discovery, via find_peer_service, to get the full base URI for this very
        #zen endpoint, and its moinrest peer
        #self.space_tag = kwargs['space_tag']
        if initial_environ:
            find_peer_service = initial_environ[FIND_PEER_SERVICE_KEY]
            self.MOINREST_BASEURI = find_peer_service(initial_environ, MOINREST_SERVICE_ID)
            self.ZEN_BASEURI = find_peer_service(initial_environ, ZEN_SERVICE_ID)
        return

    def forward(self, environ, start_response):
        '''
        Handle a forwarded call from Zen central, including the WSGI environ of the original invocation
        '''
        #Prepare the WSGI start_response function, which covers response headers and status
        self.slave_status = None
        self.slave_response_headers = None
        self.slave_exc_info = None
        self.environ = environ
        self.h = httplib2.Http('/tmp/.cache')

        #Set up utility environ variable for rulesheets
        self.environ['zen.RESOURCE_URI'] = join(self.ZEN_BASEURI, environ['PATH_INFO'].lstrip('/').split('/')[0])
        self.environ['moinrest.RESOURCE_URI'] = join(self.MOINREST_BASEURI, environ['PATH_INFO'].lstrip('/').split('/')[0])

        resource = self.resource_factory()
        #if logger: logger.debug('After moin call: ' + repr((response[:100], new_env['SCRIPT_NAME'], new_env['PATH_INFO'])))
        if not self.slave_status.startswith('20'):
            start_response(status_response(400), [('Content-Type','text/plain')])
            return ["Unable to access resource\n"]
        #handler = resource.resource_type.run_rulesheet(environ, 'GET', imt)

        imt = requested_imt(environ)

        handler = resource.type.run_rulesheet(environ, 'GET', imt)
        rendered = handler(resource)

        headers = [("Content-Type", str(handler.imt)),
                   ("Vary", "Accept")]
        if handler.ttl:
            headers.append(("Cache-Control", "max-age="+str(handler.ttl)))

        start_response(status_response(httplib.OK), self.slave_response_headers)
        return response

    def start_response_wrapper(self, status, response_headers, exc_info=None):
        self.slave_status = status
        self.slave_response_headers = response_headers
        self.slave_exc_info = exc_info
        def dummy_write(data):
            raise RuntimeError('Does not support the deprectated write() callable in WSGI clients')
        return dummy_write

    def resource_factory(self, path=None):
        '''
        Look up and retrieve a new resource based on WSGI environment or a uri path
        '''
        #Set up the environment with which we'll invoke the slave service (moin)
        environ = self.environ.copy()

        #We need to simulate a call to moinrest.  For example, an external caller to Akara invoking:
        #http://localhost:8880/moin/mywiki/MyPage
        #Gets forwarded eventually to the moinrest get_page function with:
        #(environ['SCRIPT_NAME'], environ['PATH_INFO']) = ('/moin', '/mywiki/MyPage')

        #Replace .../zen with .../moin
        environ['SCRIPT_NAME'] = environ['SCRIPT_NAME'].rsplit('/', 2)[0] + '/moin' #Should result in e.g. '/moin/mywiki'

        if path:
            #Then assume relative path to top of wiki, and add the moinrest wiki ID bit
            environ['PATH_INFO'] = '/' + self.space_tag + '/'+ path.lstrip('/') #e.g. '/MyPage'
        #else:
            #We're looking up the resource based on the WSGI environment of the original call to Zen
        #    environ['PATH_INFO'] = '/' + environ['PATH_INFO'].lstrip('/').rsplit(self.space_tag, 1)[1].lstrip('/') #e.g. '/mywiki/MyPage' -> '/MyPage'

        if logger: logger.debug('resource_factory ' + repr((environ['SCRIPT_NAME'], environ['PATH_INFO'])))

        #We handle XML fromt the wiki.  Requires the application_xml.py moin plugin that comes with Akara
        environ['HTTP_ACCEPT'] = XML_IMT

        response = self.service.handler(environ, self.start_response_wrapper)
        slave_wrapper = get_slave_wrapper(self.service.handler, environ)
        response, ctype, clength = convert_body(response, slave_wrapper.content_type, slave_wrapper.encoding, slave_wrapper.writer)
        response = response[0]
        if logger: logger.debug('resp ' + repr((response[:100],)))
        if not self.slave_status.startswith('20'):
            if logger: logger.debug("Error looking up resource: %s\n" % self.slave_status)
            return None

        doc = bindery.parse(inputsource.text(response)) #, model=MOIN_XML_MODEL
        moinrest_header = None
        for k, v in self.slave_response_headers:
            if k == ORIG_BASE_HEADER:
                moinrest_header = v
        #if logger: logger.debug('moinrest_header: ' + repr((moinrest_header,self.slave_response_headers)))
        original_base, wrapped_base, original_page = moinrest_header.split()
        rest_uri = join(wrapped_base, environ['PATH_INFO'].lstrip('/'))

        return resource.factory(self, rest_uri, doc, original_base, wrapped_base, original_page)

    #def parse_moin(new_env):
    #    '''Look up and retrieve a new resource based on '''
        #H.force_exception_to_status_code = True
        #headers={'Accept': XML_IMT}
        #if 'HTTP_CACHE_CONTROL' in environ:
        #    # Propagate any cache-control request header received by Zen
        #    headers['cache-control'] = environ['HTTP_CACHE_CONTROL']


def get_slave_wrapper(handler, environ):
    if isinstance(handler, service_method_dispatcher):
        return handler.method_table.get(environ.get("REQUEST_METHOD"))
    else:
        return handler


class resource(object):
    '''
    Akara Moin/CMS node, a Moin wiki page that follows a template to direct workflow
    activity, including metadata extraction
    '''
    AKARA_TYPE = u'http://purl.org/xml3k/akara/cms/resource-type'
    #NODES = {}
    #ENDPOINTS = None

    @staticmethod
    def factory(space, rest_uri, doc, original_base, wrapped_base, original_page, rtype=None):
        '''
        rest_uri - the full URI to the Moin/REST wrapper for this page
        relative - the URI of this page relative to the Wiki base
        
        it's a fatal error if this can't figure out the resource type
        '''
        #Primarily to decide whether to create a resource or a resource_type object
        if not rtype:
            rtype = resource.zen_type_path(rest_uri, doc)
        if rtype == RESOURCE_TYPE_TYPE:
            return resource_type(space, rest_uri, doc, original_base, wrapped_base, original_page, rtype=rtype)
        return resource(space, rest_uri, doc, original_base, wrapped_base, original_page, rtype=rtype)

        #
        #try:
        #    self.type = self.space.resource(rtype)
        #except (KeyboardInterrupt, SystemExit):
        #    raise
        #except Exception as e:
            #If there is an error looking up the resource type, just leave off.  Some operations will then fail
        #    if self.slave.logger: self.slave.logger.debug('Exception looking up resource type %s: %s'%(akara_type, repr(e)))
        #    pass
        #return

    def __init__(self, space, rest_uri, doc, original_base, wrapped_base, original_page, rtype=None):
        '''
        rest_uri - the full URI to the Moin/REST wrapper for this page
        relative - the URI of this page relative to the Wiki base
        '''
        self.doc = doc
        self.space = space
        self.rest_uri = rest_uri
        self.original_base = original_base
        self.wrapped_base = wrapped_base
        self.rulesheet = None
        
        if isinstance(rtype, basestring) and rtype != RESOURCE_TYPE_TYPE:
            self.type = space.resource_factory(rtype)
        else:
            self.type = rtype
        return

    #def render(self):
    #    raise NotImplementedError

    @staticmethod
    def zen_type_path(rest_uri, doc):
        #TYPE_PATTERN = u'//*[@title="akara:metadata"]/gloss/label[.="akara:type"]/following-sibling::item[1]//@href'
        #TYPE_PATTERN = u'//*[@title="akara:metadata"]/following-sibling::gloss/label[.="akara:type"]/following-sibling::item[1]//jump'
        #type = U(doc.xml_select(u'//definition_list/item[term = "akara:type"]/defn'))
        rtype = U(doc.xml_select(TYPE_PATTERN))
        if logger: logger.debug('zen_type: ' + repr(rtype))
        return rtype or None

    @staticmethod
    def zen_type_id(rest_uri, doc, original_base, wrapped_base, original_page):
        rtype = resource.zen_type_path(rest_uri, doc)
        if not rtype: return None
        wrapped_type, orig_type = wiki_uri(original_base, wrapped_base, rtype, rest_uri, raw=True)
        if logger: logger.debug('resource_type.construct_id wiki_uri trace: ' + repr((wrapped_type, original_base, wrapped_base, rest_uri)))
        return wrapped_type or rtype

    def section(self, title):
        '''
        Helper to extract content from a specific section within the page
        '''
        #FIXME: rethink this "caching" business
        #logger.debug("section_titled: " + repr(title))
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
        #logger.debug("definition_list: " + repr(result))
        return result

    def definition_section(self, title, patterns=None):
        '''
        Helper to extract the first definition list from a named section
        '''
        return self.definition_list(u'.//gloss', contextnode=self.section(title), patterns=patterns)

    def get_proxy(self, environ, method, accept=None):
        return self.resource_type.run_rulesheet(environ, method, accept)

    def absolute_wrap(self, link):
        link = '/' + link.lstrip('/')
        #if logger: logger.debug('absolute_wrap: ' + repr((self.original_base, self.wrapped_base, link, self.rest_uri)))
        wrapped_link, orig_link = wiki_uri(self.original_base, self.wrapped_base, link, self.rest_uri)
        #if logger: logger.debug('absolute_wrap: ' + repr((link, wrapped_link, orig_link)))
        return wrapped_link


UNSPECIFIED = object()

TYPE_PATTERN = u'//*[@title="akara:metadata"]/gloss/label[.="akara:type"]/following-sibling::item[1]//jump/@url'
RULESHEET_LINK_PATTERN = u'//*[@title="akara:metadata"]/gloss/label[.="akara:rulesheet"]/following-sibling::item[1]//jump/@url'
RULESHEET_ATT_PATTERN = u'//*[@title="akara:metadata"]/gloss/label[.="akara:rulesheet"]/following-sibling::item[1]//attachment/@href'

class resource_type(resource):
    def get_rulesheet(self):
        if self.rulesheet is None:
            #req = urllib2.Request(self.akara_type(), headers={'Accept': XML_IMT})
            #isrc = inputsource(req, resolver=self.resolver)
            rulesheet_link = U(self.doc.xml_select(RULESHEET_LINK_PATTERN))
            if rulesheet_link and not is_absolute(rulesheet_link):
                wrapped, orig = wiki_uri(self.original_base, self.wrapped_base, rulesheet_link, self.rest_uri)
                self.rulesheet = wrapped
            elif rulesheet_link:
                self.rulesheet = rulesheet_link
            else:
                rulesheet_att = U(self.doc.xml_select(RULESHEET_ATT_PATTERN))
                if rulesheet_att:
                    self.rulesheet = self.rest_uri + u';attachment=' + rulesheet_att
                else:
                    if logger: logger.debug("GRIPPO: " + repr((self.doc.xml_encode(),)))
                    self.rulesheet = UNSPECIFIED

            if self.space: self.space.logger.debug('resource_type.get_rulesheet rest_uri, rulesheet: ' + repr((self.rest_uri, self.rulesheet)))
        return self.rulesheet
    
    def run_rulesheet(self, environ, method='GET', accept='application/json'):
        #FIXME: Deprecate
        auth = extract_auth(environ)
        return rulesheet(self.get_rulesheet(), self.space, auth).run(environ, method, accept)


class rulesheet(object):
    def __init__(self, source, space, auth):
        '''
        '''
        #rs = inputsource(source, resolver=resolver)
        #self.token = rs.stream.readline().strip().lstrip('#')
        import cStringIO
        h = httplib2.Http('/tmp/.cache')
        if auth:
            user, passwd = auth
            h.add_credentials(user, passwd)
        resp, body = h.request(source)
        stream = cStringIO.StringIO(body)
        self.token = stream.readline().strip().lstrip('#')

        #XXX In theory this is a microscopic security hole.  If someone could find a way
        #to open up an expliot by changing whitespace *in the middle of the line*
        #(wiki_normalize does not touch WS at the beginning of a line)
        #In practice, we accept this small risk
        self.body = wiki_normalize(stream.read())
        self.space = space
        return

    def run(self, environ, method='GET', accept='application/json'):
        #e.g. you can sign a rulesheet as follows:
        #python -c "import sys, hashlib; print hashlib.sha1('MYSECRET' + sys.stdin.read()).hexdigest()" < rsheet.py 
        #Make sure the rulesheet has not already been signed (i.e. does not have a hash on the first line)
        rheet_sig = hashlib.sha1(self.space.SECRET + self.body).hexdigest()
        if self.token != rheet_sig:
            if logger: logger.debug("Computed signature: " + repr(rheet_sig))
            raise RuntimeError('Security token verification failed')
        #chunks = []
        #U1 is just a smarter variant of the "Unicode, dammit!"
        def U1(text): return U(text, noneok=True)
        #def write(text):
        #    chunks.append(text)

        handlers = {}
        #Decorator that allows the user to define request handler functions in rule sheets
        def handles(method, match=None, ttl=3600):
            '''
            method - HTTP method for this handler to use, e.g. 'GET' or 'PUT'
                     Might be a non-standard, internal method for special cases (e.g. 'collect')
            match - condition to determine when this handler is to be invoked for a given method
                    if a Unicode object, this should be an IMT to compare to the Accept info for the request
                    if a callable, should have signature match(accept), return ing True or False
            ttl - time-to-live for (GET) requests, for setting cache-control headers
            '''
            def deco(func):
                func.ttl = ttl
                # Set appropriate default media type when no match is specified in @handles
                if match is None :
                    func.imt = 'application/json'
                else :
                    func.imt = match
                handlers.setdefault(method, []).append((match, func))
                return func
            return deco

        #env = {'write': write, 'resource': self, 'service': service, 'U': U1}
        
        #resource_getter = partial(node.lookup, resolver=self.rtype.resolver)
        resource_getter = self.space.resource_factory
        env = {'service': service_proxy, 'U': U1, 'handles': handles, 'R': resource_getter,
                'use': use, 'environ': environ, 'logger': logger, 'H': self.space.h}

        #Execute the rule sheet
        exec self.body in env
        default = None
        matching_handler = None
        for (match, func) in handlers.get(method, []):
            if logger: logger.debug('(match, func), method : ' + repr((match, func)) + "," + method )
            if isinstance(match, basestring):
                if match == accept:
                    matching_handler = func
            elif (match is None):
                default = func
            else:
                if match(accept):
                    matching_handler = func
        if logger: logger.debug('(matching_handler, default): ' + repr((matching_handler, default)))
        return matching_handler or default


import amara
from amara import tree, bindery
from amara.bindery import html
from amara.lib.util import first_item
from amara.lib import inputsource
#from amara import inputsource as baseinputsource
from amara.lib.irihelpers import resolver as baseresolver
#from amara.namespaces import *
#from amara.xslt import transform
#from amara.writers.struct import *
#from amara.bindery.html import parse as htmlparse
from amara.lib import U
from amara.lib.iri import split_uri_ref, split_fragment, relativize, absolutize, IriError, join, is_absolute
#from amara.bindery.model import examplotron_model, generate_metadata, metadata_dict
from amara.bindery.util import dispatcher, node_handler, property_sequence_getter

from zen.services import zservice, service_proxy

#Following is updated on each request, to avoid possible reentrancy problems:
#H = httplib2.Http('/tmp/.cache')

def cleanup_text_blocks(text):
    return '\n'.join([line.strip() for line in text.splitlines() ])


def linkify(link, wikibase):
    '''
    Try to construct Moin-style link markup from a given link
    '''
    rel = relativize(link, wikibase)
    if rel:
        return u'[[%s]]'%rel
    else:
        return u'[[%s]]'%link


from zen.services import SERVICES

def use(pymodule):
    '''
    e.g. use("pypath.to.yourmodule")
    '''
    #Just importing the module should be enough if they're registering services properly
    try:
        mod = __import__(pymodule)
    except ImportError as e:
        logger.debug('Unable to import declared module, so associated services will have to be available through discovery: ' + repr(e))
    return


#XXX: do we really need this function indirection for simple global dict assignment?
def register_node_type(type_id, nclass):
    node.NODES[type_id] = nclass

#

def curation_ingest(rest_uri, mointext, user, H, auth_headers):
    '''
    '''
    import diff_match_patch
    from akara.util.moin import HISTORY_MODEL

    resp, content = H.request(rest_uri + ';history', "GET", headers=auth_headers)
    historydoc = bindery.parse(content, model=HISTORY_MODEL)
    rev = first_item(dropwhile(lambda rev: unicode(rev.editor) != user, (historydoc.history.rev or [])))
    if not rev or historydoc.history.rev.editor == user:
        #New record, or the most recent modification is also by the akara user
        logger.debug('Direct update (no conflict scenario)')
        return mointext
    else:
        #Potential conflict
        logger.debug('Potential conflict scenario')
        resp, curr_akara_rev = H.request(rest_uri + '?rev=' + rev.id, "GET", headers=auth_headers)
        curr_akara_rev = curation_ingest.wiki_normalize(curr_akara_rev)
        dmp = diff_match_patch.diff_match_patch()
        patches = dmp.patch_make(curr_akara_rev, mointext)
        logger.debug('PATCHES: ' + dmp.patch_toText(patches))
        diff_match_patch.patch_fixup(patches) #Uche's hack-around for an apparent bug in diff_match_patch
        logger.debug('PATCHES: ' + dmp.patch_toText(patches))
        #XXX Possible race condition.  Should probably figure out a way to get all revs atomically
        resp, present_rev = H.request(rest_uri, "GET", headers=auth_headers)
        present_rev = curation_ingest.wiki_normalize(present_rev)
        patched, flags = dmp.patch_apply(patches, present_rev)
        logger.debug('PATCH RESULTS: ' + repr((flags)))
        if all(flags):
            #Patch can be completely automated
            return patched
        else:
            #At least one patch hunk failed
            logger.debug('CONFLICT: ' + repr(flags))
            return None
    return


DIFF_CMD = 'diff -u'
PATCH_CMD = 'patch -p0'

def curation_ingest_via_subprocess(rest_uri, mointext, prior_ingested, user, H, auth_headers):
    '''
    Support function for freemix services.  Inital processing to guess media type of post body.
    '''
    import os
    import tempfile
    from subprocess import Popen, PIPE

    prior_rev, zen_rev, curated_rev = curation_ingest_versions(rest_uri, user, H, auth_headers)
    if not curated_rev:
        #If there has never been a curated rev, we don't have to be on guard for conflicts
        logger.debug('Direct update (no conflict scenario)')
        return True, mointext
    else:
        #Potential conflict
        logger.debug('Potential conflict scenario')
        #We need to diff the latest ingest *candidate* (i.e. mointext) version against the prior ingest *candidate* version

        oldwiki = tempfile.mkstemp(suffix=".txt")
        newwiki = tempfile.mkstemp(suffix=".txt")
        os.write(oldwiki[0], prior_ingested)
        os.write(newwiki[0], mointext)
        #os.fsync(oldwiki[0]) #is this needed with the close below?
        os.close(oldwiki[0])
        os.close(newwiki[0])

        cmdline = ' '.join([DIFF_CMD, oldwiki[1], newwiki[1]])
        logger.debug('cmdline1: \n' + cmdline)
        process = Popen(cmdline, stdout=PIPE, shell=True)
        patch = process.stdout.read()

        logger.debug('PATCHES: \n' + patch)
        #XXX Possible race condition.  Should probably figure out a way to get all revs atomically
        resp, present_rev = H.request(rest_uri, "GET", headers=auth_headers)
        present_rev = curation_ingest.wiki_normalize(present_rev)

        currwiki = tempfile.mkstemp(suffix=".txt")
        os.write(currwiki[0], present_rev)
        #os.fsync(currwiki[0]) #is this needed with the close below?
        os.close(currwiki[0])

        cmdline = ' '.join([PATCH_CMD, currwiki[1]])
        logger.debug('cmdline1: \n' + cmdline)
        process = Popen(cmdline, stdin=PIPE, stdout=PIPE, shell=True)
        process.stdin.write(patch)
        process.stdin.close()
        cmdoutput = process.stdout.read()

        #Apparently process.returncode isn't a useful indicator of patch rejection
        conflict = 'FAILED' in cmdoutput and 'rejects' in cmdoutput

        logger.debug('PATCH COMMAND OUTPUT: ' + repr((cmdoutput)))
        patched = open(currwiki[1]).read()
        patched = curation_ingest.wiki_normalize(patched)
        
        logger.debug('PATCH RESULTS: ' + repr((patched)))
        
        logger.debug('RETURN CODE: ' + repr((process.returncode)))
        process.returncode
        
        if conflict:
            #At least one patch hunk failed
            #logger.debug('CONFLICT: ' + repr(process.returncode))
            return False, patch
        else:
            #Patch can be completely automated
            return True, patched
    return False, none


curation_ingest = curation_ingest_via_subprocess
#By default, normalize for curator ops using standard Akara wiki normalization
curation_ingest.wiki_normalize = wiki_normalize

def curation_ingest_versions(rest_uri, user, H, auth_headers):
    from akara.util.moin import HISTORY_MODEL
    resp, content = H.request(rest_uri + ';history', "GET", headers=auth_headers)
    historydoc = bindery.parse(content, model=HISTORY_MODEL)
    try:
        prior_rev = historydoc.history.rev[1]
    except:
        prior_rev = None
    try:
        zen_rev = first_item(dropwhile(lambda rev: unicode(rev.editor) != user, (historydoc.history.rev or [])))
    except AttributeError: #'entity_base' object has no attribute 'history'
        zen_rev = None
    try:
        curated_rev = first_item(dropwhile(lambda rev: unicode(rev.editor) == user, (historydoc.history.rev or [])))
    except AttributeError: #'entity_base' object has no attribute 'history'
        curated_rev = None
    #if not rev or historydoc.history.rev.editor == user: #New record, or the most recent modification is also by the akara user
    logger.debug('curation_ingest_versions: rest_uri, curr_rev, zen_rev, curated_rev: ' +
        repr((rest_uri, (prior_rev.xml_encode() if prior_rev else None, zen_rev.xml_encode() if zen_rev else None, curated_rev.xml_encode() if curated_rev else None))))
    return prior_rev, zen_rev, curated_rev


from zen.services import register_service

#Services for processing Moin pages
@zservice(u'http://purl.org/com/zepheira/zen/moinmodel/get-link-urls')
def get_link_urls(node):
    links = [ attr.xml_value for attr in node.xml_select(u'.//@href') ]
    return links


@zservice(u'http://purl.org/com/zepheira/zen/moinmodel/get-obj-urls')
def get_obj_urls(node):
    links = [ attr.xml_value for attr in node.xml_select(u'.//@src') ]
    return links

@zservice(u'http://purl.org/com/zepheira/zen/exhibit/jsonize')
def jsonize(obj):
    return json.dumps(obj)

# Remove null(aka None) valued properties from a dictionary
@zservice(u'http://purl.org/com/zepheira/zen/exhibit/strip-null')
def strip_null(obj):
    return dict( (n,v) for (n,v) in obj.iteritems() if v)

def handle_list(node):
    return [ simple_struct(li) for li in node.li ]

def handle_gloss(node):
    return dict((U(l), simple_struct(first_item(l.xml_select(u'following-sibling::item'))))
                       for l in node.label)

def handle_subsection(node):
    return (U(node.title), simple_struct(node))


structure_handlers = {
    u'ul': handle_list,
    u'p': U,
    u'gloss': handle_gloss,
    u's1': handle_subsection,
    u's2': handle_subsection,
    u's3': handle_subsection,
    u's4': handle_subsection,
    u's5': handle_subsection,
}

def handle_lone_para(node):
    #See: http://foundry.zepheira.com/issues/788
    pstringval = node.xml_select(u'string(p[1])')
    if node.xml_select(u'string(.)').strip() == pstringval.strip():
        return U(pstringval)
    return None


@zservice(u'http://purl.org/com/zepheira/zen/util/simple-struct')
def simple_struct(node):
    '''
    >>> from amara.bindery import parse
    >>> from zen.moin import simple_struct
    >>> X = '<s2 id="XYZ" title="XYZ"><p>Hello</p></s2>'
    >>> doc = parse(X)
    >>> simple_struct(doc)
    [(u'XYZ', [(u'A', [u'Hello', (u'AB', [u'World'])])])]

    >>> X = '<s2 id="XYZ" title="XYZ"><p/><s3 id="A" title="A"><p>Hello</p><s4 id="AB" title="AB"><p>World</p></s4></s3></s2>'
    >>> doc = parse(X)
    >>> simple_struct(doc)
    [(u'XYZ', [(u'A', [u'Hello', (u'AB', [u'World'])])])]

    >>> X = '<s2 id="XYZ" title="XYZ"><p/><s3 id="A" title="A"><p>Hello</p><s4 id="AB" title="AB"><gloss><label>spam</label><item>eggs</item></gloss></s4></s3></s2>'
    >>> doc = parse(X)
    >>> simple_struct(doc)
    [(u'XYZ', [(u'A', [u'Hello', (u'AB', [{u'spam': u'eggs'}])])])]

    >>> X = '<s1 id="XYZ" title="XYZ"><s2 id="1" title="1"><ul><li><p>WikiLink </p></li></ul><p/></s2><s2 id="1" title="1"><ul><li>Wikilink </li></ul><p/></s2></s1>'
    >>> doc = parse(X)
    >>> simple_struct(doc)
    [(u'XYZ', [(u'1', [[u'WikiLink ']]), (u'1', [[u'Wikilink ']])])]
    '''
    #To test the above: python -m doctest lib/moinmodel.py
    #FIXME: integrate into test/test_moinmodel_services.py
    
    if not node: return None
    if len(node.xml_children) == 1 and not isinstance(node.xml_first_child, tree.element):
        return node.xml_first_child.xml_value
    simple_pstringval = handle_lone_para(node)
    if simple_pstringval is not None: return simple_pstringval
    top = []
    for child in node.xml_elements:
        handler = structure_handlers.get(child.xml_local, U)
        result = handler(child)
        if not isinstance(result, basestring) or result.strip():
            top.append(result)
    #logger.debug("simple_struct: " + repr(top))
    #if len(top) == 1: top = top[0]
    return top


@zservice(u'http://purl.org/com/zepheira/zen/util/extract-liststrings')
def extract_liststrings(node):
    '''
    Helper to extract all list items from a section
    '''
    items = []
    l = node.xml_select(u'.//ul')
    if l:
        items = [ U(li).strip() for li in list(l[0].li) ]
    return items


@zservice(u'http://purl.org/com/zepheira/zen/util/get-child-pages')
def get_child_pages(node, limit=None):
    '''
    node - the node for the page to be processed
    limit - return no more than this many pages
    
    >>> from zen.moin import node, get_child_pages
    >>> p = node.lookup(u'http://localhost:8880/moin/x/poetpaedia/poet')
    >>> print get_child_pages(p)
    [u'http://localhost:8880/moin/x/poetpaedia/poet/epound', u'http://localhost:8880/moin/x/poetpaedia/poet/splath']
    
    '''
    #isrc, resp = parse_moin_xml(node.rest_uri, resolver=node.resolver)
    #hrefs = node.doc.xml_select(u'//h:table[@class="navigation"]//@href', prefixes={u'h': u'http://www.w3.org/1999/xhtml'})
    #For some reason some use XHTML NS and some don't
    #if not hrefs:
    #    hrefs = node.doc.xml_select(u'//table[@class="navigation"]//@href')

    hrefs = node.doc.xml_select(u'//*[@class="navigation"]//@href')
    if limit:
        hrefs = islice(hrefs, 0, int(limit))
    hrefs = list(hrefs); #logger.debug('get_child_pages HREFS1: ' + repr(hrefs))
    hrefs = [ wiki_uri(node.original_base, node.wrapped_base, navchild.xml_value, node.rest_uri, raw=True)[0] for navchild in hrefs ]
    return hrefs


# -------------------------

def zenuri_to_moinrest(environ, uri=None):
    #self_end_point = environ['SCRIPT_NAME'].rstrip('/') #$ServerPath/zen
    #self_end_point = request_uri(environ, include_query=False).rstrip('/')
    #self_end_point = guess_self_uri(environ)
    #absolutize(environ['SCRIPT_NAME'].rstrip('/'), request_uri(environ, include_query=False))
    #logger.debug('moinrest_uri: ' + repr((self_end_point, MOINREST_SERVICE_ID)))
    #logger.debug('zenuri_to_moinrest: ' + repr((moinresttop, environ['PATH_INFO'], environ['SCRIPT_NAME'])))
    if uri:
        if uri.startswith(MOINREST_BASEURI):
        #if moinresttop.split('/')[-1] == environ['SCRIPT_NAME'].strip('/'):
            #It is already a moin URL
            return uri or request_uri(environ)
        else:
            raise NotImplementedError('For now a Zen uri is required')
    else:
        moinrest_uri = join(MOINREST_BASEURI, environ['PATH_INFO'].lstrip('/'))
    #logger.debug('moinrest_uri: ' + repr(moinrest_uri))
    #logger.debug('moinrest_uri: ' + repr(MOINREST_BASEURI))
    return moinrest_uri


class moinrest_resolver(baseresolver):
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

