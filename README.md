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
    >>> g = Graph(ACCESS_TOKEN) #  Access token is optional.
    >>> g
    <Graph('https://graph.facebook.com/') at 0x...>


### Addressing Nodes

Each `Graph` contains an access token and a URL. The graph you just created
will have a URL of 'https://graph.facebook.com/' by default (this is defined as
the class attribute `Graph.API_ROOT`). 

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


## Canvas Applications

Facebook is rolling out support for OAuth 2.0 in canvas applications with the
new `signed_request` parameter; you can read about it [here][signed_request].

  [signed_request]: http://developers.facebook.com/docs/authentication/canvas

pyFaceGraph comes with a simple function for verifying and decoding this
parameter:

    >>> from facegraph import decode_signed_request, InvalidSignature
    
    >>> decode_signed_request(APP_SECRET, GET['signed_request'])
    {'0': 'payload', 'algorithm': 'HMAC-SHA256'}
    
    >>> decode_signed_request('wrong-secret', GET['signed_request'])
    Traceback (most recent call last):
        ...
    InvalidSignature



### OAuth

pyFaceGraph defines two abstract class-based views (using [django-clsview][])
and a mixin; these help your app obtain OAuth 2.0 access tokens to access the
Graph API on behalf of a Facebook user.

  [django-clsview]: http://github.com/zacharyvoase/django-clsview

*   `FacebookOAuthView`: Defines some common methods useful to all
    Facebook-related CBVs. Should be used as an inherited ‘mixin’, i.e.:
    
        class Callback(CallbackView, FacebookOAuthView):
            pass
    
    Examples of methods implemented here are `redirect_uri()` (which must be the
    same for both the authorize and callback views), `client_id()` and
    `client_secret()` and `fetch_url()`

*   `AuthorizeView`: Acts solely to redirect users to Facebook for
    authorization. You can override `authorize_url()` to change the URL which
    the user is redirected to. `scope()` and `display()` are two shortcuts for
    the Facebook-specific parameters, which you might need to alter for your
    requirements.

*   `CallbackView`: The view the user is redirected back to from Facebook, upon
    successful authorization. It’s up to you to write the body of this (by
    defining `__call__()`), but you can call `get_access_token()` to fetch the
    access token. Suggestions include saving the access token to the database,
    or storing it in `request.session`.

See the source of [facegraph.django.views][fdv] for the ultimate reference guide
to these views.

  [fdv]: http://github.com/iplatform/pyFaceGraph/blob/master/src/facegraph/django/views.py


#### Example

Take a look at the example project in `test/graphdevtools`, which shows how to
construct an app that interfaces with Facebook (and provides a dashboard for
generating access tokens with varying permissions). You’ll need to create
`local_settings.py` in that directory and define `SECRET_KEY`,
`FACEBOOK_CLIENT_ID` and `FACEBOOK_CLIENT_SECRET` (for the latter two you need
to register a Facebook application).


### Middleware

The provided `FacebookGraphMiddleware` will attach a `facegraph.Graph` instance
to each request, accessible as `request.graph`. You will need to subclass this
middleware to define your own method of fetching the access token. For example:

    ## myapp/middleware.py:
    
    from facegraph.django.middleware import FacebookGraphMiddleware
    
    class GraphMiddleware(FacebookGraphMiddleware):
        def access_token(self, request):
            return request.session.get('access_token')
    
    ## settings.py:
    
    MIDDLEWARE_CLASSES = (
      # ... 
      'myapp.middleware.GraphMiddleware',
      # ...
    )

Note that this will still attach a `Graph` even if the access token is `None`.
To check for authentication, just use `if request.graph.access_token:` in your
view code.

There is also a piece of middleware for canvas applications:
`FacebookCanvasMiddleware` will verify and decode Facebook’s new
`signed_request` parameter for each request, and attach the value as
`request.fbrequest`. By default, `settings.FACEBOOK_APP_SECRET` will be used as
the application secret for signature verification, but you can subclass the
middleware and override the `app_secret()` method to modify this behavior:

    ## myapp/middleware.py:
    
    from django.conf import settings
    from facegraph.django.middleware import FacebookCanvasMiddleware
    
    class CanvasMiddleware(FacebookCanvasMiddleware):
        def app_secret(self, request):
            return settings.MY_FACEBOOK_APP_SECRET
    
    ## settings.py:
    
    MIDDLEWARE_CLASSES = (
      # ... 
      'myapp.middleware.CanvasMiddleware',
      # ...
    )

Finally, `FacebookCanvasGraphMiddleware` is a subclass of
`FacebookGraphMiddleware` which will use the signed request as the source of the
access token; no subclassing is necessary, just place it *after*
`CanvasMiddleware` in `MIDDLEWARE_CLASSES`:

    MIDDLEWARE_CLASSES = (
      # ... 
      'myapp.middleware.CanvasMiddleware',
      'facegraph.django.middleware.FacebookCanvasGraphMiddleware',
      # ...
    )


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
