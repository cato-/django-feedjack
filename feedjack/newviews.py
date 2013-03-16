
from django.core.urlresolvers import reverse
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView

from endless_pagination.views import AjaxListView    


from feedjack.models import Post, Subscriber, Feed
from feedjack.forms import SubscriptionAddForm

class PostView(AjaxListView):
    model = Post
    template_name = "feedjack/post_list.html"
    page_template = "feedjack/post.html"


### Views for settings

def get_current_site(request):
    return request.user.feedjackuser.site

class CreateSubscriber(CreateView):
    form_class = SubscriptionAddForm
    model = Subscriber

    def get_success_url(self):
        return reverse('settings-feedlist')

    def form_valid(self, form):
        feed, created = Feed.objects.get_or_create(feed_url=form.cleaned_data["feed_url"])
        feed.name = feed.feed_url
        feed.save()
        form.instance.feed = feed
        form.instance.site = get_current_site(self.request)
        return super(CreateSubscriber, self).form_valid(form)

class SubscriberList(ListView):
    model = Subscriber

    def get_queryset(self):
        qs = super(SubscriberList, self).get_queryset()
        return qs.filter(site=get_current_site(self.request))
