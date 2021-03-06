# -*- coding: utf-8 -*-

"""
feedjack
Gustavo Picón
fjlib.py
"""

from django.conf import settings
from django.db import connection
from django.db.models import Min
from django.core.paginator import Paginator, InvalidPage
from django.http import Http404
from django.utils.encoding import smart_unicode

from feedjack import models
from feedjack import fjcache
from datetime import datetime, timedelta
from time import strftime
import re


# this is taken from django, it was removed in r8191
class ObjectPaginator(Paginator):
    """
    Legacy ObjectPaginator class, for backwards compatibility.

    Note that each method on this class that takes page_number expects a
    zero-based page number, whereas the new API (Paginator/Page) uses one-based
    page numbers.
    """
    def __init__(self, query_set, num_per_page, orphans=0):
        Paginator.__init__(self, query_set, num_per_page, orphans)
        import warnings
        warnings.warn("The ObjectPaginator is deprecated. Use django.core.paginator.Paginator instead.", DeprecationWarning)

        # Keep these attributes around for backwards compatibility.
        self.query_set = query_set
        self.num_per_page = num_per_page
        self._hits = self._pages = None

    def validate_page_number(self, page_number):
        try:
            page_number = int(page_number) + 1
        except ValueError:
            raise PageNotAnInteger
        return self.validate_number(page_number)

    def get_page(self, page_number):
        try:
            page_number = int(page_number) + 1
        except ValueError:
            raise PageNotAnInteger
        return self.page(page_number).object_list

    def has_next_page(self, page_number):
        return page_number < self.pages - 1

    def has_previous_page(self, page_number):
        return page_number > 0

    def first_on_page(self, page_number):
        """
        Returns the 1-based index of the first object on the given page,
        relative to total objects found (hits).
        """
        page_number = self.validate_page_number(page_number)
        return (self.num_per_page * (page_number - 1)) + 1

    def last_on_page(self, page_number):
        """
        Returns the 1-based index of the last object on the given page,
        relative to total objects found (hits).
        """
        page_number = self.validate_page_number(page_number)
        if page_number == self.num_pages:
            return self.count
        return page_number * self.num_per_page

    # The old API called it "hits" instead of "count".
    hits = Paginator.count

    # The old API called it "pages" instead of "num_pages".
    pages = Paginator.num_pages


def sitefeeds(siteobj):
    """ Returns the active feeds of a site.
    """
    return siteobj.subscriber_set.filter(is_active=True).select_related()
    #return [subscriber['feed'] \
    #  for subscriber \
    #  in siteobj.subscriber_set.filter(is_active=True).values('feed')]

def getquery(query):
    """ Performs a query and get the results.
    """
    try:
        conn = connection.cursor()
        conn.execute(query)
        data = conn.fetchall()
        conn.close()
    except:
        data = []
    return data

def get_extra_content(site, sfeeds_ids, ctx):
    """ Returns extra data useful to the templates.
    """

    # get the subscribers' feeds
    if sfeeds_ids:
        basefeeds = models.Feed.objects.filter(id__in=sfeeds_ids)
        try:
            ctx['feeds'] = basefeeds.order_by('name').select_related()
        except:
            ctx['feeds'] = []

        # get the last_checked time
        try:
            ctx['last_modified'] = basefeeds.filter(\
              last_checked__isnull=False).order_by(\
              '-last_checked').select_related()[0].last_checked

        except:
            ctx['last_modified'] = '??'
    else:
        ctx['feeds'] = []
        ctx['last_modified'] = '??'
    ctx['site'] = site
    ctx['media_url'] = '%s/feedjack/%s' % (settings.MEDIA_URL, site.template)

def get_posts_tags(object_list, sfeeds_obj, subscription_id, tag_name):
    """ Adds a qtags property in every post object in a page.
    
    Use "qtags" instead of "tags" in templates to avoid innecesary DB hits.
    """
    tagd = {}
    subscription_obj = None
    tag_obj = None
    tags = models.Tag.objects.extra(\
      select={'post_id':'%s.%s' % (\
        connection.ops.quote_name('feedjack_post_tags'), \
        connection.ops.quote_name('post_id'))}, \
      tables=['feedjack_post_tags'], \
      where=[\
        '%s.%s=%s.%s' % (\
          connection.ops.quote_name('feedjack_tag'), \
          connection.ops.quote_name('id'), \
          connection.ops.quote_name('feedjack_post_tags'), \
          connection.ops.quote_name('tag_id')), \
        '%s.%s IN (%s)' % (\
          connection.ops.quote_name('feedjack_post_tags'), \
          connection.ops.quote_name('post_id'), \
          ', '.join([str(post.id) for post in object_list]))])
    for tag in tags:
        if tag.post_id not in tagd:
            tagd[tag.post_id] = []
        tagd[tag.post_id].append(tag)
        if tag_name and tag.name == tag_name:
            tag_obj = tag
    subd = {}
    for sub in sfeeds_obj:
        subd[sub.feed.id] = sub
    for post in object_list:
        if post.id in tagd:
            post.qtags = tagd[post.id]
        else:
            post.qtags = []
        post.subscriber = subd[post.feed.id]
        # TODO: subscription_id should be a slug specific for the subscription
        # of the feed at one site, which is resolved to a global feed for the content
        # urls, filter, etc. should be specific to the subscription, not to the feed
        if not subscription_id is None and int(subscription_id) == post.feed.id:
            subscription_obj = post.subscriber
    return subscription_obj, tag_obj

