# -*- encoding: utf-8 -*-

# Copyright 2008-2009 Zepheira LLC

'''
OAI tools - evolution of oaitools.py in akara demos
'''

import sys, time, logging
import datetime
import urllib, urllib2
#from itertools import *
#from functools import *
from contextlib import closing

import amara
from amara import bindery
from amara.bindery.model import examplotron_model, generate_metadata, metadata_dict
from amara.lib import U
from amara.writers.struct import structwriter, E, NS, ROOT, RAW
#from amara.lib.util import *
from amara.bindery import html
from amara.namespaces import *
from amara.pushtree import pushtree
from amara.thirdparty import httplib2
from amara.tools.atomtools import feed

OAI_NAMESPACE = u"http://www.openarchives.org/OAI/2.0/"

#OAI-PMH verbs:
# * Identify
# * ListMetadataFormats
# * ListSets
# * GetRecord
# * ListIdentifiers
# * ListRecords

#Useful:
# http://www.nostuff.org/words/tag/oai-pmh/
# http://libraries.mit.edu/dspace-mit/about/faq.html
# http://wiki.dspace.org/index.php/OaiInstallations - List of OAI installations harvested by DSpace
#Examples:
# http://eprints.sussex.ac.uk/perl/oai2?verb=GetRecord&metadataPrefix=oai_dc&identifier=oai:eprints.sussex.ac.uk:67
# http://dspace.mit.edu/oai/request?verb=Identify
# http://dspace.mit.edu/oai/request?verb=GetRecord&metadataPrefix=oai_dc&identifier=oai:dspace.mit.edu:1721.1/5451

#Based on: http://dspace.mit.edu/oai/request?verb=GetRecord&metadataPrefix=oai_dc&identifier=oai:dspace.mit.edu:1721.1/5451

#http://dspace.mit.edu/search?scope=%2F&query=stem+cells&rpp=10&sort_by=0&order=DESC&submit=Go

DSPACE_SEARCH_PATTERN = u"http://dspace.mit.edu/search?%s"

DSPACE_ARTICLE = u"http://www.dspace.com/index/details.stp?ID="

RESULTS_DIV = u"aspect_artifactbrowser_SimpleSearch_div_search-results"

DSPACE_OAI_ENDPOINT = u"http://dspace.mit.edu/oai/request"

DSPACE_ARTICLE_BASE = u"http://dspace.mit.edu/handle/"

DSPACE_ID_BASE = u"oai:dspace.mit.edu:"

PREFIXES = {u'o': u'http://www.openarchives.org/OAI/2.0/'}

