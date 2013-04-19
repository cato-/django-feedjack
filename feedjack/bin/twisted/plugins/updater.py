from zope.interface import implements

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker, MultiService

from twisted.application import internet, service
from twisted.python import threadpool
from twisted.internet import reactor, threads

import json
import os
import socket
import sys
import copy

class Options(usage.Options):
    optParameters = [["config", "c", "twisted.json", "The configuration file for this service."]]



class FeedListUpdater(internet.TimerService):
    name = 'feedlistupdater'

    def __init__(self, config):
        self.config = config
        self.step = self.config['feedlist']['step']
        self.call = (self.update_feed_list, [], {})
        self.pool = threadpool.ThreadPool(minthreads=1, maxthreads=1, name="feedlistupdater")
        reactor.callWhenRunning(self.pool.start)
        reactor.addSystemEventTrigger('after', 'shutdown', self.pool.stop)

    def update_feed_list(self):
        d = threads.deferToThreadPool(reactor, self.pool, self.get_feed_list)
        d.addCallback(self.set_feed_list)

    def get_feed_list(self):
        from feedjack.models import Feed
        return list(Feed.objects.values_list('id', 'feed_url'))

    def set_feed_list(self, flist):
        print flist
        self.parent.feeds = flist


class FeedUpdater(internet.TimerService):
    name = 'updater'

    # ID => DelayedCall
    fetchers = {}

    def __init__(self, config):
        self.config = config
        self.step = self.config[self.name]['step']
        self.call = (self.update_feed_list, [], {})
        self.pool = threadpool.ThreadPool(name=self.name)
        reactor.callWhenRunning(self.pool.start)
        reactor.addSystemEventTrigger('after', 'shutdown', self.pool.stop)

    def update_feed(self, id, feed):
        print "about to update %s %s" % (id, feed)
        self.schedule_feed(id, feed, 10)

    def schedule_feed(self, id, feed, seconds=0):
        d = reactor.callLater(seconds, self.update_feed, id, feed)
        self.fetchers[id] = d

    def update_feed_list(self):
        flist = copy.copy(self.parent.feeds)

        # Remove old Feeds
        to_del = []
        for id, dcall in self.fetchers.iteritems():
            if not id in flist:
                if dcall.active():
                    dcall.cancel()
                to_del.append(id)
                print "Canceled Call for %i" % id
        for id in to_del:
            del self.fetchers[id]

        # Add new Feeds
        for id, feedurl in flist:
            if not id in flist:
                print "Added Feed %s %s" % (id, feedurl)
                self.schedule_feed(id, feedurl)


class MyServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "feedupdater"
    description = "Feadme Feed updater"
    options = Options

    def makeService(self, options):
        root = service.MultiService()
        config = json.load(open(options['config']))
        root.config = config

        root.feeds = {}

        os.environ.setdefault('DJANGO_SETTINGS_MODULE', config['django']['settings'])

        feedlist = FeedListUpdater(root.config)
        feedlist.setServiceParent(root)

        updater = FeedUpdater(root.config)
        updater.setServiceParent(root)

        return root

serviceMaker = MyServiceMaker()