def getcurrentsite(http_post, path_info, query_string):
    """ Returns the site id and the page cache key based on the request.
    """
    url = u'http://%s/%s' % (smart_unicode(http_post.rstrip('/')), \
      smart_unicode(path_info.lstrip('/')))
    pagecachekey = '%s?%s' % (smart_unicode(path_info), \
      smart_unicode(query_string))
    hostdict = fjcache.hostcache_get()

    if not hostdict:
        hostdict = {}
    if url not in hostdict:
        default, ret = None, None
        for site in models.Site.objects.all():
            if url.startswith(site.url):
                ret = site
                break
            if not default or site.default_site:
                default = site
        if not ret:
            if default:
                ret = default
            else:
                # Somebody is requesting something, but the user didn't create
                # a site yet. Creating a default one...
                ret = models.Site(name='Default Feedjack Site/Planet', \
                  url='www.feedjack.org', \
                  title='Feedjack Site Title', \
                  description='Feedjack Site Description. ' \
                    'Please change this in the admin interface.')
                ret.save()
        hostdict[url] = ret.id
        fjcache.hostcache_set(hostdict)

    return hostdict[url], pagecachekey

def get_paginator(site, sfeeds_ids, page=0, tag=None, subscription=None, group=None, newer=None, asc=False):
    """ Returns a paginator object and a requested page from it.
    """

    if tag:
        try:
            localposts = models.Tag.objects.get(name=tag).post_set.filter(\
              feed__in=sfeeds_ids)
        except:
            raise Http404
    else:
        localposts = models.Post.objects.filter(feed__in=sfeeds_ids)

    if not subscription is None:
        try:
            # TODO: later subscription will be no feed, 
            # but a Subscription object
            localposts = localposts.filter(feed=subscription)
        except:
            raise Http404
    if group:
        group=int(group)
        try:
            if group==0:
                localposts = localposts.filter(feed__subscriber__group__isnull=True)
            else:
                localposts = localposts.filter(feed__subscriber__group__id=group)
        except Exception, e:
            print e
            raise Http404
    if newer:
        named={
        'yesterday': (datetime.today()-timedelta(1)).strftime("%Y-%m-%d"),
        'last_week': (datetime.today()-timedelta(7)).strftime("%Y-%m-%d"),
        '10dayago':  (datetime.today()-timedelta(10)).strftime("%Y-%m-%d"),
        '30daysago': (datetime.today()-timedelta(30)).strftime("%Y-%m-%d"),
        }
        if newer in named:
            newer=named[newer]
        localposts = localposts.filter(date_modified__gt=newer)

    if site.order_posts_by == 2:
        if asc:
            localposts = localposts.order_by('date_created', 'date_modified')
        else:
            localposts = localposts.order_by('-date_created', '-date_modified')
    else:
        if asc:
            localposts = localposts.order_by('date_modified')
        else:
            localposts = localposts.order_by('-date_modified')

    paginator = ObjectPaginator(localposts.select_related(), \
      site.posts_per_page)
    try:
        object_list = paginator.get_page(page)
    except InvalidPage:
        if page == 0:
            object_list = []
        else:
            raise Http404
    return (paginator, object_list)

def page_context(request, site, tag=None, subscription_id=None, group_id=None, newer=None, asc=None, sfeeds=None):
    """ Returns the context dictionary for a page view.
    """
    sfeeds_obj, sfeeds_ids = sfeeds
    try:
        page = int(request.GET.get('page', 0))
    except ValueError:
        page = 0
    paginator, object_list = get_paginator(site, sfeeds_ids, \
      page=page, tag=tag, subscription=subscription_id, newer=newer, asc=asc, group=group_id)
    if object_list:
        # This will hit the DB once per page instead of once for every post in
        # a page. To take advantage of this the template designer must call
        # the qtags property in every item, instead of the default tags
        # property.
        subscription_obj, tag_obj = get_posts_tags(object_list, sfeeds_obj, \
          subscription_id, tag)
    else:
        subscription_obj, tag_obj = None, None
    last_checked = sfeeds_obj.aggregate(last_checked=Min("feed__last_checked"))['last_checked']
    ctx = {
        'object_list': object_list,
        'is_paginated': paginator.pages > 1,
        'results_per_page': site.posts_per_page,
        'has_next': paginator.has_next_page(page),
        'has_previous': paginator.has_previous_page(page),
        'page': page + 1,
        'next': page + 1,
        'previous': page - 1,
        'pages': paginator.pages,
        'hits' : paginator.hits,
        'request': request,
        'now': last_checked.strftime("%Y-%m-%d %H:%M") if last_checked else None,
    }
    get_extra_content(site, sfeeds_ids, ctx)
    from feedjack import fjcloud
    ctx['tagcloud'] = fjcloud.getcloud(site, subscription_id)
    ctx['subscription_id'] = subscription_id 
    ctx['subscription'] = subscription_obj
    ctx['tag'] = tag_obj
    #ctx['subscribers'] = sfeeds_obj.filter(group__isnull=True)
    groups=set()
    for feed in sfeeds_obj:
        groups.add(feed.group)
    ctx['subscriber_groups'] = list(groups)
    ctx['subscriber_groups'] += [{'name': 'ungrouped', 'subscriber_set': sfeeds_obj.filter(group__isnull=True), 'id': 0}]
    return ctx


#~
