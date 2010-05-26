# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.template import RequestContext
from facegraph.django.views import *


SCOPES = {
    'basic': (
        'email',
        'read_friendlists',
        'read_insights',
        'read_requests',
        'read_stream',
    ),
    
    'publish': (
        'create_event',
        'offline_access',
        'publish_stream',
        'rsvp_event',
        'sms',
    ),
    
    'user_friend': (
        'about_me',
        'activities',
        'birthday',
        'education_history',
        'events',
        'groups',
        'hometown',
        'interests',
        'likes',
        'location',
        'notes',
        'online_presence',
        'photo_video_tags',
        'photos',
        'relationships',
        'religion_politics',
        'status',
        'videos',
        'website',
        'work_history',
    ),
}


FLAT_SCOPES = set()
FLAT_SCOPES.update(SCOPES['basic'])
FLAT_SCOPES.update(SCOPES['publish'])
for uf_scope in SCOPES['user_friend']:
    FLAT_SCOPES.add('user_' + uf_scope)
    FLAT_SCOPES.add('friends_' + uf_scope)


def index(request):
    return render_to_response('graphdevtools/index.html', {
        'scopes': SCOPES,
        'access_token': request.session.get('access_token')
    }, context_instance=RequestContext(request))


class Authorize(AuthorizeView, FacebookOAuthView):

    def scope(self):
        return list(FLAT_SCOPES.intersection(self.request.POST))


class Callback(CallbackView, FacebookOAuthView):

    def __call__(self):
        access_token = self.get_access_token()
        self.request.session['access_token'] = access_token
        self.request.session.save()
        return redirect('/')