class oaiservice(object):
    """
    >>> from zen.oai import oaiservice
    >>> remote = oaiservice('http://dspace.mit.edu/oai/request')
    >>> sets = remote.list_sets()
    >>> sets[0]
    >>> first_set = sets[0][0]
    >>> records = remote.list_records(first_set)
    >>> records

    If you want to see the debug messages, just do (before calling read_contentdm for the first time):

    >>> import logging; logging.basicConfig(level=logging.DEBUG)

    """
    def __init__(self, root, logger=logging, cachedir='/tmp/.cache'):
        '''
        root - root of the OAI service endpoint, e.g. http://dspace.mit.edu/oai/request
        '''
        self.root = root
        self.logger = logger
        self.h = httplib2.Http(cachedir)
        return
    
    def list_sets(self):
        #e.g. http://dspace.mit.edu/oai/request?verb=ListSets
        qstr = urllib.urlencode({'verb' : 'ListSets'})
        url = self.root + '?' + qstr
        self.logger.debug('OAI request URL: {0}'.format(url))
        start_t = time.time()
        resp, content = self.h.request(url)
        retrieved_t = time.time()
        self.logger.debug('Retrieved in {0}s'.format(retrieved_t - start_t))
        sets = []

        def receive_nodes(n):
            sets.append((n.xml_select(u'string(o:setSpec)', prefixes=PREFIXES), n.xml_select(u'string(o:setName)', prefixes=PREFIXES)))

        pushtree(content, u"o:OAI-PMH/o:ListSets/o:set", receive_nodes, namespaces=PREFIXES)
        return sets

    def get_record(self, id):
        pass

    def search(self, term):
        qstr = urllib.urlencode({'verb' : 'GetRecord', 'metadataPrefix': 'oai_dc', 'identifier': dspace_id})
        url = DSPACE_OAI_ENDPOINT + '?' + qstr
        logger.debug('DSpace URL: ' + str(url))
        #keywords = [ (k.strip(), JOVE_TAG) for k in unicode(row.xml_select(u'string(.//*[@class="keywords"])')).split(',') ]

        doc = bindery.parse(url, model=OAI_MODEL)
        #print >> sys.stderr, list(generate_metadata(doc))
        resources, first_id = metadata_dict(generate_metadata(doc))
        record = doc.OAI_PMH

        resource = resources[first_id]

    def list_records(self, set):
        '''
        '''
        #e.g. http://dspace.mit.edu/oai/request?verb=ListRecords&metadataPrefix=oai_dc&set=hdl_1721.1_18193
        qstr = urllib.urlencode({'verb' : 'ListRecords', 'metadataPrefix': 'oai_dc', 'set': set})
        url = self.root + '?' + qstr
        self.logger.debug('OAI request URL: {0}'.format(url))
        start_t = time.time()
        resp, content = self.h.request(url)
        retrieved_t = time.time()
        self.logger.debug('Retrieved in {0}s'.format(retrieved_t - start_t))
        doc = bindery.parse(url, model=OAI_LISTRECORDS_MODEL)
        #print >> sys.stderr, list(generate_metadata(doc))
        resources, first_id = metadata_dict(generate_metadata(doc))
        for id_, props in resources.items():
            for k, v in props.items():
                props[k] = [ U(item) for item in v ]
        #record = doc.OAI_PMH

        #resource = resources[first_id]
        return resources

#
OAI_LISTSETS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
  <responseDate>2011-03-14T18:26:05Z</responseDate>
  <request verb="ListSets">http://dspace.mit.edu/oai/request</request>
  <ListSets>
    <set>
      <setSpec>hdl_1721.1_18193</setSpec>
      <setName>1. Reports</setName>
    </set>
    <set>
      <setSpec>hdl_1721.1_18194</setSpec>
      <setName>2. Working Papers</setName>
    </set>
    <set>
      <setSpec>hdl_1721.1_18195</setSpec>
      <setName>3. Theses</setName>
    </set>
  </ListSets>
</OAI-PMH>
"""

OAI_LISTRECORDS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd" xmlns:o="http://www.openarchives.org/OAI/2.0/"
  xmlns:eg="http://examplotron.org/0/" xmlns:ak="http://purl.org/xml3k/akara/xmlmodel">
  <responseDate>2011-03-14T21:29:34Z</responseDate>
  <request verb="ListRecords" set="hdl_1721.1_18193" metadataPrefix="oai_dc">http://dspace.mit.edu/oai/request</request>
  <ListRecords>
    <record ak:resource="o:header/o:identifier">
      <header>
        <identifier>oai:dspace.mit.edu:1721.1/27225</identifier>
        <datestamp ak:rel="local-name()" ak:value=".">2008-03-10T16:34:16Z</datestamp>
        <setSpec>hdl_1721.1_18193</setSpec>
      </header>
      <metadata>
        <oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/" xmlns:dc="http://purl.org/dc/elements/1.1/" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd">
          <dc:title ak:rel="local-name()" ak:value=".">A methodology for the assessment of the proliferation resistance of nuclear power systems: topical report</dc:title>
          <dc:creator ak:rel="local-name()" ak:value=".">Papazoglou, Ioannis Agamennon</dc:creator>
          <dc:subject ak:rel="local-name()" ak:value=".">Nuclear disarmament</dc:subject>
          <dc:description ak:rel="local-name()" ak:value=".">A methodology for the assessment of the differential resistance of various nuclear power systems to ...</dc:description>
          <dc:date>2005-09-15T14:12:55Z</dc:date>
          <dc:date ak:rel="local-name()" ak:value=".">2005-09-15T14:12:55Z</dc:date>
          <dc:date>1978</dc:date>
          <dc:type ak:rel="local-name()" ak:value=".">Technical Report</dc:type>
          <dc:format ak:rel="local-name()" ak:value=".">6835289 bytes</dc:format>
          <dc:format>7067243 bytes</dc:format>
          <dc:format>application/pdf</dc:format>
          <dc:format>application/pdf</dc:format>
          <dc:identifier ak:rel="'handle'" ak:value=".">04980676</dc:identifier>
          <dc:identifier>http://hdl.handle.net/1721.1/27225</dc:identifier>
          <dc:language ak:rel="local-name()" ak:value=".">en_US</dc:language>
          <dc:relation ak:rel="local-name()" ak:value=".">MIT-EL</dc:relation>
          <dc:relation>78-021</dc:relation>
          <dc:relation>MIT-EL</dc:relation>
          <dc:relation>78-022</dc:relation>
        </oai_dc:dc>
      </metadata>
    </record>
    <resumptionToken expirationDate="2011-03-14T22:29:39Z">0001-01-01T00:00:00Z/9999-12-31T23:59:59Z/hdl_1721.1_18193/oai_dc/100</resumptionToken>
  </ListRecords>
</OAI-PMH>
"""


