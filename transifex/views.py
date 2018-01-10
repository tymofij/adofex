from django.conf import settings
from django.template import Context, loader

def server_error(request, template_name='500.html'):
    """Always include STATIC_URL into the 500 error"""
    from django.http import HttpResponseServerError
    t = loader.get_template(template_name)
    return HttpResponseServerError(t.render(Context({
        'STATIC_URL': settings.STATIC_URL})))

