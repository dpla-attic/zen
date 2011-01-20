import sys

from amara.thirdparty import httplib2, json
from akara.util import first_item

import subprocess
import tempfile
import os
import shutil
import random
import string
import threading
import itertools

"""
Nosetests for Zen's Moin-targetted features such as media type handling, bootstrapping, rulesheets,
cache control, ...
"""

HTTP_CC = 'cache-control'
HTTP_STATUS = 'status'
HTTP_CT = 'content-type'
HTTP_AC = 'accept'

ZEN_SECRET = "TESTSECRET99"
MOIN_ADMIN_USER = "admin"
MOIN_ADMIN_PASSWORD = "wiki8787"

POET_URI = "http://localhost:8788/zen/testwiki/poetpaedia/poet/epound"

wiki_wd = None
user_secret_file = None
zen_secret_file = None
moin_instance = None
akara_wd = None

def setup_module():
    """
    Stand up standalone Moin and Zen/Akara instances
    """

    global wiki_wd, user_secret_file, zen_secret_file, moin_instance, akara_wd
    # Start by creating a temporary directory where the wiki will be installed
    wiki_wd = tempfile.mkdtemp(prefix='zentest_moin_')
    # Now delete it so that copytree can recreate it. Duh.
    shutil.rmtree(wiki_wd)
    # Copy the wiki dir there ...
    shutil.copytree(os.path.join(sys.path[0],'testwiki'),wiki_wd)
    # Untar the underlay content
    os.chdir(os.path.join(wiki_wd,'wiki'))
    tar = subprocess.Popen(['tar','xf','underlay.tar'])
    tar.wait()
    assert tar.returncode == 0

    # Do the same for Zen/Akara
    akara_wd = tempfile.mkdtemp(prefix='zentest_akara_')
    shutil.rmtree(akara_wd)
    shutil.copytree(os.path.join(sys.path[0],'testakara'),akara_wd)

    # Start Moin
    os.chdir(wiki_wd)
    moin_instance = subprocess.Popen(['python','wikiserver.py'])

    # CD to the Akara working directory, and start it
    os.chdir(akara_wd)
    akara_instance = subprocess.Popen(['akara','-f','akara.conf','start'])

    # Give them both time to start up properly
    import time; time.sleep(5)

    akara_instance.wait()
    assert akara_instance.returncode == 0 # Akara starts asynchronously
    assert moin_instance.returncode is None # i.e. still running

    # Now prepare to bootstrap the Wiki ...

    # Need to provide credentials to wikibootstrap via a file
    user_secret_handle, user_secret_file = tempfile.mkstemp(prefix='zentest_usec_')
    os.write(user_secret_handle,"%s:%s" %(MOIN_ADMIN_USER,MOIN_ADMIN_PASSWORD))
    os.close(user_secret_handle)

    # Ditto for the Zen developer secret
    zen_secret_handle, zen_secret_file = tempfile.mkstemp(prefix='zentest_zsec_')
    os.write(zen_secret_handle,ZEN_SECRET)
    os.close(zen_secret_handle)

    # Bootstrap Moin with the poetpaedia example. This currently causes Moin to throw
    # harmless "broken pipe" errors. FIXME
    wbs_instance = subprocess.Popen(['wikibootstrap',
                                     '--usersecret',user_secret_file,
                                     '--zensecret',zen_secret_file,
                                     '--target','http://localhost:8788/moin/testwiki/poetpaedia',
                                     os.path.join(sys.path[0],'../etc/poetpaedia/bootstrap/')])
    wbs_instance.wait()
    assert wbs_instance.returncode == 0

def teardown_module():
    global wiki_wd, user_secret_file, zen_secret_file, moin_instance, akara_wd
    os.chdir(akara_wd)
    ak = subprocess.Popen(['akara','-f','akara.conf','stop'])
    ak.wait()
    shutil.rmtree(akara_wd)
    os.remove(user_secret_file)
    os.remove(zen_secret_file)
    moin_instance.kill()
    shutil.rmtree(wiki_wd)

def test_conneg1() :

    ACCEPT_HEADER = 'text/*;q=0.9,text/plain;q=0.6,text/html,application/xhtml+xml'
    EXPECTED_IMT = 'text/plain'

    H = httplib2.Http()
    try:
        resp, content = H.request(POET_URI, 'GET',headers={HTTP_AC: ACCEPT_HEADER})
    except Exception as e:
        assert 0,e

    assert resp.get(HTTP_CT,"") == EXPECTED_IMT, "Expected type %s, received type %s"%(EXPECTED_IMT,resp.get(HTTP_CT,"None"))

def test_conneg1() :

    ACCEPT_HEADER = '*/*,application/xhtml+xml,application/json,text/plain'
    EXPECTED_IMT = 'application/json'

    H = httplib2.Http()
    try:
        resp, content = H.request(POET_URI, 'GET',headers={HTTP_AC: ACCEPT_HEADER})
    except Exception as e:
        assert 0,e

    assert resp.get(HTTP_CT,"") == EXPECTED_IMT, "Expected type %s, received type %s"%(EXPECTED_IMT,resp.get(HTTP_CT,"None"))

