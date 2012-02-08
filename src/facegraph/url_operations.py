import urllib
import cgi
import urlparse

def get_path(url):
    scheme, host, path, query, fragment = urlparse.urlsplit(url)
    return path

def get_host(url):
    scheme, host, path, query, fragment = urlparse.urlsplit(url)
    return host

def add_path(url, new_path):
    """Given a url and path, return a new url that combines
    the two.
    """
    scheme, host, path, query, fragment = urlparse.urlsplit(url)
    new_path = new_path.lstrip('/')
    if path.endswith('/'):
        path += new_path
    else:
        path += '/' + new_path
    return urlparse.urlunsplit([scheme, host, path, query, fragment])

def _query_param(key, value):
    """ensure that a query parameter's value is a string
    of bytes in UTF-8 encoding.
    """
    if isinstance(value, unicode):
        pass
    elif isinstance(value, str):
        value = value.decode('utf-8')
    else:
        value = unicode(value)
    return (key, value.encode('utf-8'))

def _make_query_tuples(params):
    if hasattr(params, 'items'):
        return [_query_param(*param) for param in params.items()]
    else:
        return [_query_param(*params)]

def add_query_params(url, params):
    """use the _update_query_params function to set a new query
    string for the url based on params.
    """
    return update_query_params(url, params, update=False)

def update_query_params(url, params, update=True):
    """Given a url and a tuple or dict of parameters, return
    a url that includes the parameters as a properly formatted
    query string.

    If update is True, change any existing values to new values
    given in params.
    """
    scheme, host, path, query, fragment = urlparse.urlsplit(url)

    # cgi.parse_qsl gives back url-decoded byte strings. Leave these as
    # they are: they will be re-urlencoded below
    query_bits = [(k, v) for k, v in cgi.parse_qsl(query)]
    if update:
        query_bits = dict(query_bits)
        query_bits.update(_make_query_tuples(params))
    else:
        query_bits.extend(_make_query_tuples(params))

    query = urllib.urlencode(query_bits)
    return urlparse.urlunsplit([scheme, host, path, query, fragment])

