
from django.views.generic.list import ListView
from endless_pagination.views import AjaxListView    


from feedjack.models import Post

class PostView(AjaxListView):
    model = Post
    template_name = "feedjack/post_list.html"
    page_template = "feedjack/post.html"
