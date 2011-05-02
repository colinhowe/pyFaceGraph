# -*- coding: utf-8 -*-

"""Helpers for building OAuth 2.0-enabled Facebook canvas apps."""


import base64

import simplejson as json

import signature


def b64url_decode(encoded):
    """Decode a string encoded in URL-safe base64 without padding."""
    
    # The padding should round the length of the string up to a multiple of 4.
    padding_fixed = encoded + (((4 - (len(encoded) % 4)) % 4) * '=')
    return base64.urlsafe_b64decode(str(padding_fixed))


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
