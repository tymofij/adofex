import re
from django import template

register = template.Library()


class RegisterHelp(template.Node):
    """Put a text to the context with var_name as its id."""
    def __init__(self, var_name, nodelist):
        self.nodelist = nodelist
        self.var_name = var_name

    def render(self, context):
        if context.has_key("helptext_ext"):
            helptext_ext = context["helptext_ext"]
            helptext_ext[self.var_name] = self.nodelist.render(context)
        else:
            helptext_ext = { self.var_name : self.nodelist.render(context) }
            context["helptext_ext"] = helptext_ext
        return ''


@register.tag
def register_helptext(parser, token):
    """
    Register an object to be used with print_helptext

    This templatetag is used at the beginning of a template where a help text
    needs to be extending with extra text. CAUTION! It should be used before
    the inclusion tag print_helptext to work properly.

    Example: <% register_helptext "example_id" %>
    """
    # This version uses a regular expression to parse tag contents.
    try:
        # Splitting by None == splitting by spaces.
        tag_name, id_string = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires a single argument" % token.contents.split()[0]
    if not (id_string[0] == id_string[-1] and id_string[0] in ('"', "'")):
        raise template.TemplateSyntaxError, "%r tag's argument should be in quotes" % tag_name
    nodelist = parser.parse(('endregister_helptext',))
    parser.delete_first_token()
    return RegisterHelp(id_string[1:-1], nodelist)


@register.inclusion_tag('extended_helptext.html', takes_context=True)
def print_helptext(context, code_name, icon=None):
    """Put the registered extended helptext in a hidden container.

    The text is presented in a popup, backed by a js script. If a "yes"
    string is given as second argument (you can give any string actually)
    then a help icon with a anchored link is appeared.
    """
    return {
        'extra_helptext': context["helptext_ext"].get(code_name, None),
        'code_name': code_name,
        'icon': icon,
        'STATIC_URL': context.get("STATIC_URL", None),
    }


@register.inclusion_tag('tooltip_helptext.html', takes_context=True)
def tooltip_helptext(context, code_name, helptext, icon=None):
    """Create a tooltip around an element with id code_name

    It gets 3 arguments, an element id, a string of the helptext and an optional
    icon "True" string. The latter adds an icon which is marked with the tooltip.
    """
    return {
        'helptext': helptext,
        'code_name': code_name,
        'icon': icon,
        'STATIC_URL': context.get("STATIC_URL", None),
    }