def test_conneg_default() :

    # No accept header
    EXPECTED_IMT = 'application/json'

    H = httplib2.Http()
    try:
        resp, content = H.request(POET_URI, 'GET')
    except Exception as e:
        assert 0,e

    assert resp.get(HTTP_CT,"") == EXPECTED_IMT, "Expected type %s, received type %s"%(EXPECTED_IMT,resp.get(HTTP_CT,"None"))

def test_ttl1() :

    EXPECTED_CC = 'max-age=86400'
    ACCEPT_HEADER = 'text/plain'

    H = httplib2.Http()
    try:
        resp, content = H.request(POET_URI, 'GET',headers={HTTP_AC: ACCEPT_HEADER})
    except Exception as e:
        assert 0,e

    assert resp.get(HTTP_STATUS,"9")[0] == "2", "Expected 2xx response, received %s"%(resp.get(HTTP_STATUS,"None"))
    # FIXME Should be more robust than simple equality here and in other CC-checking tests
    assert resp.get(HTTP_CC,"") == EXPECTED_CC, "Expected C-C %s, received C-C %s"%(EXPECTED_CC,resp.get(HTTP_CC,"None"))

def test_ttl2() :

    EXPECTED_CC = 'max-age=43200'
    ACCEPT_HEADER = 'text/html'

    H = httplib2.Http()
    try:
        resp, content = H.request(POET_URI, 'GET',headers={HTTP_AC: ACCEPT_HEADER})
    except Exception as e:
        assert 0,e

    assert resp.get(HTTP_STATUS,"9")[0] == "2", "Expected 2xx response, received %s"%(resp.get(HTTP_STATUS,"None"))
    assert resp.get(HTTP_CC,"") == EXPECTED_CC, "Expected C-C %s, received C-C %s"%(EXPECTED_CC,resp.get(HTTP_CC,"None"))

def test_ttl_default() :

    EXPECTED_CC = 'max-age=3600'

    H = httplib2.Http()
    try:
        resp, content = H.request(POET_URI, 'GET')
    except Exception as e:
        assert 0,e

    assert resp.get(HTTP_STATUS,"9")[0] == "2", "Expected 2xx response, received %s"%(resp.get(HTTP_STATUS,"None"))
    assert resp.get(HTTP_CC,"") == EXPECTED_CC, "Expected C-C %s, received C-C %s"%(EXPECTED_CC,resp.get(HTTP_CC,"None"))

POUND_DESC = 'An updated description of Ezra Pound'
def test_update(desc=POUND_DESC, ignore_failures=False):

    # Read in EPound JSON, change description, and save

    H = httplib2.Http()
    try:
        resp, content = H.request(POET_URI, 'GET')
    except Exception as e:
        if not ignore_failures:
            assert 0,e

    epound = json.loads(content)
    epound[u'description'] = desc

    body=json.dumps(epound)
    headers={HTTP_CT:'application/json'}
    try:
        resp, content = H.request(POET_URI+'?type=poetpaedia/poet', 'PUT', body=body, headers=headers)
    except Exception as e:
        if not ignore_failures:
            assert 0,e

    put_resp = resp.get(HTTP_STATUS,'999')
    if not ignore_failures:
        assert put_resp[0] == "2", "Expected 2xx response, received %s"%(resp.get(HTTP_STATUS,"None"))

    headers={HTTP_AC:'application/json'}
    try:
        resp, content = H.request(POET_URI, 'GET', headers=headers)
    except Exception as e:
        if not ignore_failures:
            assert 0,e

    epound2 = json.loads(content)
    if not ignore_failures:
        assert epound2[u'description'] == desc, 'Expected %s, received %s'%(desc,repr(epound2[u'description']))

    return put_resp # Used by contention test

# Thread used by test_contention
class PutThread(threading.Thread):
    responses = []

    def run(self):
        # Update page with random text, ignoring PUT failures
        poet_desc = ''.join(random.choice(string.ascii_uppercase + string.digits) for i in range(20))
        resp = test_update(poet_desc,ignore_failures=True)
        self.responses.append(resp)

# This was supposed to test conflict detection in moinrest/Zen, but it seems that the race
# condition under which this would occur is too difficult to reproduce.  So disabling for
# now by prefixing with "_"
def _test_contention():

    # Make 50 attempts to create an update conflict with 3 PUTting clients
    threads = []
    for loop in xrange(1,200):
        t1 = PutThread()
        t2 = PutThread()

        t1.start()
        t2.start()

        t1.join()
        t2.join()

    # After that many attempts, there should be at least *some* 409 errors
    assert first_item(itertools.dropwhile(lambda x: x != '409',PutThread.responses)), "No conflicts detected"
