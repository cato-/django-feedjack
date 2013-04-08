# -*- coding: utf-8 -*-

"""
feedjack
Gustavo Picón
urls.py
"""

from django.conf.urls import patterns, url
from django.views.generic.base import RedirectView

from feedjack import views
from feedjack import newviews, forms

urlpatterns = patterns('',
    url(r'^rss20.xml$', RedirectView.as_view(url='/feed/rss/')),
    url(r'^feed/$', RedirectView.as_view(url='/feed/atom/')),
    url(r'^feed/rss/$', views.rssfeed, name="feed-rss"),
    url(r'^feed/atom/$', views.atomfeed),

    url(r'^feed/subscription/(?P<subscription>\d+)/tag/(?P<tag>.*)/$', RedirectView.as_view(url='/feed/atom/subscription/%(subscription)s/tag/%(tag)s/')),
    url(r'^feed/subscription/(?P<subscription>\d+)/$', RedirectView.as_view(url='/feed/atom/subscription/%(subscription)s/')),
    url(r'^feed/tag/(?P<tag>.*)/$', RedirectView.as_view(url='/feed/atom/tag/%(tag)s/')),

    url(r'^feed/atom/subscription/(?P<subscription>\d+)/tag/(?P<tag>.*)/$', views.atomfeed),
    url(r'^feed/atom/subscription/(?P<subscription>\d+)/$', views.atomfeed),
    url(r'^feed/atom/tag/(?P<tag>.*)/$', views.atomfeed),
    url(r'^feed/rss/subscription/(?P<subscription>\d+)/tag/(?P<tag>.*)/$', views.rssfeed),
    url(r'^feed/rss/subscription/(?P<subscription>\d+)/$', views.rssfeed),
    url(r'^feed/rss/tag/(?P<tag>.*)/$', views.rssfeed),

    url(r'^settings/feed/new/$', newviews.CreateSubscriber.as_view(), name="settings-feedcreate"),
    url(r'^settings/feed/$', newviews.SubscriberList.as_view(), name="settings-feedlist"),
    url(r'^settings/import/opml/$', newviews.OPMLImport.as_view(form_list = [forms.OPMLUploadForm, forms.OPMLEntrySet]), name="settings-import-opml"),

    url(r'^posts/$', newviews.PostView.as_view(), name="post-all"),

    url(r'^subscription/(?P<subscription>\d+)/tag/(?P<tag>.*)/$', views.mainview),
    url(r'^subscription/(?P<subscription>\d+)/$', views.mainview),
    url(r'^tag/(?P<tag>.*)/$', views.mainview, name="post-tag"),

    url(r'^group/(?P<group>\d+)/$', views.mainview),
    url(r'^since/(?P<newer>([0-9]{4,4}-[0-9]{2,2}-[0-9]{2,2}(| [0-9]{2,2}:[0-9]{2,2})|yesterday|last_week|10daysago|30daysago))(?P<asc>(|/asc))/$', views.mainview),

    url(r'^opml/$', views.opml),
    url(r'^foaf/$', views.foaf),
    url(r'^feedtitle/$', views.feedtitle),
    url(r'^$', views.mainview, name="landing"),

)

#~
