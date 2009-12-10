"""
Copyright 2009 Zepheira

Provides basic functions for interacting with Yammer via the Yammer API v1:

  https://www.yammer.com/api_doc.html

Depends on the installation of a Python OAuth library:

  http://code.google.com/p/oauth/
  http://oauth.googlecode.com/svn/code/python/

This will behave like a bot.  To that end, there should probably be
a 'member' of the organization that is clearly not associated with
any actual user.  bot@example.org, for instance.  All public messages
will be available to the bot, and the bot can broadcast publically.

So the OAuth consumer in this case is also acting in concert with the
bot as an authenticated user.  This is not a particularly safe method
security-wise; anybody who seizes on the configuration for this code
can immediately start reading from and posting to a Yammer group.
There are security concerns with securing any secret; this code
contains and relies on two secrets.

Usage:

  client = YammerClient()

  messages_xml = client.get_messages()
  # Users of libyammer should be able to keep track of the
  # latest message ID in the group to avoid overextending
  # Yammer resources.
  latest_messages_xml = client.get_messaegs(newest_msg_id)

  message_xml = client.post_message('Talking to all my Yammer cohort')

To procure bot keys, run client.bootstrap_keys() and be sure to have
a browser nearby logged in to Yammer as the appropriate bot user.
The keys should reside in this file.

Written by Ryan Lee <ryanlee@zepheira.com>
Based heavily on oauth client/consumer demo code and Yammer documentation.
"""

# TODO: conf file for bot user keys
# TODO: make library friendly, with a setup.py and eggs

import httplib
import time
import oauth.oauth as oauth

# application-specific information
CONSUMER_KEY = 'OjQGqHtQIR54dyBHnMZOgQ'
CONSUMER_SECRET = 'ORUaT6j7av3bvaJxZPo4TPDBiyAt0wXwjp0a9KSUF0'

BOT_KEY = 'Pbej35AMuWmXbIkZmWQVRA'
BOT_SECRET = 'xyH1NPflGN9ks1MvieIqdzkkaAQZy1bZS01T0FFI8o'

# Yammer URLs
REQUEST_TOKEN_URL = 'https://www.yammer.com/oauth/request_token'
ACCESS_TOKEN_URL = 'https://www.yammer.com/oauth/access_token'
AUTHORIZATION_URL = 'https://www.yammer.com/oauth/authorize'

GET_MESSAGES_URL = 'https://www.yammer.com/api/v1/messages.xml'
POST_MESSAGE_URL = 'https://www.yammer.com/api/v1/messages/'

# Base fetch class
class OAuthClient(oauth.OAuthClient):
    def __init__(self, server, port=httplib.HTTP_PORT, request_token_url = REQUEST_TOKEN_URL, access_token_url = ACCESS_TOKEN_URL, authorization_url = AUTHORIZATION_URL):
        self.server = server
        self.port = port
        self.request_token_url = request_token_url
        self.access_token_url = access_token_url
        self.authorization_url = authorization_url
        self.connection = httplib.HTTPSConnection("%s:%d" % (self.server, self.port))

    def fetch_request_token(self, oauth_request):
        self.connection.request(oauth_request.http_method, self.request_token_url, headers=oauth_request.to_header())
        response = self.connection.getresponse()
        return oauth.OAuthToken.from_string(response.read())

    def fetch_access_token(self, oauth_request):
        self.connection.request(oauth_request.http_method, self.access_token_url, headers=oauth_request.to_header()) 
        response = self.connection.getresponse()
        return oauth.OAuthToken.from_string(response.read())

    def authorize_token(self, oauth_request):
        self.connection.request(oauth_request.http_method, oauth_request.to_url()) 
        response = self.connection.getresponse()
        return response.read()

    def access_resource(self, oauth_request):
        if (oauth_request.http_method == 'POST'):
            headers = {'Content-Type' :'application/x-www-form-urlencoded'}
            self.connection.request(oauth_request.http_method, oauth_request.http_url, body=oauth_request.to_postdata(), headers=headers)
        else:
            self.connection.request(oauth_request.http_method, oauth_request.to_url())
        response = self.connection.getresponse()
        return response.read()

class YammerClient():
    def __init__(self):
        self.client = OAuthClient('www.yammer.com', 443)
        self.consumer = oauth.OAuthConsumer(CONSUMER_KEY, CONSUMER_SECRET)
        self.bot_token = oauth.OAuthToken(BOT_KEY, BOT_SECRET)
        self.sha1 = oauth.OAuthSignatureMethod_HMAC_SHA1()

    def bootstrap_keys(self):
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(self.consumer, http_url=self.client.request_token_url)
        oauth_request.sign_request(self.sha1, self.consumer, None)
        token = self.client.fetch_request_token(oauth_request)

        print 'Visit the following URL in your browser and authorize Orth,'
        print 'then return here with a verification code.'
        print '%s%s%s' % (AUTHORIZATION_URL, '?oauth_token=', str(token.key))
        verifier = raw_input('Enter 4-digit verification code: ')
    
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(self.consumer, token=token, verifier=verifier, http_url=self.client.access_token_url)
        oauth_request.sign_request(self.sha1, self.consumer, token)
        token = self.client.fetch_access_token(oauth_request)

        print 'Copy and paste the following, replacing their values in the'
        print 'header of this script.'
        print 'BOT_KEY = %s' % str(token.key)
        print 'BOT_SECRET = %s' % str(token.secret)
    
    def get_messages(self, latest_mid):
        parameters = { 'newer_than': latest_mid }
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(self.consumer, token=self.bot_token, http_method='GET', http_url=GET_MESSAGES_URL, parameters=parameters)
        oauth_request.sign_request(self.sha1, self.consumer, self.bot_token)
        response = self.client.access_resource(oauth_request)
        print response

    def post_message(self, msg_text):
        parameters = { 'body': msg_text }
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(self.consumer, token=self.bot_token, http_method='POST', http_url=POST_MESSAGE_URL, parameters=parameters)
        oauth_request.sign_request(self.sha1, self.consumer, self.bot_token)
        response = self.client.access_resource(oauth_request)
        print response

if __name__ == '__main__':
    y = YammerClient()
    r = y.get_messages()
    print r
