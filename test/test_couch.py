import sys

from amara.thirdparty import httplib2, json

import couchdb
import subprocess
import os
import tempfile
import shutil

"""
Nosetests for Zen's CouchDB support. Assumes CouchDB is running on port 5984.
"""

DEV_SECRET = 'TESTSECRET99'
COUCH_DB_NAME = 'zentest'

FEED_TYPE_URI = 'http://localhost:5984/%s/feed'%COUCH_DB_NAME
FEED_URI = 'http://localhost:5984/%s/%s'
FEED_ZEN_URI = 'http://localhost:8788/zen/couchtest/%s'
FEED_RULESHEET_URI = FEED_TYPE_URI+'/attachment?rev=%s'

HTTP_AC = 'accept'
HTTP_CT = 'content-type'
JSON_IMT = 'application/json'

ASSERT_GET_2XX = 'Response to GET of %s was %s, expected 2xx'

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
        resp, content = H.request('http://localhost:5984','GET',headers={HTTP_AC:JSON_IMT})
        assert HTTP_CT in resp, repr(resp)
        assert resp[HTTP_CT] == JSON_IMT, repr(resp)

        os.chdir(os.path.join(sys.path[0],'../etc/feedhub/bootstrap'))

        cls.couch = couchdb.Server()
        cls.couch.delete(COUCH_DB_NAME)
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
        assert resp['status'].startswith('2'), 'Problem saving rulesheet attachment: '+content

        # Create a feed
        ff = open('copia.js','r')
        feed_js = json.loads(ff.read())
        feed_ret = cls.db.save(feed_js)
        assert feed_ret is not None
        cls.feed_uri = FEED_URI%(COUCH_DB_NAME,feed_ret[0])
        cls.feed_zen_uri = FEED_ZEN_URI%feed_ret[0]

        # Start Akara/Zen
        cls.akara_wd = tempfile.mkdtemp(prefix='zentest_akara_')
        shutil.rmtree(cls.akara_wd)
        shutil.copytree(os.path.join(sys.path[0],'testakara'),cls.akara_wd)

        # CD to the Akara working directory, and start it
        os.chdir(cls.akara_wd)
        akara_instance = subprocess.Popen(['akara','-f','akara.conf','start'])

        # Give it time to start up properly
        import time; time.sleep(5)

        akara_instance.wait()
        assert akara_instance.returncode == 0 # Akara starts asynchronously
        
    @classmethod
    def tearDownClass(cls):
        #del cls.db
        #os.chdir(cls.akara_wd)
        #ak = subprocess.Popen(['akara','-f','akara.conf','stop'])
        #ak.wait()
        #shutil.rmtree(cls.akara_wd)
        pass

    def test_feed(self):
        resp, content = H.request(self.feed_uri,'GET',headers={HTTP_AC:JSON_IMT})
        assert resp['status'].startswith('2'), ASSERT_GET_2XX%(self.feed_uri,resp['status'])

    def test_zen_feed(self):
        resp, content = H.request(self.feed_zen_uri,'GET',headers={HTTP_AC:JSON_IMT})
        assert resp['status'].startswith('2'), ASSERT_GET_2XX%(self.feed_zen_uri,resp['status'])
        assert resp[HTTP_CT] == JSON_IMT
        print >>sys.stderr,"t2r"+repr(resp)
        print >>sys.stderr,"t2c"+repr(content)
