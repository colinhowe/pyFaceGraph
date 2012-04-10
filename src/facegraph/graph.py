# -*- coding: utf-8 -*-
import logging
import re
import urllib
import urllib2 as default_urllib2
import httplib as default_httplib
import traceback

from facegraph.url_operations import (add_path, get_host,
        add_query_params, update_query_params, get_path)

import bunch
import simplejson as json
from functools import partial

p = "^\(#(\d+)\)"
code_re = re.compile(p)

__all__ = ['Graph']

log = logging.getLogger('pyfacegraph')

class Graph(object):
    
    """
    Proxy for accessing the Facebook Graph API.
    
    This class uses dynamic attribute handling to provide a flexible and
    future-proof interface to the Graph API.
    
    Tutorial
    ========
    
    To get started using the API, create a new `Graph` instance with an access
    token:
    
        >>> g = Graph(access_token)  # Access token is optional.
        >>> g
        <Graph('https://graph.facebook.com/') at 0x...>
    
    Addressing Nodes
    ----------------
    
    Each `Graph` contains an access token and a URL. The graph you just created
    will have its URL set to 'https://graph.facebook.com/' by default (this is
    defined as the class attribute `Graph.API_ROOT`).

        >>> print g.url
        https://graph.facebook.com/
    
    To address child nodes within the Graph API, `Graph` supports dynamic
    attribute and item lookups:
    
        >>> g.me
        <Graph('https://graph.facebook.com/me') at 0x...>
        >>> g.me.home
        <Graph('https://graph.facebook.com/me/home') at 0x...>
        >>> g['me']['home']
        <Graph('https://graph.facebook.com/me/home') at 0x...>
        >>> g[123456789]
        <Graph('https://graph.facebook.com/123456789') at 0x...>
    
    Note that a `Graph` instance is rarely modified; these methods return copies
    of the original object. In addition, the API is lazy: HTTP requests will
    never be made unless you explicitly make them.
    
    Retrieving Nodes
    ----------------
    
    You can fetch data by calling a `Graph` instance:
    
        >>> about_me = g.me()
        >>> about_me
        Node({'about': '...', 'id': '1503223370'})
    
    This returns a `Node` object, which contains the retrieved data. `Node` is
    a subclass of `bunch.Bunch`, so you can access keys using attribute syntax:
    
        >>> about_me.id
        '1503223370'
        >>> about_me.first_name
        'Zachary'
        >>> about_me.hometown.name
        'London, United Kingdom'
    
    Accessing non-existent attributes or items will return a `Graph` instance
    corresponding to a child node. This `Graph` can then be called normally, to
    retrieve the child node it represents:
    
        >>> about_me.home
        <Graph('https://graph.facebook.com/me/home') at 0x...>
        >>> about_me.home()
        Node({'data': [...]})
    
    See `Node`’s documentation for further examples.
    
    Creating, Updating and Deleting Nodes
    -------------------------------------
    
    With the Graph API, node manipulation is done via HTTP POST requests. The
    `post()` method on `Graph` instances will POST to the current URL, with
    varying semantics for each endpoint:
    
        >>> post = g.me.feed.post(message="Test.")  # Status update
        >>> post
        Node({'id': '...'})
        >>> g[post.id].comments.post(message="A comment.") # Comment on the post
        Node({'id': '...'})
        >>> g[post.id].likes.post()  # Like the post
        True
        
        >>> event = g[121481007877204]()
        >>> event.name
        'Facebook Developer Garage London May 2010'
        >>> event.rsvp_status is None
        True
        >>> event.attending.post()  # Attend the given event
        True
    
    Deletes are just POST requests with `?method=delete`; the `delete()` method
    is a helpful shortcut:
    
        >>> g[post.id].delete()
        True
    
    """
    
    API_ROOT = 'https://graph.facebook.com/'
    DEFAULT_TIMEOUT = 0 # No timeout as default
    
    def __init__(self, access_token=None, err_handler=None, timeout=DEFAULT_TIMEOUT, retries=5, urllib2=None, httplib=None, **state):
        self.access_token = access_token
        self.err_handler = err_handler
        self.url = self.API_ROOT
        self.timeout = timeout
        self.retries = retries
        self.__dict__.update(state)
        if urllib2 is None:
            import urllib2
        self.urllib2 = urllib2
        if httplib is None:
            import httplib
        self.httplib = httplib
    
    def __repr__(self):
        return '<Graph(%r) at 0x%x>' % (self.url, id(self))
    
    def copy(self, **update):
        """Copy this Graph, optionally overriding some attributes."""
        return type(self)(access_token=self.access_token, 
                          err_handler=self.err_handler,
                          timeout=self.timeout,
                          retries=self.retries,
                          urllib2=self.urllib2,
                          httplib=self.httplib,
                          **update)
    
    def __getitem__(self, item):
        if isinstance(item, slice):
            log.debug('Deprecated magic slice!')
            log.debug( traceback.format_stack())
            return self._range(item.start, item.stop)
        return self.copy(url=add_path(self.url, unicode(item)))
    
    def __getattr__(self, attr):
        return self[attr]

    def _range(self, start, stop):
        params = {'offset': start,
                  'limit': stop - start}
        return self.copy(url=add_query_params(self.url, params))

    def with_url_params(self, param, val):
        """
            this used to overload the bitwise OR op
        """
        return self.copy(url=update_query_params(self.url, (param, val)))

    def __call__(self, **params):
        log.debug('Deprecated magic call!')
        log.debug( traceback.format_stack())
        return self.call_fb(**params)
    
    def call_fb(self, **params):
        """Read the current URL, and JSON-decode the results."""

        if self.access_token:
            params['access_token'] = self.access_token
        url = update_query_params(self.url, params)
        data = json.loads(self.fetch(url,
                                     timeout=self.timeout,
                                     retries=self.retries,
                                     urllib2=self.urllib2,
                                     httplib=self.httplib))
        return self.process_response(data, params)

    def __iter__(self):
        raise TypeError('%r object is not iterable' % self.__class__.__name__)

    def __sentry__(self):
        return 'Graph(url: %s, params: %s)' % (self.url, repr(self.__dict__))
    
    def fields(self, *fields):
        """Shortcut for `?fields=x,y,z`."""
        return self | ('fields', ','.join(fields))
    
    def ids(self, *ids):
        """Shortcut for `?ids=1,2,3`."""
        
        return self | ('ids', ','.join(map(str, ids)))
    
    def process_response(self, data, params, method=None):
        if isinstance(data, dict):
            if data.get("error"):
                code = data["error"].get("code")
                if code is None:
                    code = data["error"].get("error_code")
                msg = data["error"].get("message")
                if msg is None:
                    msg = data["error"].get("error_msg")
                if code is None:
                    code_match = code_re.match(msg)
                    if code_match is not None:
                        code = int(code_match.group(1))
                e = GraphException(code, msg, graph=self, params=params, method=method)
                if self.err_handler:
                    return self.err_handler(e=e)
                else:
                    raise e
            return bunch.bunchify(data)
        return data
    
    def post(self, **params):
        """
        POST to this URL (with parameters); return the JSON-decoded result.
        
        Example:
        
            >>> Graph('ACCESS TOKEN').me.feed.post(message="Test.")
            Node({'id': '...'})
        
        Some methods allow file attachments so uses MIME request to send those through.
        Must pass in a file object as 'file'
        """
        
        if self.access_token:
            params['access_token'] = self.access_token
        
        if get_path(self.url).split('/')[-1] in ['photos']:
            params['timeout'] = self.timeout
            params['httplib'] = self.httplib
            fetch = partial(self.post_mime, 
                            self.url,
                            httplib=self.httplib,
                            retries=self.retries, 
                            **params)
        else:
            params = dict([(k, v.encode('UTF-8')) for (k,v) in params.iteritems() if v is not None])
            fetch = partial(self.fetch, 
                            self.url, 
                            urllib2=self.urllib2,
                            httplib=self.httplib,
                            timeout=self.timeout,
                            retries=self.retries, 
                            data=urllib.urlencode(params))
        
        data = json.loads(fetch())
        return self.process_response(data, params, "post")
    
    def post_file(self, file, **params):
        if self.access_token:
            params['access_token'] = self.access_token
        params['file'] = file
        params['timeout'] = self.timeout
        params['httplib'] = self.httplib
        data = json.loads(self.post_mime(self.url, **params))
        
        return self.process_response(data, params, "post_file")
    
    @staticmethod
    def post_mime(url, httplib=default_httplib, timeout=DEFAULT_TIMEOUT, retries=5, **kwargs):
        body = []
        crlf = '\r\n'
        boundary = "graphBoundary"
        
        # UTF8 params
        utf8_kwargs = dict([(k, v.encode('UTF-8')) for (k,v) in kwargs.iteritems() if k != 'file' and v is not None])
        
        # Add args
        for (k,v) in utf8_kwargs.iteritems():
            body.append("--"+boundary)
            body.append('Content-Disposition: form-data; name="%s"' % k) 
            body.append('')
            body.append(str(v))
        
        # Add raw data
        file = kwargs.get('file')
        if file:
            file.open()
            data = file.read()
            file.close()
            
            body.append("--"+boundary)
            body.append('Content-Disposition: form-data; filename="facegraphfile.png"')
            body.append('')
            body.append(data)
            
            body.append("--"+boundary+"--")
            body.append('')
        
        body = crlf.join(body)
        
        # Post to server
        kwargs = {}
        if timeout:
            kwargs = {'timeout': timeout}
        r = httplib.HTTPSConnection(get_host(url), **kwargs)
        headers = {'Content-Type': 'multipart/form-data; boundary=%s' % boundary,
                   'Content-Length': str(len(body)),
                   'MIME-Version': '1.0'}
        
        r.request('POST', get_path(url).encode(), body, headers)
        attempt = 0
        while True:
            try:
                return r.getresponse().read()
            except (httplib.BadStatusLine, IOError):
                if attempt < retries:
                    attempt += 1
                else:
                    raise
            finally:
                r.close()
    
    def delete(self):
        """
        Delete this resource. Sends a POST with `?method=delete`
        """
        return self.post(method='delete')
    
    @staticmethod
    def fetch(url, data=None, urllib2=default_urllib2, httplib=default_httplib, timeout=DEFAULT_TIMEOUT, retries=None):
        """
        Fetch the specified URL, with optional form data; return a string.
        
        This method exists mainly for dependency injection purposes. By default
        it uses urllib2; you may override it and use an alternative library.
        """
        conn = None
        attempt = 0
        while True:
            try:
                kwargs = {}
                if timeout:
                    kwargs = {'timeout': timeout}
                conn = urllib2.urlopen(url, data=data, **kwargs)
                return conn.read()
            except urllib2.HTTPError, e:
                return e.fp.read()        
            except (httplib.BadStatusLine, IOError):
                if attempt < retries:
                    attempt += 1
                else:
                    raise
            finally:
                conn and conn.close()

    def __sentry__(self):
        """
        Transform the graph object into something that sentry can
        understand
        """
        return "Graph(%s, %s)" % (self.url, str(self.__dict__))


class GraphException(Exception):
    def __init__(self, code, message, args=None, params=None, graph=None, method=None):
        Exception.__init__(self)
        if args is not None:
            self.args = args
        self.message = message
        self.code = code
        self.params = params
        self.graph = graph
        self.method = method

    def __repr__(self):
        return str(self)

    def __str__(self):
        s = self.message
        if self.graph:
            s += "Node: %s" % self.graph.url
        if self.params:
            s += ", Params: %s" % self.params
        if self.code:
            s +=  ", (%s)" % self.code
        return s