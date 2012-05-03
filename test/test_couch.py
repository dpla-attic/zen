"""
Nosetests for Zen's CouchDB support. By default assumes CouchDB is running on
port 5984 of localhost.

You can override this through the environment, for example:

COUCH_DB_BASE=http://rex.zepheira.com:5984; AKARA_BASE=http://rex.zepheira.com:8788; nosetests test/test_couch.py
"""

import os, sys

from amara.thirdparty import httplib2, json
from amara.lib import iri

from string import Template

import subprocess
import os
import tempfile
import shutil

try:
    import couchdb
except:
    assert False, "CouchDB (and python-couchdb) needs to be installed and running on port 5984 for these tests to run"

COUCH_DB_BASE = os.environ.get('COUCH_DB_BASE', 'http://localhost:5984')
AKARA_BASE = os.environ.get('AKARA_BASE', 'http://localhost:8788')

DEV_SECRET = 'TESTSECRET99'
COUCH_DB_NAME = 'zentest'

FEED_TYPE_URI = iri.join(COUCH_DB_BASE, COUCH_DB_NAME, 'feed')
FEED_URI = iri.join(COUCH_DB_BASE, '%s/%s')
FEED_ZEN_URI = iri.join(AKARA_BASE, 'zen/couchtest/%s')
FEED_RULESHEET_URI = FEED_TYPE_URI+'/attachment?rev=%s'
BLAH_FEED_ZEN_URI = (FEED_ZEN_URI%'blah')
BLAH_FEED_ZEN_PUT_URI = BLAH_FEED_ZEN_URI+'?type=feed'

HTTP_AC = 'accept'
HTTP_AC_LANG = 'accept-language'
HTTP_CT = 'content-type'
HTTP_CL = 'content-language'
IMT_JSON = 'application/json'
IMT_TEXT = 'text/plain'

ASSERT_2XX = 'Response to %s of %s was %s, expected 2xx'

H = httplib2.Http()
H.force_exception_to_status_code = True

