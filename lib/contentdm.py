import sys
import urllib#, urlparse
from cgi import parse_qs
from itertools import islice, chain, imap

from amara.bindery.html import parse as htmlparse

from amara.lib.iri import absolutize, split_uri_ref
from amara.lib.util import first_item
from amara.lib import U
from amara.tools import atomtools
from amara.bindery.model import examplotron_model, generate_metadata, metadata_dict
from amara.bindery.util import dispatcher, node_handler

"""
( http://www.contentdm.com/ )

python contentdm_adapter.py http://digital.library.louisville.edu/cdm4/ "crutches"

 * http://digital.library.louisville.edu/collections/jthom/
 * http://digital.library.louisville.edu/cdm4/search.php
"""

#QUERY = sys.argv[2]
#URL = 'item_viewer.php?CISOROOT=/jthom&CISOPTR=920&CISOBOX=1&REC=1'


class content_handlers(dispatcher):
    @node_handler([u'br'])
    def br(self, node):
        yield u', '

    @node_handler(u'span')
    def code(self, node):
        for chunk in chain(*imap(self.dispatch, node.xml_children)):
            yield chunk

    #@node_handler([u'text()'])
    #def text(self, node):
    #    yield node.xml_value

    @node_handler([u'*'], priority=-1)
    def default(self, node):
        yield unicode(node)


CONTENT = content_handlers()

def read_contentdm(site, collection=None, query=None, limit=None):
    '''
    A generator of CDM records
    First generates header info

    >>> from zen.contentdm import read_contentdm
    >>> results = read_contentdm('http://digital.library.louisville.edu/cdm4/', collection='/jthom', query=None, limit=None)
    >>> results.next()
    {'basequeryurl': 'http://digital.library.louisville.edu/cdm4/results.php?CISOOP1=any&CISOROOT=%2Fjthom&CISOBOX1=&CISOFIELD1=CISOSEARCHALL'}
    >>> results.next()
    {u'Title': u'60 years in darkness.  ', u'Object_Type': u'Negatives, ', u'Source': u"4 x 5 in. b&w safety negative. Item no. 1979.33.1026 in the Jean Thomas, The Traipsin' Woman, Collection, University of Louisville Photographic Archives. ", u'Collection': u"Jean Thomas, The Traipsin' Woman, Collection, ",...}

    The first yielded value is global metadata; the  second is the record
    for the first item  in the collection/query, and so on until all the items
    are returned, or the limit reached.

    for a nice-sized collection to try:
    >>> read_contentdm('http://digital.library.louisville.edu/cdm4/', collection='/maps', query=None, limit=None)

    i.e.: http://digital.library.louisville.edu/cdm4/browse.php?CISOROOT=/maps

    See also:

    * http://content.lib.auburn.edu/cdm4/browse.php?CISOROOT=/football (51 items)
    '''
    #For testing there are some very large collections at http://doyle.lib.muohio.edu/about-collections.php
    urlparams = {}
    #if urlparams:
    #   ingest_service += '?' + urllib.urlencode(urlparams)

    qstr = urllib.urlencode({'CISOBOX1' : query or '', 'CISOROOT' : collection})
    url = '%sresults.php?CISOOP1=any&%s&CISOFIELD1=CISOSEARCHALL'%(site, qstr)

    yield {'basequeryurl': url}

    resultsdoc = htmlparse(url)

    seen = set()
    
    #items = resultsdoc.xml_select(u'//form[@name="searchResultsForm"]//a[starts-with(@href, "item_viewer.php")]')

    def follow_pagination(doc):
        #e.g. of page 1: http://digital.library.louisville.edu/cdm4/browse.php?CISOROOT=/afamoh
        #e.g. of page 2: http://digital.library.louisville.edu/cdm4/browse.php?CISOROOT=/afamoh&CISOSTART=1,21
        page_start = 1
        while True:
            items = doc.xml_select(u'//a[starts-with(@href, "item_viewer.php")]')
            #items = list(items)
            #print >> sys.stderr, "doc: ", items
            #for i in items: yield i
            for i in items:
                print >> sys.stderr, "i: ", unicode(i)
                yield i
            next = [ l.href for l in doc.xml_select(u'//a[@class="res_submenu"]') if int(l.href.split(u',')[-1]) > page_start ]
            if not next:
                break
            page_start = int(l.href.split(u',')[-1])
            url = absolutize(next[0], site)
            print >> sys.stderr, "Next page URL: ", url
            doc = htmlparse(url)
        return

    items = follow_pagination(resultsdoc)

    at_least_one = False
    count = 0
    for it in items:
        at_least_one = True
        entry = {}
        pageuri = absolutize(it.href, site)
        print >> sys.stderr, "Processing item URL: ", pageuri
        (scheme, netloc, path, query, fragment) = split_uri_ref(pageuri)
        entry['domain'] = netloc
        params = parse_qs(query)
        entry['cdm-coll'] = params['CISOROOT'][0].strip('/').split('/')[0]
        entry['id'] = params['CISOPTR'][0]
        if entry['id'] in seen:
            continue
        seen.add(entry['id'])
        entry['link'] = unicode(pageuri)
        entry['local_link'] = '#' + entry['id']
        page = htmlparse(pageuri)
        image = first_item(page.xml_select(u'//td[@class="tdimage"]//img'))
        if image:
            imageuri = absolutize(image.src, site)
            entry['imageuri'] = imageuri
            try:
                entry['thumbnail'] = absolutize(dict(it.xml_parent.a.img.xml_attributes.items())[None, u'src'], site)
            except AttributeError:
                print >> sys.stderr, "No thumbnail"
        #entry['thumbnail'] = DEFAULT_RESOLVER.normalize(it.xml_parent.a.img.src, root)
        fields = page.xml_select(u'//tr[td[@class="tdtext"]]')
        for f in fields:
            key = unicode(f.td[0].span.b).replace(' ', '_')
            value = u''.join(CONTENT.dispatch(f.td[1].span))
            entry[key] = unicode(value)
        if u'Title' in entry:
            print >> sys.stderr, "(%s)"%entry['Title']
            entry['label'] = entry['Title']
        if u"Location_Depicted" in entry:
            locations = entry[u"Location_Depicted"].split(u', ')
            #locations = [ l.replace(' (', ', ').replace(')', '').replace(' ', '+') for l in locations if l.strip() ]
            locations = [ l.replace(' (', ', ').replace(')', '').replace('.', '') for l in locations if l.strip() ]
            #print >> sys.stderr, "LOCATIONS", repr(locations)
            entry[u"Locations_Depicted"] = locations
        if u"Date_Original" in entry:
            entry[u"Estimated_Original_Date"] = entry[u"Date_Original"].strip().replace('-', '5').replace('?', '') 
        entry[u"Subject"] = [ s for s in entry.get(u"Subject", u'').split(', ') if s.strip() ]
        yield entry
        count += 1
        if limit and count > limit:
            print >> sys.stderr, "Limit reached"
            break
    return


