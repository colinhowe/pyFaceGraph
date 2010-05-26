# -*- coding: utf-8 -*-

import cgi
import urllib2

from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
import djclsview
from urlobject import URLObject


class FacebookOAuthView(djclsview.View):
    
    """
    Abstract base class providing sensible defaults for Facebook OAuth views.
    
    This class should be used as a mixin when defining your OAuth authorization
    and callback views. For example:
    
        class Authorize(AuthorizeView, FacebookOAuthView):
            ...
        
        class Callback(CallbackView, FacebookOAuthView):
            ...
    
    """
    
    def redirect_uri(self):
        """The URI to redirect the client to after successful authorization."""
        
        return unicode(
            URLObject(scheme='http', host=self.request.get_host()) /
            reverse('oauth-callback'))
    
    def client_id(self):
        """The client ID for this app."""
        
        return settings.FACEBOOK_CLIENT_ID
    
    def client_secret(self):
        """The client secret for this app."""
        
        return settings.FACEBOOK_CLIENT_SECRET
    
    def fetch_url(self, url):
        """Fetch a given URL; return a string representing the response body."""
        
        conn = urllib2.urlopen(url)
        try:
            return conn.read()
        finally:
            conn.close()


class AuthorizeView(object):
    
    """
    Abstract base class for OAuth authorization.
    
    By default, this class just redirects to `self.authorize_url()` (see
    `FacebookOAuthView` for more information).
    
    Example usage:
    
        ## views.py:
        
        class Authorize(AuthorizeView, FBOAuthView):
            pass
        
        ## urls.py:
        
        patterns('myapp.views',
            url('^oauth/authorize/$, 'Authorize', name='oauth-authorize'),
        )
    
    """
    
    def authorize_url(self):
        """The URL to redirect the client to for authorization."""
        
        url = URLObject.parse('https://graph.facebook.com/oauth/authorize')
        url |= ('client_id', self.client_id())
        url |= ('redirect_uri', self.redirect_uri())
        
        scope = self.scope()
        if scope:
            url |= ('scope', ','.join(scope))
        
        display = self.display()
        if display:
            url |= ('display', display)
        
        return url
    
    def scope(self):
        """Return the list of additional permissions to request."""
        
        return []
    
    def display(self):
        """The authorization dialog form factor. Default is 'page'."""
        
        return None  # default.
    
    def __call__(self):
        return redirect(self.authorize_url())


class CallbackView(object):
    
    """
    Abstract base class for OAuth callback views.
    
    This class provides `get_access_token()`. It’s up to you to call it, save
    the result (e.g. in a signed cookie, session or DB record) and send the
    client on their way.
    
    Example usage:
    
        ## views.py:
        
        from django.shortcuts import redirect
        
        class Callback(CallbackView, FBOAuthView):
            def __call__(self):
                access_token = self.get_access_token()
                self.request.session['access_token'] = self.get_access_token()
                return redirect('/')
        
        ## urls.py:
        
        patterns('myapp.views',
            url('^oauth/callback/$, 'Callback', name='oauth-callback'),
        )
    
    """
    
    def get_access_token(self):
        """Retrieve the access token."""
        
        access_token_url = self.access_token_url()
        token_info = dict(cgi.parse_qsl(self.fetch_url(access_token_url)))
        return token_info['access_token']
    
    def access_token_url(self):
        """The URL to retrieve to exchange a code for an access token."""
        
        url = URLObject.parse('https://graph.facebook.com/oauth/access_token')
        url |= ('code', self.request.GET['code'])
        url |= ('client_id', self.client_id())
        url |= ('client_secret', self.client_secret())
        url |= ('redirect_uri', self.redirect_uri())
        return unicode(url)
