import httplib2
import sys
import hashlib

from testconfig import config

"""
Nosetests for Zen's HTTP-related features such as media type handling and cache control.

This could use some simplification; there's lots of repeated code.  I suppose a pipeline would help?

"""

POET_RESOURCE_TYPE_URI = 'http://localhost:8880/%s/testwiki/poetpaedia/poet'
POET_RESOURCE_TYPE_CREOLE = '''
= resource:name =

Poet

= resource:description =

A poet is a person who writes poems

= Children =

Generated listing of poets who lie under this page in hierarchy:

Children: <<Navigation(children)>>

= akara:metadata =

 akara:type:: http://purl.org/xml3k/akara/cms/resource-type
 akara:rulesheet:: http://www.markbaker.ca/poet.txt
'''
#akara:rulesheet:: [[poetpaedia/rulesheet]]

POET_RULESHEET_URI = 'http://localhost:8880/%s/testwiki/poetpaedia/rulesheet'

POET_RULESHEET = '''
from amara.thirdparty import json

#Declare transform services
strip = service(u'http://purl.org/xml3k/akara/builtins/string/strip')
parsedate = service(u'http://purl.org/com/zepheira/zen/temporal/parse-date')
obj_urls = service(u'http://purl.org/com/zepheira/zen/moinmodel/get-obj-urls')
link_urls = service(u'http://purl.org/com/zepheira/zen/moinmodel/get-link-urls')

#Used to serve requests for a raw Python dictionary
@handles('GET', 'raw/pydict')
def objectify(resource):
    #Data extraction
    bio = resource.definition_section(u'poet:bio')

    #Output
    obj = {
      u'id': resource.rest_uri,
      u'name': strip(U(bio[u'poet:name'])),
      u'born': U(parsedate(U(bio[u'poet:born']))),
      u'died': U(parsedate(U(bio[u'poet:died']))),
      u'images': obj_urls(bio[u'poet:image']),
      u'wikipedia': link_urls(bio[u'poet:wikipedia']),
      u'description': U(resource.section(u'About')),
    }
    return obj

#Used to serve normal HTTP GET requests for the default representation of this resource
@handles('GET',ttl=3600)
def get_poet(resource):
    return json.dumps(objectify(resource))

#A simple text/plain representation
@handles('GET','text/plain',86400)
def get_poet(resource):
    poet = objectify(resource)
    return poet.name + ': ' + poet.description

@handles('GET','text/html',43200)
def get_poet(resource):
    poet = objectify(resource)
    return "<html><head><title>%s</title></head><body><p>%s</p></body></html" % (poet.name, poet.description)

#Used to serve requests for a collection of resources, in raw form
@handles('collect','raw/pydict')
def collect_poets(resources):
    return json.dumps([objectify(resource) for resource in resources])
'''

POET_URI = 'http://localhost:8880/%s/testwiki/poetpaedia/poet/pound'
POET_CREOLE = '''
One of my favorite poets is Ezra Pound

= About =

He was an American expatriate poet, critic and intellectual who was a major figure of the [[http://en.wikipedia.org/wiki/Modernist_poetry|Modernist]] movement in the first half of the 20th century. He is generally considered the poet most responsible for defining and promoting a modernist aesthetic in poetry. The critic Hugh Kenner said of Pound upon meeting him: "I suddenly knew that I was in the presence of the center of modernism."

= poet:bio =

 poet:name:: Ezra Weston Loomis Pound
 poet:born:: 1885-10-30
 poet:died:: 1972-11-01
 poet:birthplace:: Hailey, ID
 poet:wikipedia:: http://en.wikipedia.org/wiki/Ezra_pound

= akara:metadata =

 akara:type:: [[poetpaedia/poet]]
'''

# poet:image:: {{http://upload.wikimedia.org/wikipedia/commons/thumb/d/d3/Ezra_Pound.jpg/240px-Ezra_Pound.jpg}}

BASE_MOIN = 'moin'
BASE_ZEN = 'zen'

HTTP_CC = 'cache-control'
HTTP_STATUS = 'status'
HTTP_CT = 'content-type'

