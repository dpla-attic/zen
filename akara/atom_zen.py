import sys
import urllib, httplib2, urllib2
from itertools import *

import simplejson

from amara import bindery
from amara.lib.iri import absolutize
from amara.tools import atomtools

from akara.services import simple_service
from akara import logger

import logging; logger.setLevel(logging.DEBUG)

#AKARA is automatically defined at global scope for a module running within Akara
MOINBASE = AKARA.module_config['moinrestbase']
#Make sure the URl ends with a / for graceful URL resolution
MOINBASE = MOINBASE.rstrip('/')+'/'
USER = AKARA.module_config.get('moin-user', None)
PASSWD = AKARA.module_config.get('moin-passwd', None)

SERVICE_ID = 'http://purl.org/com/zepheira/services/atom.zen'

import re
SLUGCHARS = r'a-zA-Z0-9\-\_'
OMIT_FROM_SLUG_PAT = re.compile('[^%s]'%SLUGCHARS)
atomtools.slug_from_title = slug_from_title = lambda t: OMIT_FROM_SLUG_PAT.sub('_', t).lower().decode('utf-8')

@simple_service('POST', SERVICE_ID, 'atom.zen', 'text/plain')
def atom_zen(body, ctype, maxcount=None, folder=None):
    #Sample query: "http://localhost:8880/atom.zen?search=diabetes&maxcount=10&folder=foo091023"
    #You can set ...&maxcount=100 or whatever number, if you like
    maxcount = int(maxcount) if maxcount else 10

    H = httplib2.Http('.cache')
    if USER:
        H.add_credentials(USER, PASSWD)

    #e.g. http://clinicaltrials.gov/search?term=diabetes&displayxml=true
    import simplejson
    entries = atomtools.ejsonize(body)
    for entry in islice(entries, 0, maxcount):
        aid = entry[u'label']
        slug = atomtools.slug_from_title(aid)
        #logger.debug('GRIPPO' + repr((id,)))
        dest = folder + '/' + slug
        chunks = [ ' title:: ' + entry[u'title'] ]
        chunks.append(' last changed:: ' + entry[u'updated'])
        chunks.append(' link:: ' + entry[u'link'])

        if u'summary' in entry: chunks.append('= Summary =\n' + entry[u'summary'])
        if u'content' in entry: chunks.append('= Content =\n' + entry[u'content'])
        #logger.debug("Result IDs: " + ids)
        if u'categories' in entry:
            chunks.append(u'= Categories =')
            for categories in entry[u'categories']:
                chunks.append(' * ' + categories)

        url = absolutize(dest, MOINBASE)
        headers = {'Content-Type' : 'text/plain'}
        resp, content = H.request(url, "PUT", body='\n'.join(chunks).encode('utf-8'), headers=headers)
        logger.debug("Result: " + repr((resp, content)))
        
    return 'Wiki updated OK'

