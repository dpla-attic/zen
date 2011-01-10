import sys

from amara.thirdparty import httplib2

import subprocess
import tempfile
import os
import shutil

"""
Nosetests for Zen's Moin-targetted features such as media type handling, bootstrapping, rulesheets,
cache control, ...
"""

HTTP_CC = 'cache-control'
HTTP_STATUS = 'status'
HTTP_CT = 'content-type'

MOIN_PORT = 8787
ZEN_SECRET = "TESTSECRET99"
MOIN_ADMIN_USER = "admin"
MOIN_ADMIN_PASSWORD = "wiki8787"

POET_URI = "http://localhost:8788/zen/testwiki/poetpaedia/poet/epound"

class TestHttpResponses :

    wiki_wd = None
    user_secret_file = None
    zen_secret_file = None
    moin_instance = None
    akara_wd = None

    @classmethod
    def setUpClass(cls):
        """
        Stand up standalone Moin and Zen/Akara instances
        """

        # Start by creating a temporary directory where the wiki will be installed
        cls.wiki_wd = tempfile.mkdtemp(prefix='zentest_moin_')
        # Now delete it so that copytree can recreate it. Duh.
        shutil.rmtree(cls.wiki_wd)
        # Copy the wiki dir there ...
        shutil.copytree(os.path.join(sys.path[0],'testwiki'),cls.wiki_wd)
        # Untar the underlay content
        os.chdir(os.path.join(cls.wiki_wd,'wiki'))
        tar = subprocess.Popen(['tar','xf','underlay.tar'])
        tar.wait()
        assert tar.returncode == 0

        # Do the same for Zen/Akara
        cls.akara_wd = tempfile.mkdtemp(prefix='zentest_akara_')
        shutil.rmtree(cls.akara_wd)
        shutil.copytree(os.path.join(sys.path[0],'testakara'),cls.akara_wd)

        # Start Moin
        os.chdir(cls.wiki_wd)
        cls.moin_instance = subprocess.Popen(['python','wikiserver.py'])

        # CD to the Akara working directory, and start it
        os.chdir(cls.akara_wd)
        akara_instance = subprocess.Popen(['akara','-f','akara.conf','start'])

        # Give them both time to start up properly
        import time; time.sleep(5)

        akara_instance.wait()
        assert akara_instance.returncode == 0 # Akara starts asynchronously
        assert cls.moin_instance.returncode is None # i.e. still running

        # Now prepare to bootstrap the Wiki ...

        # Need to provide credentials to wikibootstrap via a file
        user_secret_handle, cls.user_secret_file = tempfile.mkstemp(prefix='zentest_usec_')
        os.write(user_secret_handle,"%s:%s" %(MOIN_ADMIN_USER,MOIN_ADMIN_PASSWORD))
        os.close(user_secret_handle)

        # Ditto for the Zen developer secret
        zen_secret_handle, cls.zen_secret_file = tempfile.mkstemp(prefix='zentest_zsec_')
        os.write(zen_secret_handle,ZEN_SECRET)
        os.close(zen_secret_handle)

        # Bootstrap Moin with the poetpaedia example. This currently causes Moin to throw
        # harmless "broken pipe" errors. FIXME
        wbs_instance = subprocess.Popen(['wikibootstrap',
                                         '--usersecret',cls.user_secret_file,
                                         '--zensecret',cls.zen_secret_file,
                                         '--target','http://localhost:8788/moin/testwiki/poetpaedia',
                                         os.path.join(sys.path[0],'../etc/poetpaedia/bootstrap/')])
        wbs_instance.wait()
        assert wbs_instance.returncode == 0

    @classmethod
    def tearDownClass(cls):
        os.chdir(cls.akara_wd)
        ak = subprocess.Popen(['akara','-f','akara.conf','stop'])
        ak.wait()
        shutil.rmtree(cls.akara_wd)
        os.remove(cls.user_secret_file)
        os.remove(cls.zen_secret_file)
        cls.moin_instance.kill()
        shutil.rmtree(cls.wiki_wd)

    def test_conneg1(self) :

        ACCEPT_HEADER = 'text/*;q=0.9,text/plain;q=0.6,text/html,application/xhtml+xml'
        EXPECTED_IMT = 'text/plain'

        H = httplib2.Http()
        try:
            resp, content = H.request(POET_URI, 'GET',headers={'accept': ACCEPT_HEADER})
        except Exception as e:
            assert 0,e

        assert resp.get(HTTP_CT,"") == EXPECTED_IMT, "Expected type %s, received type %s"%(EXPECTED_IMT,resp.get(HTTP_CT,"None"))

    def test_conneg1(self) :

        ACCEPT_HEADER = '*/*,application/xhtml+xml,application/json,text/plain'
        EXPECTED_IMT = 'application/json'

        H = httplib2.Http()
        try:
            resp, content = H.request(POET_URI, 'GET',headers={'accept': ACCEPT_HEADER})
        except Exception as e:
            assert 0,e

        assert resp.get(HTTP_CT,"") == EXPECTED_IMT, "Expected type %s, received type %s"%(EXPECTED_IMT,resp.get(HTTP_CT,"None"))

    def test_conneg_default(self) :

        # No accept header
        EXPECTED_IMT = 'application/json'

        H = httplib2.Http()
        try:
            resp, content = H.request(POET_URI, 'GET')
        except Exception as e:
            assert 0,e

        assert resp.get(HTTP_CT,"") == EXPECTED_IMT, "Expected type %s, received type %s"%(EXPECTED_IMT,resp.get(HTTP_CT,"None"))

    def test_ttl1(self) :

        EXPECTED_CC = 'max-age=86400'
        ACCEPT_HEADER = 'text/plain'

        H = httplib2.Http()
        try:
            resp, content = H.request(POET_URI, 'GET',headers={'accept': ACCEPT_HEADER})
        except Exception as e:
            assert 0,e

        assert resp.get(HTTP_STATUS,"9")[0] == "2", "Expected 2xx response, received %s"%(resp.get(HTTP_STATUS,"None"))
        # FIXME Should be more robust than simple equality here and in other CC-checking tests
        assert resp.get(HTTP_CC,"") == EXPECTED_CC, "Expected C-C %s, received C-C %s"%(EXPECTED_CC,resp.get(HTTP_CC,"None"))

    def test_ttl2(self) :

        EXPECTED_CC = 'max-age=43200'
        ACCEPT_HEADER = 'text/html'

        H = httplib2.Http()
        try:
            resp, content = H.request(POET_URI, 'GET',headers={'accept': ACCEPT_HEADER})
        except Exception as e:
            assert 0,e

        assert resp.get(HTTP_STATUS,"9")[0] == "2", "Expected 2xx response, received %s"%(resp.get(HTTP_STATUS,"None"))
        assert resp.get(HTTP_CC,"") == EXPECTED_CC, "Expected C-C %s, received C-C %s"%(EXPECTED_CC,resp.get(HTTP_CC,"None"))

    def test_ttl_default(self) :

        EXPECTED_CC = 'max-age=3600'

        H = httplib2.Http()
        try:
            resp, content = H.request(POET_URI, 'GET')
        except Exception as e:
            assert 0,e

        assert resp.get(HTTP_STATUS,"9")[0] == "2", "Expected 2xx response, received %s"%(resp.get(HTTP_STATUS,"None"))
        assert resp.get(HTTP_CC,"") == EXPECTED_CC, "Expected C-C %s, received C-C %s"%(EXPECTED_CC,resp.get(HTTP_CC,"None"))