class TestHttpResponses :

    def setUp(self) :
        # Write a poet to the TestWiki, along with its resource type page and rulesheet

        H = httplib2.Http()
        headers = {'Content-Type': 'text/plain'};
        try:
            resp, content = H.request(POET_RESOURCE_TYPE_URI % BASE_MOIN, 'PUT',
                                      body=POET_RESOURCE_TYPE_CREOLE, headers=headers)
        except Exception as e:
            assert 0

        secret = config['http']['secret']

        signed_rulesheet = "#" + hashlib.sha1(secret + POET_RULESHEET).hexdigest() + POET_RULESHEET

        try:
            resp, content = H.request(POET_RULESHEET_URI % BASE_MOIN, 'PUT',
                                      body=signed_rulesheet, headers=headers)
        except Exception as e:
            assert 0

        try:
            resp, content = H.request(POET_URI % BASE_MOIN, 'PUT',
                                      body=POET_CREOLE, headers=headers)
        except Exception as e:
            assert 0

#    def tearDown(self) :
        # Perhaps delete the test pages

    def test_conneg1(self) :

        ACCEPT_HEADER = 'text/*;q=0.9,text/plain;q=0.6,text/html,application/xhtml+xml'
        EXPECTED_IMT = 'text/plain'

        H = httplib2.Http()
        try:
            resp, content = H.request(POET_URI % BASE_ZEN, 'GET',headers={'accept': ACCEPT_HEADER})
        except Exception as e:
            assert 0

        print "Content type: " + resp.get(HTTP_CT,"")
        assert resp.get(HTTP_CT,"") == EXPECTED_IMT

    def test_conneg1(self) :

        ACCEPT_HEADER = '*/*,application/xhtml+xml,application/json,text/plain'
        EXPECTED_IMT = 'application/json'

        H = httplib2.Http()
        try:
            resp, content = H.request(POET_URI % BASE_ZEN, 'GET',headers={'accept': ACCEPT_HEADER})
        except Exception as e:
            assert 0

        print "Content type: " + resp.get(HTTP_CT,"")
        assert resp.get(HTTP_CT,"") == EXPECTED_IMT

    def test_conneg_default(self) :

        # No accept header
        EXPECTED_IMT = 'application/json'

        H = httplib2.Http()
        try:
            resp, content = H.request(POET_URI % BASE_ZEN, 'GET')
        except Exception as e:
            assert 0

        print "Content type: " + resp.get(HTTP_CT,"")
        print "Content : " + content
        assert resp.get(HTTP_CT,"") == EXPECTED_IMT

    def test_ttl1(self) :

        EXPECTED_CC = 'max-age=86400'
        ACCEPT_HEADER = 'text/plain'

        H = httplib2.Http()
        try:
            resp, content = H.request(POET_URI % BASE_ZEN, 'GET',headers={'accept': ACCEPT_HEADER})
        except Exception as e:
            assert 0

        print "Content type: " + resp.get(HTTP_CT,"N/A")
        print "Cache control: " + resp.get(HTTP_CC,"N/A")
        print "Content : " + content
        assert resp.get(HTTP_STATUS,"9")[0] == "2" # successful response
        # FIXME Should be more robust than simple equality here
        assert resp.get(HTTP_CC,"") == EXPECTED_CC

    def test_ttl2(self) :

        EXPECTED_CC = 'max-age=43200'
        ACCEPT_HEADER = 'text/html'

        H = httplib2.Http()
        try:
            resp, content = H.request(POET_URI % BASE_ZEN, 'GET',headers={'accept': ACCEPT_HEADER})
        except Exception as e:
            assert 0

        print "Content type: " + resp.get(HTTP_CT,"N/A")
        print "Cache control: " + resp.get(HTTP_CC,"N/A")
        assert resp.get(HTTP_STATUS,"9")[0] == "2" # successful response
        # FIXME Should be more robust than simple equality here
        assert resp.get(HTTP_CC,"") == EXPECTED_CC

    def test_ttl_default(self) :

        EXPECTED_CC = 'max-age=3600'

        H = httplib2.Http()
        try:
            resp, content = H.request(POET_URI % BASE_ZEN, 'GET')
        except Exception as e:
            assert 0

        assert resp.get(HTTP_STATUS,"9")[0] == "2"
        assert resp.get(HTTP_CC,"") == EXPECTED_CC
