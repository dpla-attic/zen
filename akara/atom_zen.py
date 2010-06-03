"""
 Module name:: atom_zen

Atom Akara adapter for Moin Zen integration

See:

 * http://purl.org/xml3k/akara
 * http://foundry.zepheira.com/projects/zen
 
@ 2009 by Semio Clinical and Zepheira

= Defined REST entry points =

http://purl.org/com/zepheira/services/atom.moin (atom.moin) Handles POST

= Configuration =

moinrestbase (required) - the base Moin/REST URI for the place where pages should
                          be added/updated
default-max-count (optional) - limit on the number of Atom entries to be added/updated on the wiki
breather -                number of seconds to wait between each query to update the wiki, to avoid
                          [[http://moinmo.in/HelpOnConfiguration/SurgeProtection|surge protection]]
                          10s by default

A closer look at moinrestbase.  In the example value: http://localhost:8880/moin/mywiki/

 * http://localhost:8880/... - the URL to the root of an Akara instance
 * ...moin... - the moint point of the Moin/REST wrapper module under Akara (moinrest.py)
 * ...mywiki... - the wiki ID for a specific, wrapped Moin wiki, as defined e.g.
   in a target-xxx config var for moinrest.py e.g. "mywiki" above would correspond to
   "target-mywiki" config var for moinrest

Sample config:

[ctgov_moin]
moinrestbase = http://localhost:8880/moin/mywiki/feeds/

= Notes on security =

To-do
"""

import sys
import time
import urllib, httplib2, urllib2
from itertools import islice

from amara import bindery
from amara.lib.iri import absolutize
from amara.tools import atomtools
from amara.lib.util import first_item
from amara.writers.struct import structencoder, E, NS, ROOT, RAW, E_CURSOR

from akara.services import simple_service
from akara import logger

#AKARA is automatically defined at global scope for a module running within Akara
MOINBASE = AKARA.module_config['moinrestbase']
#Make sure the URl ends with a / for graceful URL resolution
MOINBASE = MOINBASE.rstrip('/')+'/'
USER = AKARA.module_config.get('moin-user', None)
PASSWD = AKARA.module_config.get('moin-passwd', None)

DEFAULT_MAX = AKARA.module_config.get('default-max-count', 20)
BREATHER = int(AKARA.module_config.get('breather', 2))

import re
SLUGCHARS = r'a-zA-Z0-9\-\_'
OMIT_FROM_SLUG_PAT = re.compile('[^%s]'%SLUGCHARS)
atomtools.slug_from_title = slug_from_title = lambda t: OMIT_FROM_SLUG_PAT.sub('_', t).lower().decode('utf-8')

SERVICE_ID = 'http://purl.org/com/zepheira/services/atom.moin'

@simple_service('POST', SERVICE_ID, 'atom.moin', 'text/plain')
def atom_moin(body, ctype, maxcount=None, folder=None, feed=None):
    #Sample query:
    #curl --request POST "http://localhost:8880/atom.moin?feed=http://bitworking.org/news/feed/&maxcount=10&folder=foo091023"
    #You can set ...&maxcount=100 or whatever number, if you like
    maxcount = int(maxcount if maxcount else DEFAULT_MAX)

    H = httplib2.Http('.cache')
    if USER:
        H.add_credentials(USER, PASSWD)

    #Prepare the envelope for the output (POST response)
    w = structencoder()
    output = w.cofeed(ROOT(E_CURSOR(u'updates', {u'feed': feed})))
    logger.debug('Feed: ' + feed)
    
    entries = atomtools.ejsonize(feed)
    for entry in islice(entries, 0, maxcount):
        try:
            logger.debug('ENTRY: ' + repr(entry))
            aid = entry[u'label']
            slug = atomtools.slug_from_title(aid)
            #logger.debug('GRIPPO' + repr((id,)))
            dest = folder + '/' + slug
            chunks = [ ' title:: ' + entry[u'title'] ]
            chunks.append(' last changed:: ' + entry[u'updated'])
            chunks.append(' link:: ' + (first_item(entry[u'link']) or ''))

            if u'summary' in entry: chunks.append('= Summary =\n' + entry[u'summary'])
            if u'content_src' in entry: chunks.append('= Content =\n' + entry[u'content_src'])
            if u'content_text' in entry: chunks.append('= Content =\n' + entry[u'content_text'])
            #logger.debug("Result IDs: " + ids)
            if u'categories' in entry:
                chunks.append(u'= Categories =')
                for categories in entry[u'categories']:
                    chunks.append(' * ' + categories)

            chunks.append(' id:: ' + entry[u'id'])
            chunks.append('= akara:metadata =\n akara:type:: http://purl.org/com/zepheira/zen/resource/webfeed\n')

            url = absolutize(dest, MOINBASE)
            headers = {'Content-Type' : 'text/plain'}
            resp, content = H.request(url, "PUT", body='\n'.join(chunks).encode('utf-8'), headers=headers)
            logger.debug("Result: " + repr((resp, content)))
            output.send(E(u'update', {u'entry-id': entry[u'id'], u'page': url}))
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception, e:
            logger.info('Exception handling Entry page: ' + repr(e))
            output.send(E(u'failure', {u'entry-id': entry[u'id']}))
    time.sleep(BREATHER)
        
    output.close()
    return w.read()

