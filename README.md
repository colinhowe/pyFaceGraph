# pyFaceGraph

pyFaceGraph is a Python client library for the [Facebook Graph API][api]. It is
being developed and maintained by [iPlatform][].

  [api]: http://developers.facebook.com/docs/api
  [iplatform]: http://theiplatform.com/


## Installation

Via `pip` or `easy_install`:

    pip install pyfacegraph
    easy_install pyfacegraph

You can install an 'edge' version via git:

    git clone 'git://github.com/iplatform/pyFaceGraph.git'
    cd pyFaceGraph
    python setup.py install


## Graph API Tutorial

To begin using the API, create a new `Graph` with an access token:
    
    >>> from facegraph import Graph
    >>> g = Graph(ACCESS_TOKEN)
    >>> g
    <Graph('https://graph.facebook.com/') at 0x...>


### Addressing Nodes

Each `Graph` contains an access token and a URL. The graph you just created
will have a URL of 'https://graph.facebook.com/' by default (this is defined as
the class attribute `Graph.API_ROOT`). The URL is represented as a `URLObject`;
see <http://github.com/zacharyvoase/urlobject> for more information. Remember
that you can treat it exactly as you would a `unicode` string; it just supports
a few more methods to enable easy URL manipulation.

    >>> g.url
    <URLObject(u'https://graph.facebook.com/') at 0x...>
    >>> print g.url
    https://graph.facebook.com/
    >>> unicode(g.url)
    u'https://graph.facebook.com/'

To address child nodes, `Graph` supports dynamic attribute and item lookups:

    >>> g.me
    <Graph('https://graph.facebook.com/me') at 0x...>
    >>> g.me.home
    <Graph('https://graph.facebook.com/me/home') at 0x...>
    >>> g['me']['home']
    <Graph('https://graph.facebook.com/me/home') at 0x...>
    >>> g[123456789]
    <Graph('https://graph.facebook.com/123456789') at 0x...>

Note that a `Graph` instance is rarely modified; these methods all return copies
of the original object. In addition, the API is lazy: HTTP requests will
never be made unless you explicitly make them.


### Retrieving Nodes

You can fetch data by calling a `Graph` instance:

    >>> about_me = g.me()
    >>> about_me
    Node({'about': '...', 'id': '1503223370'})

This returns a `Node` object, which contains the retrieved data. `Node` is
a subclass of `bunch.Bunch` [[pypi](http://pypi.python.org/pypi/bunch)], so you
can access keys using either attribute or item syntax:

    >>> about_me.id
    '1503223370'
    >>> about_me.first_name
    'Zachary'
    >>> about_me.hometown.name
    'London, United Kingdom'
    >>> about_me['hometown']['name']
    'London, United Kingdom'

Accessing non-existent attributes or items will return a `Graph` instance
corresponding to a child node. This `Graph` can then be called normally, to
retrieve the child node it represents:

    >>> 'home' in about_me  # Not present in the data itself
    False
    >>> about_me.home
    <Graph('https://graph.facebook.com/me/home') at 0x...>
    >>> about_me.home()
    Node({'data': [...]})


### Creating, Updating and Deleting Nodes

With the Graph API, node manipulation is done via HTTP POST requests.
`Graph.post()` will POST to the current URL, with varying semantics for each
endpoint:

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

Any keyword arguments passed to `post()` will be added as form data. Consult the
[Facebook API docs][api-ref] for a complete reference on URLs and options.

  [api-ref]: http://developers.facebook.com/docs/reference/api/

Nodes can be deleted by adding `?method=delete` to the URL; the `delete()`
method is a helpful shortcut:

    >>> g[post.id].delete()
    True


## (Un)license

This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or distribute this
software, either in source code form or as a compiled binary, for any purpose,
commercial or non-commercial, and by any means.

In jurisdictions that recognize copyright laws, the author or authors of this
software dedicate any and all copyright interest in the software to the public
domain. We make this dedication for the benefit of the public at large and to
the detriment of our heirs and successors. We intend this dedication to be an
overt act of relinquishment in perpetuity of all present and future rights to
this software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

For more information, please refer to <http://unlicense.org/>
