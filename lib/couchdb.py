# -*- coding: iso-8859-1 -*-
# 
"""

"""

#Create a Python couchdb attachment:
#curl -H "Content-Type: application/python" -X PUT --data-binary "@-" http://server:5984/test1/$docid/attachment?rev=$rev < spam.rsheet
#Note: attachments must always be on a doc, and rev is mandatory.
#See: http://wiki.apache.org/couchdb/HTTP%5FDocument%5FAPI#Standalone_Attachments

#Retrieve it:
#curl http://server:5984/test1/$docid/attachment

import cStringIO
import hashlib
import datetime
from gettext import gettext as _

from functools import partial
from itertools import islice, dropwhile

from amara.thirdparty import json, httplib2

from amara.lib.iri import split_uri_ref, split_fragment, relativize, absolutize, IriError, join, is_absolute

from akara.util import status_response, requested_imt, header_credentials, extract_auth
#from akara.util.moin import wiki_uri, wiki_normalize, WSGI_ORIG_BASE_HEADER, XML_IMT
from akara.util.moin import wiki_uri, wiki_normalize, ORIG_BASE_HEADER, XML_IMT
from akara.services import convert_body, service_method_dispatcher

try:
    from akara import logger
except ImportError:
    logger = None

from zen import ZEN_SERVICE_ID
from zen.services import SERVICES, zservice, service_proxy
from zen.util import use

MOINREST_SERVICE_ID = 'http://purl.org/xml3k/akara/services/demo/moinrest'
#WSGI_ORIG_BASE_HEADER = 'HTTP_X_AKARA_WRAPPED_MOIN'
FIND_PEER_SERVICE_KEY = 'akara.FIND_PEER_SERVICE'

RESOURCE_TYPE_TYPE = u'http://purl.org/xml3k/akara/cms/resource-type'


class space(object):
    def __init__(self, params, space_tag, logger, zensecret, initial_environ=None):
        '''
        initial_environ is the environment used from the first call to Zen for this space, which causes
        this space to be set up
        '''
        #Use akara discovery, via find_peer_service, to get the full base URI for this very
        #zen endpoint, and its moinrest peer
        #self.space_tag = kwargs['space_tag']
        if initial_environ:
            find_peer_service = initial_environ[FIND_PEER_SERVICE_KEY]
            self.ZEN_BASEURI = find_peer_service(initial_environ, ZEN_SERVICE_ID)
        #Start out with the first environment used for a call that activated this space
        #self.environ will be updated upon every invocation of this space
        self.environ = initial_environ
        #Set up class/instance params based on live Akara environment
        self.params = params
        self.remotedb = params['dburi']
        self.space_tag = space_tag
        self.logger = logger
        self.zensecret = zensecret
        return

    def setup_request(self, environ):
        '''
        Prepare to service a forwarded call from Zen central
        environ - the WSGI environ of the original invocation
        '''
        #Prepare the WSGI start_response function, which covers response headers and status
        self.resp_status = None
        self.resp_headers = None
        self.exc_info = None
        self.environ = environ
        #FIXME: Use akara to get the right cache location
        self.h = httplib2.Http('/tmp/.cache')
        self.h.force_exception_to_status_code = True

        #Set up utility environ variable for rulesheets
        self.environ['zen.RESOURCE_URI'] = join(self.ZEN_BASEURI, environ['PATH_INFO'].lstrip('/').split('/')[0])
        return

    def resource_factory(self, path=None):
        '''
        Look up and retrieve a new resource based on WSGI environment or a uri path
        '''
        if path:
            docid = path
            if is_absolute(path):
                docid = relativize(path, self.remotedb)
        else:
            docid = self.environ['PATH_INFO'].lstrip('/').rsplit(self.space_tag, 1)[1].lstrip('/') #e.g. '/mydb/MyDoc' -> 'MyDoc'
        #resp, content = self.h.request(slave_uri + ';history', "GET", headers=auth_headers)
        if logger: logger.debug('query ' + repr((self.remotedb, docid, join(self.remotedb, docid))))
        resp, content = self.h.request(join(self.remotedb, docid))
        
        if logger: logger.debug('resp ' + repr((content[:100], resp)))

        self.resp_status = resp['status']
        #XXX: do we need to bother with a copy?
        self.resp_headers = resp.copy()
        del self.resp_headers['status']

        if not (self.resp_status.startswith('20') or self.resp_status == '304'):
            if logger: logger.debug("Error looking up resource: %s: %s\n" % (content, self.resp_status))
            return None #No resource could be retrieved

        data = json.loads(content)
        return resource.factory(self, docid, data)

    def update_resource(self, path=None):
        '''
        Update a resource based on WSGI environment or a uri path
        '''
        if path:
            docid = path
            if is_absolute(path):
                docid = relativize(path, self.remotedb)
        else:
            docid = self.environ['PATH_INFO'].lstrip('/').rsplit(self.space_tag, 1)[1].lstrip('/') #e.g. '/mydb/MyDoc' -> 'MyDoc'

        if logger: logger.debug('query ' + repr((self.remotedb, docid, join(self.remotedb, docid))))
        body = self.environ['wsgi.input'].read()
        resp, content = self.h.request(join(self.remotedb, docid), "PUT", body=body)#, headers=headers)
        
        if logger: logger.debug('resp ' + repr((content[:100], resp)))

        self.resp_status = resp['status']
        #XXX: do we need to bother with a copy?
        self.resp_headers = resp.copy()
        del self.resp_headers['status']

        if not (self.resp_status.startswith('20') or self.resp_status == '304'):
            if logger: logger.debug("Error looking up resource: %s: %s\n" % (content, self.resp_status))
            return None #No resource could be retrieved

        return content
        
    #For couchdb create & update happen to be the same back end mechanism (since rulesheets are expected to provide the URL location)
    create_resource = update_resource

    def delete_resource(self, path=None):
        '''
        Delete a resource based on WSGI environment or a uri path
        '''
        if path:
            docid = path
            if is_absolute(path):
                docid = relativize(path, self.remotedb)
        else:
            docid = self.environ['PATH_INFO'].lstrip('/').rsplit(self.space_tag, 1)[1].lstrip('/') #e.g. '/mydb/MyDoc' -> 'MyDoc'

        if logger: logger.debug('query ' + repr((self.remotedb, docid, join(self.remotedb, docid))))
        resp, content = self.h.request(join(self.remotedb, docid), "DELETE", body=body)#, headers=headers)
        
        if logger: logger.debug('resp ' + repr((content[:100], resp)))

        self.resp_status = resp['status']
        #XXX: do we need to bother with a copy?
        self.resp_headers = resp.copy()
        del self.resp_headers['status']

        if not (self.resp_status.startswith('20') or self.resp_status == '304'):
            if logger: logger.debug("Error looking up resource: %s: %s\n" % (content, self.resp_status))
            return None #No resource could be retrieved

        return content


