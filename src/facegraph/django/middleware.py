# -*- coding: utf-8 -*-

from django.conf import settings

from facegraph import signature
from facegraph import Graph, decode_signed_request


class FacebookGraphMiddleware(object):
    
    """
    Abstract middleware to attach a `facegraph.Graph` instance to each request.
    
    The simplest way to use this middleware is to subclass it and define
    `access_token()`:
    
        class GraphSessionMiddleware(FacebookGraphMiddleware):
            def access_token(self, request):
                return request.session['access_token']
    
    You can also re-define how `Graph` instances are constructed; this is useful
    if you have your own subclass of `Graph` you’d like to use instead:
    
        class MyGraph(Graph):
            pass
        
        class MyGraphSessionMiddleware(GraphSessionMiddleware):
            def graph_for_request(self, request):
                access_token = self.access_token(request)
                if access_token:
                    return MyGraph(access_token)
                return MyGraph()
    
    Note that if `access_token()` returns a false value (e.g. `None`), an
    unauthenticated `Graph()` instance will still be attached to the request.
    You can check this in your views like so:
    
        if request.graph.access_token:
            # Auth'd
        else:
            # Not auth'd
    
    """
    
    def process_request(self, request):
        request.graph = self.graph_for_request(request)
    
    def graph_for_request(self, request):
        """Return the `Graph` for a given request."""
        
        access_token = self.access_token(request)
        if access_token:
            return Graph(access_token)
        return Graph()
    
    def access_token(self, request):
        """Abstract method to retrieve the access token for a given request."""
        
        raise NotImplementedError


class FacebookCanvasMiddleware(object):
    
    """
    Middleware to decode `signed_request` parameters for canvas applications.
    
    If verification is successful, the decoded value is attached to each request
    as `request.fbrequest`. If either: `signed_request` is not present;
    `app_secret()` returns a false value; or verification fails,
    `request.fbrequest` will be set to `None`.
    
    By default, this middleware uses `settings.FACEBOOK_APP_SECRET` as the
    application secret, but you can subclass and override the `app_secret()`
    method to specify your own.
    """
    
    def process_request(self, request):
        app_secret = self.app_secret(request)
        raw_fbrequest = request.GET.get('signed_request', None)
        if not (app_secret and raw_fbrequest):
            request.fbrequest = None
            return
        
        try:
            request.fbrequest = decode_signed_request(app_secret, raw_fbrequest)
        except (signature.InvalidSignature, signature.UnknownSignatureAlgorithm):
            request.fbrequest = None
    
    def app_secret(self, request):
        """Semi-abstract method to retrieve the FB app secret for a request."""
        
        return getattr(settings, 'FACEBOOK_APP_SECRET', None)


class FacebookCanvasGraphMiddleware(FacebookGraphMiddleware):
    
    """A FacebookGraphMiddleware that uses the `signed_request`."""
    
    def access_token(self, request):
        """Retrieve the access token from `request.fbrequest`."""
        
        if request.fbrequest:
            return request.fbrequest.get('oauth_token')