OAI_GETRECORD_XML = """<?xml version="1.0" encoding="UTF-8"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:o="http://www.openarchives.org/OAI/2.0/"
         xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"
         xmlns:eg="http://examplotron.org/0/" xmlns:ak="http://purl.org/xml3k/akara/xmlmodel">
  <responseDate>2009-03-30T06:09:23Z</responseDate>
  <request verb="GetRecord" identifier="oai:dspace.mit.edu:1721.1/5451" metadataPrefix="oai_dc">http://dspace.mit.edu/oai/request</request>
  <GetRecord>
    <record ak:resource="o:header/o:identifier">
      <header>
        <identifier>oai:dspace.mit.edu:1721.1/5451</identifier>
        <datestamp ak:rel="local-name()" ak:value=".">2006-09-20T00:15:44Z</datestamp>
        <setSpec>hdl_1721.1_5443</setSpec>
      </header>
      <metadata>
        <oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/" xmlns:dc="http://purl.org/dc/elements/1.1/" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd">
          <dc:creator ak:rel="local-name()" ak:value=".">Cohen, Joshua</dc:creator>
          <dc:date ak:rel="local-name()" ak:value=".">2004-08-20T19:48:34Z</dc:date>
          <dc:date>2004-08-20T19:48:34Z</dc:date>
          <dc:date>1991</dc:date>
          <dc:identifier ak:rel="'handle'" ak:value=".">http://hdl.handle.net/1721.1/5451</dc:identifier>
          <dc:description ak:rel="local-name()" ak:value=".">Cohen's Comments on Adam Przeworski's article "Could We Feed Everyone?"</dc:description>
          <dc:format>2146519 bytes</dc:format>
          <dc:format>application/pdf</dc:format>
          <dc:language>en_US</dc:language>
          <dc:publisher ak:rel="local-name()" ak:value=".">Politics and Society</dc:publisher>
          <dc:title ak:rel="local-name()" ak:value=".">"Maximizing Social Welfare or Institutionalizing Democratic Ideals?"</dc:title>
          <dc:type>Article</dc:type>
          <dc:identifier>Joshua Cohen, "Maximizing Social Welfare or Institutionalizing Democratic Ideals?"; Politics and Society, Vol. 19, No. 1</dc:identifier>
        </oai_dc:dc>
      </metadata>
    </record>
  </GetRecord>
</OAI-PMH>
"""

OAI_GETRECORD_MODEL = examplotron_model(OAI_GETRECORD_XML)
OAI_LISTRECORDS_MODEL = examplotron_model(OAI_LISTRECORDS_XML)


