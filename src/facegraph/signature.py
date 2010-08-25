# -*- coding: utf-8 -*-

"""Utilities for dealing with signing and signature verification."""

import hashlib
import hmac


class InvalidSignature(Exception):
    """The signature did not verify against the key and payload."""
    pass


class UnknownSignatureAlgorithm(Exception):
    """The signature algorithm was not recognized."""
    pass


def secure_string_compare(string1, string2):
    """Determine the equality of two strings in `O(len(s))` time."""
    
    # I consider this secure, since the timing doesn't give away information on
    # the *degree* of difference between the two strings. Besides, signatures
    # are supposed to be a fixed length anyway. If they 'find out' we're looking
    # for 256-bit sigs it doesn't constitute a security breach.
    if len(string1) != len(string2):
        return False
    
    # This would be so much faster in C. I don't know why Python doesn't come
    # with a native function for doing exactly this.
    result = True
    for i in xrange(len(string1)):
        result &= string1[i] == string2[i]
    return result


def verify_signature(key, signature, payload, algorithm="HMAC-SHA256"):
    """Verify a signature, given the key and payload."""
    
    if algorithm == "HMAC-SHA256":
        return secure_string_compare(
            signature,
            hmac.HMAC(key, msg=payload, digestmod=hashlib.sha256).digest())
    elif algorithm == "HMAC-SHA1":
        return secure_string_compare(
            signature,
            hmac.HMAC(key, msg=payload, digestmod=hashlib.sha1).digest())
    else:
        raise UnknownSignatureAlgorithm
