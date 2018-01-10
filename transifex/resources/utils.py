# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.cache import cache
from django.utils.hashcompat import md5_constructor
from django.utils.http import urlquote


def invalidate_template_cache(fragment_name, *variables):
    """
    This function invalidates a template cache named `fragment_name` and with
    variables which are included in *variables. For example:

    {% cache 500 project_details project.slug %}
        ...
    {% endcache %}

    We invalidate this by calling:
     -  invalidate_template_cache("project_details", project.slug)
    """
    for lang,code in settings.LANGUAGES:
        cur_vars = list(variables)
        cur_vars.append(unicode(lang))
        args = md5_constructor(u':'.join([urlquote(var) for var in cur_vars]))
        cache_key = 'template.cache.%s.%s' % (fragment_name, args.hexdigest())
        cache.delete(cache_key)
