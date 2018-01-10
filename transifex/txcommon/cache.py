# -*- coding: utf-8 -*-

"""
Cache-related functionality.
"""

from django.core.cache import cache
from django.conf import settings
from django.template import Context
from django.template.loader import get_template
from django.templatetags.cache import CacheNode
from django.utils.hashcompat import md5_constructor
from django.utils.http import urlquote
from transifex.txcommon.log import logger


def invalidate_template_cache(fragment_name, *variables):
    """This function invalidates a template cache.

    The template cache is named `fragment_name` and the variables are
    included in *variables. For example:

    {% cache 500 project_details project.slug LANGUAGE_CODE%}
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


def update_template_cache(template_name, fragment_names, key_vars, context):
    """Update the template cache with the new data.

    The caches will be invalidated in the order given.
    """
    logger.debug("Invalidating %s in %s" % (fragment_names, template_name))
    t = get_template(template_name)
    nodes = t.nodelist.get_nodes_by_type(CacheNode)
    for f_name in fragment_names:
        for node in nodes:
            if f_name == node.fragment_name:
                set_fragment_content(node, key_vars, context)
                break


def set_fragment_content(node, key_vars, context):
    """Set the rendered content of a template fragment."""
    try:
        for code, lang in settings.LANGUAGES:
            cur_vars = list(key_vars)
            cur_vars.append(unicode(code))
            args = md5_constructor(u':'.join([urlquote(var) for var in cur_vars]))
            cache_key = 'template.cache.%s.%s' % (node.fragment_name, args.hexdigest())
            context['use_l10n'] = True
            context['LANGUAGE_CODE'] = code
            value = node.nodelist.render(context=Context(context))
            cache.set(cache_key, value, settings.CACHE_MIDDLEWARE_SECONDS)
    except Exception, e:
        invalidate_template_cache(node.fragment_name, key_vars.keys())

