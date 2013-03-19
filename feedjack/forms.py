from django import forms 

from feedjack.models import Subscriber
from django.utils.translation import ugettext as _
from django.forms.formsets import formset_factory


class SubscriptionAddForm(forms.ModelForm):
    feed_url = forms.URLField(label=_("URL"))
    class Meta:
        model = Subscriber
        fields = ('feed_url', 'name', 'group',)


class OPMLUploadForm(forms.Form):
    file = forms.FileField(required=False, label=_("OPML File"))
    url = forms.URLField(required=False, label=_("URL to OPML File"))
    
    def clean(self):
        res = super(OPMLUploadForm, self).clean()
        if self.cleaned_data['file'] is None and self.cleaned_data['url'] == "":
            raise forms.ValidationError(_('Please upload either a file or specify an URL'))
        return res


class OPMLEntry(forms.Form):
    enabled = forms.BooleanField()
    title = forms.CharField()
    feedurl = forms.URLField()
    wwwurl = forms.URLField()


OPMLEntrySet = formset_factory(OPMLEntry, extra=0)
