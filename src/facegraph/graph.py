# -*- coding: utf-8 -*-

import pprint
import urllib
import urllib2

import bunch
import simplejson as json
from urlobject import URLObject

__all__ = ['Graph']


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
    defined as the class attribute `Graph.API_ROOT`). The URL is represented as
    a `URLObject`; see <http://github.com/zacharyvoase/urlobject> for more
    information. Remember that you can treat it exactly as you would a `unicode`
    string; it just supports a few more methods to enable easy URL manipulation.
    
        >>> g.url
        <URLObject(u'https://graph.facebook.com/') at 0x...>
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
    
    API_ROOT = URLObject.parse('https://graph.facebook.com/')
    
    def __init__(self, access_token=None, **state):
        self.access_token = access_token
        self.url = self.API_ROOT
        self.__dict__.update(state)
    
    def __repr__(self):
        return '<Graph(%r) at 0x%x>' % (str(self.url), id(self))
    
    def copy(self, **update):
        """Copy this Graph, optionally overriding some attributes."""
        
        return type(self)(access_token=self.access_token, **update)
    
    def __getitem__(self, item):
        return self.copy(url=(self.url / unicode(item)))
    
    def __getattr__(self, attr):
        return self[attr]
    
    def __or__(self, params):
        return self.copy(url=(self.url | params))
    
    def __and__(self, params):
        return self.copy(url=(self.url & params))
    
    def __call__(self, **params):
        """Read the current URL, and JSON-decode the results."""
        
        if self.access_token:
            params['access_token'] = self.access_token
        
        data = json.loads(self.fetch(self.url | params))
        return Node._new(self, data)
    
    def fields(self, *fields):
        """Shortcut for `?fields=x,y,z`."""
        
        return self | ('fields', ','.join(fields))
    
    def ids(self, *ids):
        """Shortcut for `?ids=1,2,3`."""
        
        return self | ('ids', ','.join(map(str, ids)))
    
    def post(self, **params):
        
        """
        POST to this URL (with parameters); return the JSON-decoded result.
        
        Example:
        
            >>> Graph('ACCESS TOKEN').me.feed.post(message="Test.")
            Node({'id': '...'})
        
        """
        
        if self.access_token:
            params['access_token'] = self.access_token
        
        data = json.loads(self.fetch(self.url, data=urllib.urlencode(params)))
        return Node._new(self, data)
    
    def delete(self):
        """Delete this resource. Sends a POST with `?method=delete`."""
        
        return self.post(method='delete')
    
    @staticmethod
    def fetch(url, data=None):
        
        """
        Fetch the specified URL, with optional form data; return a string.
        
        This method exists mainly for dependency injection purposes. By default
        it uses urllib2; you may override it and use an alternative library.
        """
        
        conn = urllib2.urlopen(url, data=data)
        try:
            return conn.read()
        finally:
            conn.close()


class Node(bunch.Bunch):
    
    """
    Represent a JSON dictionary result from the Facebook Graph API.
    
    Accessing Items
    ---------------
    
    You can access items using either attribute or item syntax:
    
        >>> n = Node._new(None, {'a': 1, 'b': {'c': 3}})
        >>> n.a
        1
        >>> n['a']
        1
        >>> n.b.c
        3
        >>> n['b'].c
        3
        >>> n.b['c']
        3
        >>> n['b']['c']
    
    The same applies to assignment, although this is not recommended. Under the
    hood, this uses `bunch.Bunch` (<http://pypi.python.org/pypi/bunch>).
    
    Requesting Child Nodes
    ----------------------
    
    Many types of node in the Graph API have child nodes accessible through
    further API calls. For example:
    
        >>> g = Graph('access token')
        >>> g.me
        <Graph('https://graph.facebook.com/me') at 0x...>
        >>> g.me()  # User
        Node(...)
        >>> g.me.feed
        <Graph('https://graph.facebook.com/me/feed) at 0x...>
        >>> g.me.feed()  # News Feed for current user
        Node(...)
    
    `Node` makes it easier to access these child nodes using dynamic attribute
    handling:
    
        >>> me = g.me()
        >>> me.feed
        <Graph('https://graph.facebook.com/me/feed') at 0x...>
    
    Accessing a non-existent attribute or item will return a new `Graph`
    pointing to the child node, which you can then retrieve (as a `Node`) by
    calling directly.
    
    Because `Node` uses dynamic attribute handling, accessing non-existent
    attributes will still return a `Graph`. This can sometimes seem like more of
    a bug than a feature. You’ll have to check for the presence of a key first,
    to make sure what you're trying to access actually exists:
    
        def user_location(user_id):
            user = graph[user_id]()
            if 'location' in user:
                return user.location
            return False
    
    """
    
    @classmethod
    def _new(cls, api, data):
        
        """
        Create a new `Node` from a `Graph` and a JSON-decoded object.
        
        If the object is not a dictionary, it will be returned as-is.
        """
        
        if isinstance(data, dict):
            return cls(api, bunch.bunchify(data))
        return data
    
    def __init__(self, api, data):
        super(Node, self).__init__(data)
        object.__setattr__(self, '_api', api)
    
    def __repr__(self):
        return 'Node(%r,\n%s)' % (
            self._api,
            indent(pprint.pformat(bunch.unbunchify(self)), prefix='     '))
    
    def __getitem__(self, item):
        try:
            return bunch.Bunch.__getitem__(self, item)
        except KeyError:
            return self._api[item]
    
    def __getattr__(self, attr):
        try:
            return bunch.Bunch.__getattr__(self, attr)
        except AttributeError:
            return self._api[attr]
    
    @property
    def next_page(self):
        """Shortcut for a `Graph` pointing to the next page."""
        
        return self._api.copy(url=URLObject.parse(self.paging.next))
    
    @property
    def previous_page(self):
        """Shortcut for a `Graph` pointing to the previous page."""
        
        return self._api.copy(url=URLObject.parse(self.paging.next))


def indent(string, prefix='    '):
    """Indent each line of a string with a prefix (default is 4 spaces)."""
    
    return ''.join(prefix + line for line in string.splitlines(True))
