# -*- coding: utf-8 -*-

"""Helpers for building OAuth 2.0-enabled Facebook canvas apps."""


import base64

import simplejson as json

import signature


def b64url_encode(data):
    return base64.urlsafe_b64encode(data).rstrip('=')
        
def b64url_decode(encoded):
    data = data.encode(u'ascii')
    data += '=' * (4 - (len(data) % 4))
    return base64.urlsafe_b64decode(data)


def decode_signed_request(app_secret, signed_request):
    
    """
    Decode and verify an OAuth 2.0 `signed_request` parameter.
    
        >>> print decode_signed_request('secret',
        ...     'vlXgu64BQGFSQrY0ZcJBZASMvYvTHu9GQ0YM9rjPSso.'
        ...     'eyJhbGdvcml0aG0iOiJITUFDLVNIQTI1NiIsIjAiOiJwYXlsb2FkIn0')
        {'0': 'payload', 'algorithm': 'HMAC-SHA256'}
        
        >>> print decode_signed_request('wrong-secret',
        ...     'vlXgu64BQGFSQrY0ZcJBZASMvYvTHu9GQ0YM9rjPSso.'
        ...     'eyJhbGdvcml0aG0iOiJITUFDLVNIQTI1NiIsIjAiOiJwYXlsb2FkIn0')
        Traceback (most recent call last):
           ...
        InvalidSignature
    
    """
    
    sig, payload = signed_request.split('.', 1)
    sig = b64url_decode(sig)
    value = json.loads(b64url_decode(payload))
    
    if not signature.verify_signature(app_secret, sig, payload,
                                      algorithm=value.get("algorithm", "HMAC-SHA256")):
        raise signature.InvalidSignature
    return value
