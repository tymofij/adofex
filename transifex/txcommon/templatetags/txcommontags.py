# -*- coding: utf-8 -*-
import re
from django import template
from django.conf import settings
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape
from django.utils.translation import ugettext_lazy as _
from django.template import Node, NodeList, TemplateSyntaxError
from actionlog.models import LogEntry
from transifex.projects.models import Project
from transifex import txcommon

register = template.Library()

class ResolverNode(template.Node):
    """
    A small wrapper that adds a convenient resolve method.
    """
    def resolve(self, var, context):
        """Resolves a variable out of context if it's not in quotes"""
        if var is None:
            return var
        if var[0] in ('"', "'") and var[-1] == var[0]:
            return var[1:-1]
        else:
            return template.Variable(var).resolve(context)

    @classmethod
    def next_bit_for(cls, bits, key, if_none=None):
        try:
            return bits[bits.index(key)+1]
        except (ValueError, IndexError):
            return if_none


class LatestProjects(template.Node):

    def __init__(self, number=5):
        self.number = number

    def render(self, context):
        try:
            latest_projects = Project.public.order_by('-created')[:self.number]
        except ValueError:
            latest_projects = None

        context['latest_projects'] = latest_projects
        return ''

class DoGetLatestProjects:

    def __init__(self):
        pass

    def __call__(self, parser, token):
        tokens = token.contents.split()
        if not tokens[1].isdigit():
            raise template.TemplateSyntaxError, (
                "The argument for '%s' must be an integer" % tokens[0])
        return LatestProjects(tokens[1])

register.tag('get_latest_projects', DoGetLatestProjects())


@register.inclusion_tag("common_render_metacount.html")
def render_metacount(list, countable):
    """
    Return meta-style link rendered as superscript to count something.

    For example, with list=['a', 'b'] and countable='boxes' return
    the HTML for "2 boxes".
    """
    count = len(list)
    if count > 1:
        return {'count': count,
                'countable': countable}

@register.inclusion_tag("common_homelink.html")
def homelink(text=_("Home")):
    """Return a link to the homepage."""
    return {'text': text}

@register.simple_tag
def txversion():
    """Return the version of Transifex"""
    return txcommon.version

@register.simple_tag
def txrevision():
    """
    Return the revision of the Transifex repository in case it's running on
    top of a checkout. If it's not, return an empty string.
    """
    return txcommon.revision

@register.simple_tag
def txversion_full():
    """
    Return the full version of Transifex.

    For versions that are not 'final' return the current version of Transifex
    plus the revision of the repository, in case it's running on top of a
    checkout.
    """
    return txcommon.version_full

class CounterNode(ResolverNode):
    """A template node to count how many times it was called."""

    @classmethod
    def handle_token(cls, parser, token):
        bits = token.contents.split()
        tag_name = bits[0]
        kwargs = {
            'initial': cls.next_bit_for(bits, tag_name, 0),
        }
        return cls(**kwargs)

    def __init__(self, initial):
        self.count = 0
        self.initial = initial

    def render(self, context):
        if self.count == 0 and self.initial != 0:
            try:
                initial = int(self.initial)
            except ValueError:
                initial = int(template.resolve_variable(self.initial, context))
        else:
            initial = 0

        self.count += 1 + initial
        return self.count

@register.tag
def counter(parser, token):
    """
    Return a number increasing its counting each time it's called.
    An ``initial`` value can be passed to identify from which number it should
    start counting.

    Syntax::

        {% counter %}
        {% counter 20 %}

    """
    return CounterNode.handle_token(parser, token)


# Forms

@register.inclusion_tag("form_as_table_rows.html", takes_context=True)
def form_as_table_rows(context, form, id=None):
    """
    Create a form using HTML table rows.
    """
    context['form'] = form
    context['id'] = id
    return context


# Email Munger by cootetom
# http://www.djangosnippets.org/snippets/1284/

