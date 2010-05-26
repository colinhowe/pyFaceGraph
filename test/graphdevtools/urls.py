# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *


urlpatterns = patterns('',
    url(r'^$', 'graphdevtools.views.index', name='index'),
    url(r'^oauth/authorize/$', 'graphdevtools.views.Authorize', name='oauth-authorize'),
    url(r'^oauth/callback/$', 'graphdevtools.views.Callback', name='oauth-callback'),
)
