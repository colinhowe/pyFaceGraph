#from eventlet.green import urllib2
#from eventlet.green import httplib

import socket
import simplejson
from urllib import urlencode, unquote
from simplejson.decoder import JSONDecodeError

FB_READ_TIMEOUT = 180

class Api:
    
    def __init__(self, access_token=None, request=None, cookie=None, app_id=None, stack=None,
                       err_handler=None, timeout=FB_READ_TIMEOUT, urllib2=None, httplib=None,
                       retries=5):
        
        self.uid = None
        self.access_token = access_token
        self.stack = stack if stack else []
        self.cookie = cookie
        self.err_handler = err_handler
        self.retries = retries
        
        if urllib2 is None:
            import urllib2
        self.urllib2 = urllib2
        if httplib is None:
            import httplib
        self.httplib = httplib
        self.timeout = timeout

        socket.setdefaulttimeout(self.timeout)
        
        if self.cookie:
            self.load_cookie()
        elif request:
            self.check_cookie(request, app_id)

    def __sentry__(self):
        return u'FB(method: %s, access_token: %s)' % (self.__method(), self.access_token)

    def __repr__(self):
        return '<FB(%r) at 0x%x>' % (self.__method(), id(self))
    
    def __method(self):
        return u".".join(self.stack)
    
    def __getitem__(self, name):
        '''
        This method returns a new FB and allows us to chain attributes, e.g. fb.stream.publish
        A stack of attributes is maintained so that we can call the correct method later
        '''
        s = []
        s.extend(self.stack)
        s.append(name)
        return self.__class__(stack=s, access_token=self.access_token, cookie=self.cookie, err_handler=self.err_handler,
                              timeout=self.timeout, retries=self.retries, urllib2=self.urllib2, httplib=self.httplib)
    
    def __getattr__(self, name):
        '''
        We trigger __getitem__ here so that both self.method.name and self['method']['name'] work
        '''
        return self[name]
    
    def __call__(self, _retries=None, *args, **kwargs):
        '''
        Executes an old REST api method using the stored method stack
        '''
        _retries = _retries or self.retries
        
        if len(self.stack)>0:
            kwargs.update({"format": "JSON"})
            method = self.__method()
            # Custom overrides
            if method == "photos.upload":
                return self.__photo_upload(**kwargs)            
            
            # UTF8
            utf8_kwargs = {}
            for (k,v) in kwargs.iteritems():
                try:
                    v = v.encode('UTF-8')
                except AttributeError: pass
                utf8_kwargs[k] = v
            
            url = "https://api.facebook.com/method/%s?" % method
            if self.access_token:
                url += 'access_token=%s&' % self.access_token        
            url += urlencode(utf8_kwargs)
            
            attempt = 0
            while True:
                try:
                    response = self.urllib2.urlopen(url, timeout=self.timeout).read()
                    break
                except self.urllib2.HTTPError, e:
                    response = e.fp.read()
                    break
                except (self.httplib.BadStatusLine, IOError):
                    if attempt < _retries:
                        attempt += 1
                    else:
                        raise

            return self.__process_response(response, params=kwargs)

    def __process_response(self, response, params=None):
        try:
            data = simplejson.loads(response)
        except JSONDecodeError:
            data = response
        try:
            if 'error_code' in data:
                e = ApiException(code=int(data.get('error_code')),
                                 message=data.get('error_msg'),
                                 method=self.__method(), 
                                 params=params,
                                 api=self)
                if self.err_handler:
                    return self.err_handler(e=e)
                else:
                    raise e
                                                
        except TypeError:
            pass
        return data

    def __photo_upload(self, _retries=None, **kwargs):
        _retries = _retries or self.retries
        
        body = []
        crlf = '\r\n'
        boundary = "conversocialBoundary"
        
        # UTF8
        utf8_kwargs = {}
        for (k,v) in kwargs.iteritems():
            try:
                v = v.encode('UTF-8')
            except AttributeError: pass
            utf8_kwargs[k] = v
        
        # Add args
        utf8_kwargs.update({'access_token': self.access_token})
        for (k,v) in utf8_kwargs.iteritems():
            if k=='photo': continue
            body.append("--"+boundary)
            body.append('Content-Disposition: form-data; name="%s"' % k) 
            body.append('')
            body.append(str(v))
        
        # Add raw image data
        photo = utf8_kwargs.get('photo')
        photo.open()
        data = photo.read()
        photo.close()
        
        body.append("--"+boundary)
        body.append('Content-Disposition: form-data; filename="myfilewhichisgood.png"')
        body.append('Content-Type: image/png')
        body.append('')
        body.append(data)
        
        body.append("--"+boundary+"--")
        body.append('')
        
        body = crlf.join(body)
                
        # Post to server
        r = self.httplib.HTTPSConnection('api.facebook.com', timeout=self.timeout)
        headers = {'Content-Type': 'multipart/form-data; boundary=%s' % boundary,
                   'Content-Length': str(len(body)),
                   'MIME-Version': '1.0'}
        
        r.request('POST', '/method/photos.upload', body, headers)
        
        attempt = 0
        while True:
            try:
                response = r.getresponse().read()
                return self.__process_response(response, params=kwargs)
            except (self.httplib.BadStatusLine, IOError):
                if attempt < _retries:
                    attempt += 1
                else:
                    raise
            finally:
                r.close()            
        
    def check_cookie(self, request, app_id):
        """"
        Parses the fb cookie if present
        """
        cookie = request.COOKIES.get("fbs_%s" % app_id)
        if cookie:
            self.cookie = dict([(v.split("=")[0], unquote(v.split("=")[1])) for v in cookie.split('&')])
            self.load_cookie()

    def load_cookie(self):
        """
        Checks for user FB cookie and sets as instance attributes.
        Contains:
            access_token    OAuth 2.0 access token used by FB for authentication
            uid             Users's Facebook UID
            expires         Expiry date of cookie, will be 0 for constant auth
            secret          Application secret
            sig             Sig parameter
            session_key     Old-style session key, replaced by access_token, deprecated
        """
        if self.cookie:
            for k in self.cookie:
                setattr(self, k, self.cookie.get(k))

    def __fetch(self, url):
        try:
            response = self.urllib2.urlopen(url, timeout=self.timeout)
        except self.urllib2.HTTPError, e:
            response = e.fp
        return simplejson.load(response)
    
    def verify_token(self, tries=1):
        url = "https://graph.facebook.com/me?access_token=%s" % self.access_token
        for n in range(tries):
            data = self.__fetch(url)
            if 'error' in data:
                pass
            else:
                return True
        
    def exists(self, object_id):
        url = "https://graph.facebook.com/%s?access_token=%s" % (object_id, self.access_token)
        data = self.__fetch(url)
        if data:
            return True
        else:
            return False

class ApiException(Exception):
    def __init__(self, code, message, args=None, params=None, api=None, method=None):
        Exception.__init__(self)
        if args is not None:
            self.args = args
        self.message = message
        self.code = code
        self.params = params
        self.api = api
        self.method = method
        
    def __repr__(self):
        return str(self)
    
    def __str__(self):
        str = "%s, Method: %s" % (self.message, self.method)
        if self.params:
            str = "%s, Params: %s" % (str, self.params)
        if self.code:
            str =  "(#%s) %s" % (self.code, str)
        return str