#@simple_service('GET', 'http://open-science.zepheira.com/content/dspace/source', 'osci.dspace.atom', 'application/atom+xml')
def dspace_adapter(search=None, id=None):
    '''
    Sample queries:
    curl "http://localhost:8880/dspace?search=stem+cells"
    curl "http://localhost:8880/dspace?id=19358275"
    '''
    #FIXME: How do we handle no search or id param?  Just serve up the latest entries?  Or error as below?
    #assert_(not(search and id), msg="You must specify the 'search' or 'id' query parameter is mandatory.")
    if search:
        #reldate: only search for last N days
        #query = urllib.urlencode({'db' : NCBI_DB, 'term': query, 'reldate': '60', 'datetype': 'edat', 'retmax': DEFAULT_MAX_RESULTS, 'usehistory': 'y'})
        query = urllib.urlencode({'query': search, 'scope': '/', 'rpp': DEFAULT_MAX_RESULTS, 'sort_by': '0', 'order': 'DESC', 'submit': 'Go'})
        search_url = DSPACE_SEARCH_PATTERN%(query)
        #print >> sys.stderr, search_url
        search_terms = search
        alt_link = search_url
        self_link = DSPACE_ADAPTER_BASE + '?' + urllib.urlencode({'search': search})
        doc = html.parse(search_url)

        f = feed(ATOM_ENVELOPE, title=search_terms.decode('utf-8'), id=self_link.decode('utf-8'))
        #f.feed.update = self_link.decode('utf-8')
        f.feed.xml_append(E((ATOM_NAMESPACE, u'link'), {u'rel': u'self', u'type': u'application/atom+xml', u'href': self_link.decode('utf-8')}))
        f.feed.xml_append(E((ATOM_NAMESPACE, u'link'), {u'rel': u'search', u'type': u'application/opensearchdescription+xml', u'href': OSCI_BASE + u'/content/dspace.discovery'}))
        f.feed.xml_append(E((ATOM_NAMESPACE, u'link'), {u'rel': u'alternate', u'type': u'text/xml', u'href': alt_link.decode('utf-8')}))
        f.feed.xml_append(E((OPENSEARCH_NAMESPACE, u'Query'), {u'role': u'request', u'searchTerms': search_terms.decode('utf-8')}))
        maxarticles = DEFAULT_MAX_RESULTS

        #for item in doc.xml_select(u'//*[@class="result_table"]//*[@class="article_title"]'):
        for li in islice(doc.xml_select(u'//*[@id="'+RESULTS_DIV+'"]//*[@class="artifact-description"]/..'), 0, maxarticles):
            row = li.xml_parent.xml_parent
            title = li.xml_select(u'.//*[@class="artifact-title"]')[0]
            rel_id = title.a.href.partition(u'/handle/')[2]
            dspace_id = DSPACE_ID_BASE + rel_id
            alt_link = DSPACE_ARTICLE_BASE + u'1721.1/7488'
            #Do not quote.  DSpace doesn't like that
            #alt_link = DSPACE_ARTICLE_BASE + urllib.quote(u'1721.1/7488', '')
            title = unicode(title)
            summary = unicode(row.xml_select(u'string(.//*[@class="summary"])'))
            updated = unicode(row.xml_select(u'string(.//*[@class="date"])')).strip().partition(u'Published: ')[2]
            #updated = time.strptime(updated, "%m/%d/%Y %H:%M:%S") #2/11/2008 2:20:00 AM
            authors = [ (name.strip(), None, None) for name in unicode(row.xml_select(u'string(.//*[@class="author"]//b)')).split(';') ]

            #Retrieve the DSpace page
            qstr = urllib.urlencode({'verb' : 'GetRecord', 'metadataPrefix': 'oai_dc', 'identifier': dspace_id})
            url = DSPACE_OAI_ENDPOINT + '?' + qstr
            logger.debug('DSpace URL: ' + str(url))
            #keywords = [ (k.strip(), JOVE_TAG) for k in unicode(row.xml_select(u'string(.//*[@class="keywords"])')).split(',') ]

            doc = bindery.parse(url, model=OAI_MODEL)
            #print >> sys.stderr, list(generate_metadata(doc))
            resources, first_id = metadata_dict(generate_metadata(doc))
            record = doc.OAI_PMH

            resource = resources[first_id]

            authors = [ (a, None, None) for a in resource.get(u'creator', '') ]
            links = [
                (DSPACE_ARTICLE_BASE + rel_id, u'alternate'),
                (u'dspace?id=' + dspace_id, u'self'),
            ]
            elements = [
                E((ATOM_NAMESPACE, u'content'), {u'src': alt_link}),
            ]
            f.append(
                dspace_id,
                U(resource['title']),
                updated=U(resource['date']),
                summary=U(resource.get('description', '')),
                authors=authors,
                links=links,
                #categories=categories,
                elements=elements,
            )

        #FIXME: indent
        return f.xml_encode()

