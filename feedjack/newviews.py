from django.contrib.formtools.wizard.views import SessionWizardView
from django.core.files.storage import FileSystemStorage
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView

from endless_pagination.views import AjaxListView    
import opml

from feedjack.forms import SubscriptionAddForm, OPMLUploadForm, OPMLEntrySet
from feedjack.models import Post, Subscriber, Feed


class PostView(AjaxListView):
    model = Post
    template_name = "feedjack/post_list.html"
    page_template = "feedjack/post.html"


### Views for settings

def get_current_site(request):
    return request.user.feedjackuser.site


def get_or_create_feed(url, name=None):
    # TODO: Implement feed aliasing
    feed, created = Feed.objects.get_or_create(feed_url=url)
    if created:
        feed.name = feed.feed_url if name is None else name
        feed.save()
    return (feed, created)


class CreateSubscriber(CreateView):
    form_class = SubscriptionAddForm
    model = Subscriber

    def get_success_url(self):
        return reverse('settings-feedlist')

    def form_valid(self, form):
        feed, created = get_or_create_feed(form.cleaned_data["feed_url"])
        form.instance.feed = feed
        form.instance.site = get_current_site(self.request)
        return super(CreateSubscriber, self).form_valid(form)

class SubscriberList(ListView):
    model = Subscriber

    def get_queryset(self):
        qs = super(SubscriberList, self).get_queryset()
        return qs.filter(site=get_current_site(self.request))

### OPML import

class OPMLImport(SessionWizardView):

    file_storage = FileSystemStorage()
    template_name = 'feedjack/opml_import.html'

    def done(self, form_list, **kwargs):
        importdata = self.get_cleaned_data_for_step('1')
        feeds = []
        for line in importdata:
            if line['enabled']:
                feed, created = get_or_create_feed(line['feedurl'], line['title'])
                site = get_current_site(self.request)
                subscription = Subscriber.objects.get_or_create(feed=feed, site=site)
                feeds.append({'feed': feed, 'created': created})
        return render_to_response('feedjack/opml_import_done.html', {
            'feeds': feeds,
        })
   
    def get_form_initial(self, step):
        if step == '1':
            src = None
            uploaddata = self.get_cleaned_data_for_step('0')
            if uploaddata['file']:
                fsrc = uploaddata['file']
                str = ""
                for chunk in fsrc.chunks():
                    str += chunk
                ofile = opml.from_string(str)
            else:
                src = uploaddata['url']
                ofile = opml.parse(src)
            initial = []
            for entry in ofile:
                init_entry = {
                    'enabled': True,
                    'title': entry.title,
                    'feedurl': entry.xmlUrl,
                    'wwwurl': entry.htmlUrl,
                }
                initial.append(init_entry)
            return initial
        else:
            return super(OPMLImport, self).get_form_initial(step)