#FIXME: Detect resource reference loops

class resource(object):
    '''
    Akara Moin/CMS node, a Moin wiki page that follows a template to direct workflow
    activity, including metadata extraction
    '''
    AKARA_TYPE = u'http://purl.org/xml3k/akara/cms/resource-type'

    @staticmethod
    def factory(space, docid, data, rtype=None):
        '''
        
        Note: it's a fatal error if this can't figure out the resource type
        '''
        #Primarily to decide whether to create a resource or a resource_type object
        if not rtype:
            typeid, tpath = resource.zen_type(space, data)
        if typeid == RESOURCE_TYPE_TYPE:
            return resource_type(space, docid, data, rtype=typeid)
        return resource(space, docid, data, rtype=typeid)

    def __init__(self, space, docid, data, rtype=None):
        '''
        '''
        self.docid = docid
        self.space = space
        self.slave_uri = join(space.remotedb, docid)
        self.data = data
        self.rulesheet = None

        if logger: logger.debug('GRIPPO: ' + repr(rtype))
        if isinstance(rtype, basestring) and rtype != RESOURCE_TYPE_TYPE:
            self.type = space.resource_factory(rtype)
        else:
            self.type = rtype
        return

    @staticmethod
    def zen_type(space, data):
        '''
        Computer a Zen type full moinrest uri as well as a path relative to top of the wiki instance
        '''
        rtype = data['zen:metadata']['zen:type']
        if logger: logger.debug('zen_type link: ' + repr(rtype))
        tpath, tid = rtype, absolutize(rtype, space.remotedb)
        if logger: logger.debug('Retrieved zen_type: ' + repr((tid, tpath)))
        return (tid, tpath)

    def get_proxy(self, environ, method, accept=None):
        return self.resource_type.run_rulesheet(environ, method, accept)


UNSPECIFIED = object()

class resource_type(resource):
    def get_rulesheet(self):
        rsheet = self.data['zen:metadata']['zen:rulesheet']
        if rsheet == '.':
            #The rulesheet is in a standalone attachment to thios doc
            rev = self.data['_rev']
            self.rulesheet = join(self.slave_uri, u'attachment?rev=' + rev)
        else:
            #self.rulesheet = UNSPECIFIED
            self.rulesheet = rsheet
        if self.space: self.space.logger.debug('resource_type.get_rulesheet slave_uri, rulesheet: ' + repr((self.slave_uri, self.rulesheet)))
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
        h = httplib2.Http('/tmp/.cache')
        if auth:
            user, passwd = auth
            h.add_credentials(user, passwd)
        resp, body = h.request(source)
        if logger: logger.debug('rsheet_body ' + repr((body[:200],)))
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
        rheet_sig = hashlib.sha1(self.space.zensecret + self.body).hexdigest()
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


