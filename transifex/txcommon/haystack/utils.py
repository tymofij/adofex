import re, operator
from django.conf import settings

from haystack import connections
from haystack.backends.solr_backend import SolrSearchBackend
from haystack.constants import DEFAULT_ALIAS
from haystack.inputs import Raw
from haystack.query import SQ

from transifex.txcommon.log import logger

def support_fulltext_search(using=DEFAULT_ALIAS):
    """
    Method to check whether django-haystack backend used supports fulltext 
    search or not.
    """

    if isinstance(connections[using].get_backend(), SolrSearchBackend):
        return True
    return False

def fulltext_project_search_filter(string):
    """
    Take a string and return a filter to be used on the SearchQuerySet.

    It splits string/phrases into words and search them individually with
    the operator OR using different boost values for 3 fields: 'name', 
    'description' and 'text'. The 'text' field uses fuzzy match.

    The parameter `string` must be passed through the function
    prepare_solr_query_string() before, to ensure the string don't break the
    query.

    >>> value = "Test <br/> %s"
    >>> fulltext_project_search_filter(prepare_solr_query_string(value))
    <SQ: OR (name__exact=Test^1.2 OR description__exact=Test^1.1 OR text__exact=Test~)>
    """
    if string:
        filters = []
        for w in string.split():
            filters.append(SQ(slug=Raw('%s^1.2' % w)))
            filters.append(SQ(name=Raw('%s^1.2' % w)))
            filters.append(SQ(description=Raw('%s^1.1' % w)))
            filters.append(SQ(text=Raw('"%s~"' % w)))
        return reduce(operator.__or__, filters)

def fulltext_fuzzy_match_filter(string):
    """
    Take a string and return a filter to be used on the SearchQuerySet.

    It splits string/phrases into words and search them individually with
    the operator OR using fuzzy match on each word.

    The parameter `string` must be passed through the function
    prepare_solr_query_string() before, to ensure the string don't break the
    query.

    >>> value = "Test <a href="">link</a> for %s"
    >>> fulltext_fuzzy_match_filter(prepare_solr_query_string(value)):
    <SQ: OR (text__exact=Test~ OR text__exact=link~ OR text__exact=for~)>
    """

    # TODO: Searching in this way might be slow. We should investigate 
    # alternatives for it.
    if string:
        return reduce(operator.__or__, 
            [SQ(text=Raw('"%s~"' % w)) for w in string.split()[:1000]])
    else:
        return SQ(text='""')

def prepare_solr_query_string(value):
    """
    Prepare text, striping special chars, HTML tags, prinf vars and extra 
    spaces to be used on a SOLR query.

    >>> value = "The <a href="">link</a> for %s and %(ops)s are NOT right."
    >>> prepare_solr_query_string(value)
    'The link for and are not right.'
    """
    from haystack.query import SearchQuerySet
    value = clean_tags(value)
    value = clean_printf_vars(value)
    value = clean_especial_chars(value)
    value = clean_extra_spaces(value)
    for word in SearchQuerySet().query.backend.RESERVED_WORDS:
        value = value.replace(word, word.lower())
    return value


def clean_especial_chars(value):
    """
    Remove SOLR special characters.

    Taken from SearchQuerySet().query.backend.RESERVED_CHARACTERS.
    We decided to remove them instead of escaping to improve the searching
    results

    >>> strip_chars('?:";')
    ''
    """
    matches = ['\\', '+', '-', '&', '|', '!', '(', ')', '{', '}', '[', ']', 
        '^', '~', '*', '?', ':', '"', ';']
    for m in matches:
        value = value.replace(m, '')
    return value.strip()


def clean_tags(value):
    """
    Return the given HTML with all tags stripped.

    >>> strip_tags('<a href="">link</a>')
    'link'
    """
    return re.sub(r'<[^>]*?>', '', value) 


def clean_extra_spaces(value):
    """
    Remove consecutive spaces from the given value.

    >>> strip_extra_spaces('foo    bar  baz')
    'foo bar baz'
    """
    p = re.compile(r'\s+')
    return p.sub(' ', value)


def clean_printf_vars(value):
    """
    Remove printf vars from the given value.

    >>> strip_printf_vars('foo %s bar $(ops)s')
    'foo  bar '
    """
    printf_pattern = re.compile('%((?:(?P<ord>\d+)\$|\((?P<key>\w+)\))'\
        '?(?P<fullvar>[+#-]*(?:\d+)?(?:\.\d+)?(hh\|h\|l\|ll)?(?P<type>[\w%])))')

    matches = re.finditer(printf_pattern, value)
    for m in matches:
        value = value.replace(m.group(0), '' )

    return value
