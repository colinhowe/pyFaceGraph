#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
import os
import re

from distribute_setup import use_setuptools; use_setuptools()
from setuptools import setup, find_packages


rel_file = lambda *args: os.path.join(os.path.dirname(os.path.abspath(__file__)), *args)
cleanup = lambda lines: filter(None, map(lambda s: s.strip(), lines))

def read_from(filename):
    fp = open(filename)
    try:
        return fp.read()
    finally:
        fp.close()

def get_version():
    data = read_from(rel_file('src', 'facegraph', '__init__.py'))
    return re.search(r"__version__ = '([^']+)'", data).group(1)

def get_requirements():
    return cleanup(read_from(rel_file('REQUIREMENTS')).splitlines())

def get_extra_requirements():
    extras_require = {}
    for req_filename in glob.glob(rel_file('REQUIREMENTS.*')):
        group = os.path.basename(req_filename).split('.', 1)[1]
        extras_require[group] = cleanup(read_from(req_filename).splitlines())
    return extras_require


setup(
    name             = 'pyfacegraph',
    version          = get_version(),
    author           = "iPlatform Ltd",
    author_email     = "opensource@theiplatform.com",
    url              = 'http://github.com/iplatform/pyFaceGraph',
    description      = "A client library for the Facebook Graph API.",
    packages         = find_packages(where='src'),
    package_dir      = {'': 'src'},
    install_requires = get_requirements(),
    extras_require   = get_extra_requirements(),
)
