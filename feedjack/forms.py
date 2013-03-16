from django.forms import ModelForm, URLField

from feedjack.models import Subscriber
from django.utils.translation import ugettext as _


class SubscriptionAddForm(ModelForm):
    feed_url = URLField(label=_("URL"))
    class Meta:
        model = Subscriber
        fields = ('feed_url', 'name', 'group',)
