from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

def index(request):
    """ Dashboard. Redirects user to Projects or My projects page
    """
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse("myprojects"))
    else:
        return HttpResponseRedirect(reverse("project_list"))
