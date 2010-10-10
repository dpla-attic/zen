# Adapted from Django-MoinMoin
#
# http://code.google.com/p/django-moinmoin/
#
# Visit that page for instructions on how to use ... but instead of copying your settings
# into this file, add this to your moin/wsgi script;
#
#     os.environ['DJANGO_SETTINGS_MODULE'] = '<your_django_project>.settings'
#

from MoinMoin.auth import BaseAuth

import traceback

import base64
import cPickle as pickle
import sys

try:
    import hashlib
    md5_constructor = hashlib.md5
    sha_constructor = hashlib.sha1
except ImportError:
    import md5
    md5_constructor = md5.new
    import sha
    sha_constructor = sha.new

# This is included in case you want to create a log file during testing
import time
def writeLog(*args):
    '''Write an entry in a log file with a timestamp and all of the args.'''
    s = time.strftime('%Y-%m-%d %H:%M:%S ',time.localtime())
    for a in args:
        s = '%s %s;' % (s,a)
    log = open('/tmp/cookie.log', 'a') # +++ location for log file
    log.write('\n' + s + '\n')
    log.close()
    return

class DjangoAuth(BaseAuth):
    
    name = 'DjangoAuth'
    # +++ The next 2 lines may be useful if you are overriding the username method in your themes.
    # +++  If commented out, wiki pages will not have login or logout hyperlinks
    login_inputs = ['username', 'password'] # +++ required to get a login hyperlink in wiki navigation area
    logout_possible = True # +++ required to get a logout hyperlink in wiki navigation area
    
    def __init__(self, autocreate=False):
        self.autocreate = autocreate
        BaseAuth.__init__(self)
        from django.conf import settings
        
    def get_profile(self, user_id):
        from django.contrib.auth.models import User
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return False, {}
        try:
            self.user_profile = {}
            self.user_profile['username'] = user.username
            self.user_profile['name'] = user.first_name + ' ' + user.last_name
            self.user_profile['email'] = user.email
        except:
            return False, {}
        return True


    def get_session(self, session_id):

        try:
            from django.contrib.sessions.models import Session
            session = Session.objects.get(session_key=session_id)
        except Session.DoesNotExist:
            return False, ''

        try:
            from datetime import datetime
            #Has the session expired?
            if session.expire_date < datetime.now():
                return False, ''
            return True, session.session_data
        except:
            return False, ''

    def get_decoded(self, session_data):
        from django.conf import settings
        encoded_data = base64.decodestring(session_data)
        pickled, tamper_check = encoded_data[:-32], encoded_data[-32:]
        if md5_constructor(pickled + settings.SECRET_KEY).hexdigest() != tamper_check:
            return {}
        try:
            return pickle.loads(pickled)
        # Unpickling can cause a variety of exceptions. If something happens,
        # just return an empty dictionary (an empty session).
        except:
            return {}
    
    def request(self, request, user_obj, **kw):

        if user_obj and user_obj.auth_method == self.name:
            user_obj = None

        # if we're already authenticated, no need to do anything more
        if user_obj and user_obj.valid:
            return user_obj, False

        """Return (user-obj,False) if user is authenticated, else return (None,True). """
        # login = kw.get('login') # +++ example does not use this; login is expected in other application
        # user_obj = kw.get('user_obj')  # +++ example does not use this
        # username = kw.get('name') # +++ example does not use this
        # logout = kw.get('logout') # +++ example does not use this; logout is expected in other application
        import Cookie
        user = None  # user is not authenticated
        try_next = True  # if True, moin tries the next auth method in auth list
        otherAppCookie = "sessionid" # +++ username, email,useralias, session ID separated by #
        try:
            cookie = Cookie.SimpleCookie(kw.get('cookie',None))
        except Cookie.CookieError:
            cookie = None # ignore invalid cookies        

        if cookie and otherAppCookie in cookie: # having this cookie means user auth has already been done in other application
            # Work around SimpleCookie parsing bug in 2.6.4
            if type(cookie[otherAppCookie]) == unicode:
                result, session_raw = self.get_session(cookie[otherAppCookie])
            else:
                result, session_raw = self.get_session(cookie[otherAppCookie].value)

            if not result:
                return user, try_next
            session_decoded = self.get_decoded(session_raw)
            writeLog('Session Decoded', session_decoded)
            
            try:            
                result = self.get_profile(session_decoded['_auth_user_id'])
            except KeyError:
                writeLog('Could not find user id in decoded cookie')
                return user, try_next
                
            writeLog('got user profile', self.user_profile)
            
            if not result:
                return user, try_next
                
            from MoinMoin.user import User
            # giving auth_username to User constructor means that authentication has already been done.
            user = User(request, name=self.user_profile['username'], auth_username=self.user_profile['username'], auth_method=self.name)
            changed = False
            if self.user_profile['email'] != user.email: # was the email addr externally updated?
                user.email = self.user_profile['email'];
                changed = True # yes -> update user profile
            if self.user_profile['name'] != user.aliasname: # +++ was the aliasname externally updated?
                user.aliasname = self.user_profile['name'] ;
                changed = True # yes -> update user profile
            
            if user:
                user.create_or_update(changed)
            if user and user.valid:
                try_next = False # have valid user; stop processing auth method list
                writeLog(str(user))

        return user, try_next
