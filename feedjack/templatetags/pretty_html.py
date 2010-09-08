from django import template
from django.template.defaultfilters import *
from BeautifulSoup import BeautifulSoup as soup

register=template.Library()

@register.filter
@stringfilter
def prettyhtml(value, autoescape=None):
    value=str(soup(value))
    if autoescape and not isinstance(value, SafeData):
        from django.utils.html import escape
        value = escape(value)
    return mark_safe(value)