@register.filter
@stringfilter
def mungify(email, text=None, autoescape=None):
    text = text or email

    if autoescape:
        email = conditional_escape(email)
        text = conditional_escape(text)

    emailArrayContent = ''
    textArrayContent = ''
    r = lambda c: '"' + str(ord(c)) + '",'

    for c in email: emailArrayContent += r(c)
    for c in text: textArrayContent += r(c)

    result = """<script type=\"text/javascript\">
                var _tyjsdf = [%s], _qplmks = [%s];
                document.write('<a href="&#x6d;&#97;&#105;&#x6c;&#000116;&#111;&#x3a;');
                for(_i=0;_i<_tyjsdf.length;_i++){document.write('&#'+_tyjsdf[_i]+';');}
                document.write('">');
                for(_i=0;_i<_qplmks.length;_i++){document.write('&#'+_qplmks[_i]+';');}
                document.write('<\/a>');
                </script>""" % (re.sub(r',$', '', emailArrayContent),
                                re.sub(r',$', '', textArrayContent))

    return mark_safe(result)

mungify.needs_autoescape = True

@register.filter
def sort(value, arg):
    keys = [k.strip() for k in arg.split(',')]
    return txcommon.utils.key_sort(value, *keys)


# Temporary filter
@register.filter
def notice_type_user_filter(noticetype_list):
    """
    Filter a NoticeType list passed by parameter using the NOTICE_TYPES
    dictionary that says which notice types must be shown to the user.

    It is necessary by now until the upstream project have a model change to be
    able to do this filtering from the database.
    """
    from txcommon.notifications import NOTICE_TYPES
    new_list=[]
    for nt in noticetype_list:
        add = True
        for n in NOTICE_TYPES:
            if nt['notice_type'].label == n["label"]:
                if not n["show_to_user"]:
                    add = False
        if add:
            new_list.append(nt)
    return new_list

@register.filter
def in_list(value, arg):
    """Check if a value is present in a list."""
    return value in arg

@register.filter
def getitem(d, key):
  return d.get(key, '')

@register.filter
def get_next(request):
    """Return the next path from the request."""
    try:
        next = request.GET.get('next', '')
        if not next:
            next = request.path
        return next
    except AttributeError:
        return ''

@register.filter
def size_humanize(value):
    """Return a more human readable size number with the appropriate unit type."""
    return txcommon.utils.size_human(value)

@register.filter
def strip_tags(value):
    """Return the value with HTML tags striped."""
    return txcommon.rst.strip_tags(value)

@register.filter
def as_rest_title(value, border=None):
    """
    Return a value as a restructured text header.

    border - Character to be used in the header bottom-border
    """
    return txcommon.rst.as_title(value, border)

class TooltipNode(Node):
    def __init__(self, prefix, id, nodelist):
        self.prefix = prefix
        self.id = id
        self.nodelist = nodelist

    def __repr__(self):
        return "<TooltipNode:%s>" % self.id

    def render(self, context):
        output = self.nodelist.render(context).replace("\"", "\\\"").replace("\n", "") # We need better escaping ofc!
        id = self.id.resolve(context)
        return """<script type=\"text/javascript\">\ntooltip("#%s-%s", "%s");\n</script>""" % (self.prefix, id, output)

class GetSettings(Node):

    def __init__(self, variable_name, context_variable):
        self.variable_name = variable_name
        self.context_variable = context_variable

    def render(self, context):
        try:
            context[self.context_variable] = settings.__getattr__(
                    self.variable_name)
        except AttributeError:
            context[self.context_variable] = False

        return ""

def do_tooltip(parser, token):
    try:
        bits = token.split_contents()
        cmd, prefix, id = bits

    except:
        raise TemplateSyntaxError("%r expects two arguments constant 'prefix' and variable 'id'" %
                                  bits[0])
    nodelist = parser.parse(('endtooltip',))
    parser.delete_first_token()
    prefix = prefix[1:-1] # Strip quotes
    id = parser.compile_filter(id)
    return TooltipNode(prefix, id, nodelist)

register.tag('tooltip', do_tooltip)

def get_settings(parser, token):
    """
    {% settings VARIABLE_NAME as variable_name %}
    """
    bits = token.split_contents()
    if len(bits) == 2:
        variable_name = bits[1]
        context_variable = variable_name
    elif len(bits) == 4 and bits[2] == 'as':
        variable_name = bits[1]
        context_variable = bits[3]
    else:
        raise TemplateSyntaxError("%r expects a single argument or "\
                "two arguments separated by 'as'." % bits[0])
    return GetSettings(variable_name, context_variable)

register.tag('settings', get_settings)
