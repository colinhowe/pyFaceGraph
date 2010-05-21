# -*- coding: utf-8 -*-

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
    
        >>> g = Graph(access_token)
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
    
    def __init__(self, access_token, **state):
        self.access_token = access_token
        self.url = self.API_ROOT
        self.__dict__.update(state)
    
    def __repr__(self):
        return '<Graph(%r) at 0x%x>' % (str(self.url), id(self))
    
    def copy(self, **update):
        return type(self)(self.access_token, **update)
    
    def __getitem__(self, item):
        return self.copy(url=(self.url / unicode(item)))
    
    def __getattr__(self, attr):
        return self[attr]
    
    def __or__(self, params):
        return self.copy(url=(self.url | params))
    
    def __call__(self, **params):
        """Read the current URL, and JSON-decode the results."""
        
        params['access_token'] = self.access_token
        conn = urllib2.urlopen(self.url | params)
        try:
            data = json.load(conn)
        finally:
            conn.close()
        
        if isinstance(data, dict):
            return Node(self, bunch.bunchify(data))
        return data
    
    def fields(self, *fields):
        return self | ('fields', ','.join(fields))
    
    def ids(self, *ids):
        return self | ('ids', ','.join(map(str, ids)))
    
    def post(self, **params):
        params['access_token'] = self.access_token
        conn = urllib2.urlopen(self.url, data=urllib.urlencode(params))
        try:
            data = json.load(conn)
        finally:
            conn.close()
        
        if isinstance(data, dict):
            return Node(self, bunch.bunchify(data))
        return data
    
    def delete(self):
        return self.post(method='delete')


class Node(bunch.Bunch):
    
    def __init__(self, api, data):
        super(Node, self).__init__(data)
        object.__setattr__(self, '_api', api)
    
    def __repr__(self):
        return 'Node(%r)' % (dict(self),)
    
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
        return self._api.copy(url=URLObject.parse(self.paging.next))
    
    @property
    def previous_page(self):
        return self._api.copy(url=URLObject.parse(self.paging.next))