class TestCouchDB :

    couch = None
    db = None
    akara_wd = None
    feed_id = None

    @classmethod
    def setUpClass(cls):
        """
        Setup CouchDB with the feedhub demo
        """

        # Check that couchdb is running
        resp, content = H.request(COUCH_DB_BASE, 'GET', headers={HTTP_AC:IMT_JSON})
        assert HTTP_CT in resp, repr(resp)
        assert resp[HTTP_CT] == IMT_JSON, repr(resp)

        orig_cwd = sys.path[0]
        os.chdir(os.path.join(sys.path[0],'../etc/feedhub/bootstrap'))

        cls.couch = couchdb.Server()
        try:
            cls.couch.delete(COUCH_DB_NAME)
        except:
            pass
        cls.db = cls.couch.create(COUCH_DB_NAME)
        assert cls.db is not None

        # Create the feed type resource
        ftf = open('__feed__.js','r')
        feedtype = json.loads(ftf.read())
        feedtype_ret = cls.db.save(feedtype)
        assert feedtype_ret is not None

        # Sign and store the rulesheet as an attachment to the feed type document
        sign = subprocess.Popen(['sign_rulesheet',DEV_SECRET,'__feed__.rsheet'],
                                stdout=subprocess.PIPE)
        assert sign is not None
        sign.wait()
        rsheet, err = sign.communicate()
        rsheet_uri = FEED_RULESHEET_URI%feedtype_ret[1]
        resp, content = H.request(rsheet_uri,'PUT',body=rsheet)
        assert resp['status'].startswith('2'), 'Problem saving rulesheet as attachment: '+content

        # Create a feed
        ff = open('copia.js','r')
        feed_js = json.loads(ff.read())
        feed_ret = cls.db.save(feed_js)
        assert feed_ret is not None
        cls.feed_uri = FEED_URI%(COUCH_DB_NAME,feed_ret[0])
        cls.feed_zen_uri = FEED_ZEN_URI%feed_ret[0]

        # Copy akara.conf to temp dir
        os.chdir(orig_cwd)
        cls.akara_wd = tempfile.mkdtemp(prefix='zentest_akara_')
        akc_orig = open('testakara/akara.conf','r').read()
        ak_template = Template(akc_orig)
        akc_new = ak_template.substitute({"configRoot":cls.akara_wd})
        akara_conf = open(os.path.join(cls.akara_wd,'akara.conf'),'w')
        akara_conf.write(akc_new)
        akara_conf.close()

        # CD to the Akara working directory, and start it
        os.chdir(cls.akara_wd)
        akara_instance = subprocess.Popen(['akara','-f','akara.conf','setup'])
        akara_instance.wait()
        akara_instance = subprocess.Popen(['akara','-f','akara.conf','start','-f'])

        # Give it time to start up properly
        import time; time.sleep(5)

        akara_instance.wait()
        assert akara_instance.returncode == 0 # Akara starts asynchronously
        
    @classmethod
    def tearDownClass(cls):
        cls.couch.delete(COUCH_DB_NAME)
        os.chdir(cls.akara_wd)
        ak = subprocess.Popen(['akara','-f','akara.conf','stop'])
        ak.wait()
        shutil.rmtree(cls.akara_wd)

    def test_feed(self):
        resp, content = H.request(self.feed_uri,'GET',headers={HTTP_AC:IMT_JSON})
        assert resp['status'].startswith('2'), ASSERT_2XX%('GET',self.feed_uri,resp['status'])

    def test_zen_feed(self):
        resp, content = H.request(self.feed_zen_uri,'GET',headers={HTTP_AC:IMT_JSON})
        assert resp['status'].startswith('2'), ASSERT_2XX%('GET',self.feed_zen_uri,resp['status'])
        assert resp[HTTP_CT] == IMT_JSON

    def test_zen_feed_update(self):
        new_feed = {
                       "name": "Copia",
                       "source": "http://copia.posterous.com/",
                       "description": "An updated description for Copia",
                   }   

        # Update it...
        resp, content = H.request(self.feed_zen_uri,'PUT',
                                  body=json.dumps(new_feed),
                                  headers={HTTP_CT:IMT_JSON,HTTP_AC:IMT_JSON})
        assert resp['status'].startswith('2'), ASSERT_2XX%('PUT',self.feed_zen_uri,resp['status'])

        # ... then check it was updated
        resp, content = H.request(self.feed_zen_uri,'GET',headers={HTTP_AC:IMT_JSON})
        assert resp['status'].startswith('2'), ASSERT_2XX%('GET',self.feed_zen_uri,resp['status'])
        assert resp.get(HTTP_CT,"") == IMT_JSON
        read_feed = json.loads(content)
        assert read_feed.get('description') == new_feed['description'], read_feed

    def test_zen_new_resource(self):
        # Create a new feed from scratch via Zen

        new_feed = {
                       "name": "Blah Blah",
                       "source": "http://blah.example.net",
                       "description": "A feed about nothing in particular",
                       "zen:metadata": {
                           "zen:type":"feed"
                       }
                   }   

        resp, content = H.request(BLAH_FEED_ZEN_PUT_URI,'PUT',
                                  body=json.dumps(new_feed),
                                  headers={HTTP_CT:IMT_JSON,HTTP_AC:IMT_JSON})
        assert resp['status'].startswith('2'), ASSERT_2XX%('PUT',BLAH_FEED_ZEN_PUT_URI,resp['status'])

        # Check that it works as expected
        resp, content = H.request(BLAH_FEED_ZEN_URI,'GET',headers={HTTP_AC:IMT_JSON})
        assert resp['status'].startswith('2'), ASSERT_2XX%('GET',BLAH_FEED_ZEN_URI,resp['status'])
        assert resp.get(HTTP_CT,"") == IMT_JSON

    def test_zen_language_conneg1(self):
        # No preferred language, so first wins (English)

        resp, content = H.request(self.feed_zen_uri,'GET',headers={HTTP_AC:IMT_TEXT})
        assert resp.get(HTTP_CL,"") == "en", "Content-Language response is %s, expecting en"%resp.get(HTTP_CL,None)
        assert content == "en feed", content

    def test_zen_language_conneg2(self):
        # Request French feed

        resp, content = H.request(self.feed_zen_uri,'GET',headers={HTTP_AC:IMT_TEXT,HTTP_AC_LANG:"fr"})
        assert resp.get(HTTP_CL,"") == "fr", "Content-Language response is %s, expecting fr"%resp.get(HTTP_CL,None)
        assert content == "fr feed", content

    def test_zen_language_conneg3(self):
        # Request English feed

        resp, content = H.request(self.feed_zen_uri,'GET',headers={HTTP_AC:IMT_TEXT,HTTP_AC_LANG:"en"})
        assert resp.get(HTTP_CL,"") == "en", "Content-Language response is %s, expecting en"%resp.get(HTTP_CL,None)
        assert content == "en feed", content

    def _test_zen_language_conneg4(self): # FIXME good test but fails atm and not sure how best to fix
        # Request non-existent German feed. Should return English

        resp, content = H.request(self.feed_zen_uri,'GET',headers={HTTP_AC:IMT_TEXT,HTTP_AC_LANG:"de"})
        assert resp.get(HTTP_CL,"") == "en", "Content-Language response is %s, not en"%resp.get(HTTP_CL,None)
        assert content == "en feed", content
