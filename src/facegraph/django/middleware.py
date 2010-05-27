# -*- coding: utf-8 -*-

from facegraph import Graph


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
                return MyGraph(self.access_token(request))
    
    """
    
    def process_request(self, request):
        request.graph = self.graph_for_request(request)
    
    def graph_for_request(self, request):
        """Return the `Graph` for a given request."""
        
        return Graph(self.access_token(request))
    
    def access_token(self, request):
        """Abstract method to retrieve the access token for a given request."""
        
        raise NotImplementedError
