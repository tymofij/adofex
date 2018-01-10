from __future__ import absolute_import
import gc, re
import operator
from django.core.urlresolvers import get_resolver
from django.views.generic.simple import direct_to_template
from django.views.decorators.http import condition
from django.conf import settings
from django.core.cache import cache
from transifex.txcommon.log import logger
from datastores.txredis import TxRedisMapper, redis_exception_handler


STATIC_CACHE_KEY_LAST_MODIFIED = 'tx_static_pages_last_modified'
STATIC_CACHE_KEY_ETAG = 'tx_static_pages_etag'


@redis_exception_handler
def static_etag(*args, **kwargs):
    r = TxRedisMapper()
    return r.get(STATIC_CACHE_KEY_ETAG)


@redis_exception_handler
def static_last_modified(*args, **kwargs):
    r = TxRedisMapper()
    return r.get(STATIC_CACHE_KEY_LAST_MODIFIED)

cached_direct_to_template = condition(
    last_modified_func=static_last_modified, etag_func=static_etag
)(direct_to_template)


def log_skip_transaction_test(msg):
    if not settings.DATABASES['default']['ENGINE'].endswith('postgresql_psycopg2'):
        logger.info(msg)
    return msg

def get_url_pattern(urlname, args=[]):
    """
    Return URL pattern for a URL based on its name.

    args - list of argument names for the URL. Useful to distinguish URL
    patterns identified with the same name.

    >>> get_url_pattern('project_detail')
    u'/projects/p/%(project_slug)s/'

    >>> get_url_pattern('project_detail', args=['project_slug'])
    u'/projects/p/%(project_slug)s/'

    """
    patterns = get_resolver(None).reverse_dict.getlist(urlname)
    if not args:
        return '/%s' % patterns[0][0][0][0]

    for pattern in patterns:
        if pattern[0][0][1] == args:
            return '/%s' % pattern[0][0][0]


def cached_property(func):
    """
    Cached property.

    This function is able to verify if an instance of a property field
    was already created before and, if not, it creates the new one.
    When needed it also is able to delete the cached property field from
    the memory.

    Usage:
    @cached_property
    def trans(self):
        ...

    del(self.trans)

    """
    def _set_cache(self):
        cache_attr = "__%s" % func.__name__
        try:
            return getattr(self, cache_attr)
        except AttributeError:
            value = func(self)
            setattr(self, cache_attr, value)
            return value

    def _del_cache(self):
        cache_attr = "__%s" % func.__name__
        try:
            delattr(self, cache_attr)
        except AttributeError:
            pass

    return property(_set_cache, fdel=_del_cache)


def immutable_property(func):
    """
    Immutable property.

    This function prevents an instance of a property field to be
    altered and/or deleted.

    Usage:
    class Foo(object):
        @immutable_property
        def bar(self):
            return True

    foo=Foo()
    foo.bar = False
    ValueError: 'bar' is immutable and can not be changed

    del(foo.bar)
    ValueError: 'bar' is immutable and can not be deleted

    """
    def _set_attr(self, value):
        raise ValueError("'%s' is immutable and can not be changed"
            % func.__name__)

    def _get_attr(self):
        return func(self)

    def _del_attr(self):
        raise ValueError("'%s' is immutable and can not be deleted"
            % func.__name__)

    return property(fget=_get_attr, fset=_set_attr, fdel=_del_attr)


def key_sort(l, *keys):
    """
    Sort an iterable given an arbitrary number of keys relative to it
    and return the result as a list. When a key starts with '-' the
    sorting is reversed.

    Example: key_sort(people, 'lastname', '-age')
    """
    l = list(l)
    for key in keys:
        #Find out if we want a reversed ordering
        if key.startswith('-'):
            reverse = True
            key = key[1:]
        else:
            reverse = False

        attrs = key.split('.')
        def fun(x):
            # Calculate x.attr1.attr2...
            for attr in attrs:
                x = getattr(x, attr)
            # If the key attribute is a string we lowercase it
            if isinstance(x, basestring):
                x = x.lower()
            return x
        l.sort(key=fun, reverse=reverse)
    return l

def size_human(size):
    """
    Make the size in bytes to a more human readable format.

    This function compares the size value with some thresholds and returns
    a new value with the appropriate suffix (K, M, T, P). The correct input
    is an integer value not a string!!!

    >>> size_human(755745434)
    '721.0M'
    """

    if size:
        _abbrevs = [
        (1<<50L, 'P'),
        (1<<40L, 'T'),
        (1<<30L, 'G'),
        (1<<20L, 'M'),
        (1<<10L, 'k'),
        (1, 'bytes')]

        for factor, suffix in _abbrevs:
            if size > factor:
                break
        if factor == 1:
            return "%d %s" % (size, suffix)
        else:
            return "%.3f%s" % (float(size)/float(factor), suffix)


def restructured_table(column_names, column_ids, object_list, truncate_len=13):
    """Restructured table creation method

    This method takes some objects in a list and present them in a table format.
    The format is similar with the one used in restructured text, so it can easily
    be used in formatted text.
    The arguments are the following:
    column_names : a list or tuple with the title of each column
    column_id : a list or tuple of all the keys which will be presented from
    each object
    object_list : the list of the objects which contain the data to be presented
    truncate_len : the length of the strings in each cell

    Example output :
    +---------------+---------------+---------------+
    |Alfa           |Beta           |Gama           |
    +---------------+---------------+---------------+
    |2314           |34545          |5666           |
    |12165          |34512345       |53254          |
    +---------------+---------------+---------------+

    """
    single_cell_border = "+" + (truncate_len+2) * "-"
    border = len(column_names) * single_cell_border + "+"
    table = "\n" + border + "\n"
    # Column Headers first
    for column in column_names:
        table += "| %-13s " % column[:truncate_len]
    table += "|\n" + border + "\n"
    # Data next
    for obj in object_list:
        for i in column_ids:
            levels = i.split(".")
            attr = obj
            for l in levels:
                attr = getattr(attr, l)
            table += "| %-13s " % str(attr)[:truncate_len]
        table += "|\n"
    table += border + "\n"
    return table

def paginate(qs, start, end):
    """
    Return the specified queryset paginated by start:end.
    """
    if start is None and end is None:
        return (qs, "")

    int_msg = "Value of '%s' parameter must be an integer."
    neg_msg = "Parameter '%s' cannot be less than 1."
    if start is not None:
        try:
            start = int(start) - 1
            if start < 0:
                return (None, neg_msg % "start")
        except ValueError, TypeError:
            return (None, int_msg % "start")
    if end is not None:
        try:
            end = int(end) - 1
            if end < 0:
                return (None, neg_msg % "end")
        except ValueError, TypeError:
            return (None, int_msg % "end")

    if start is None:
        return (qs[:end], "")
    elif end is None:
        return (qs[start:], "")
    else:
        return (qs[start:end], "")


def queryset_iterator(queryset, chunksize=1000):
    """
    Iterate over a Django Queryset ordered by the primary key

    This method loads a maximum of chunksize (default: 1000) rows in it's
    memory at the same time while django normally would load all rows in it's
    memory. Using the iterator() method only causes it to not preload all the
    classes.

    Note that the implementation of the iterator does not support ordered
    query sets.
    """
    pk = 0
    last_pk = queryset.order_by('-pk')[0].pk
    queryset = queryset.order_by('pk')
    while pk < last_pk:
        for row in queryset.filter(pk__gt=pk)[:chunksize]:
            pk = row.pk
            yield row
        gc.collect()

def normalize_query(query_string,
        findterms=re.compile(r'\'([^\']+)\'|"([^"]+)"|(\S+)').findall,
    normspace=re.compile(r'\s{2,}').sub):
    """
    Splits the query string in individual keywords, getting rid of unnecessary
    spaces and grouping quoted words together.
    Example:

    >>> normalize_query('  some random  words "with   quotes  " and   spaces')
    ['some', 'random', 'words', 'with quotes', 'and', 'spaces']

    """
    return list(set([normspace(' ', (t[0] or t[1] or t[2]).strip()) for t in
        findterms(query_string)]))


class StatBarsPositions(dict):
    """
    Hold the positions of a number of statistic bars.

    Used to present bars for translation completion status.
    """

    class BarPos:
        def __init__(self, width, left=0):
            """Initialize a simple bar."""
            self.w = width
            self.l = left

    def __init__(self, bar_data, width=100, border=1):
        """
        A dictionary to hold the positions of named bars.

        Arguments:

        - An ordered list of tuples (name, bar_width) to render
        - The width of the "100%" bar in pixels
        - The width of a border to pad each consecutive non-zero-sized bar

        Example:

        >>> pos = [('a', 2), ('b', 1), border=1]
        >>> pos['a'].w
        2
        >>> pos['b'].l   # Should return first bar width + border = 2
        3
        """
        innerwidth = width
        if innerwidth < 0:
            raise ValueError('Too many items (%d) for given width (%d) '
                'and border (%d)' % (len(bar_data), width, border))

        totsegwidth = reduce(operator.add, (x[1] for x in bar_data), 0)
        if totsegwidth == 0:
            # No translations whatsoever
            self['trans'] = self.BarPos(width, 0)
            self['fuzzy'] = self.BarPos(0, width)
            self['untrans'] = self.BarPos(0, width)
            return
        oldend = 0
        for segnum, segment in enumerate(bar_data):
            if segment[1] < 0:
                raise ValueError('Negative segment size (%d) given for '
                    'element %d'% (segment[1], segnum + 1))
            fl = oldend
            fr = fl + segment[1] * innerwidth
            oldend = fr
            l = int(round(float(fl) / totsegwidth))
            r = int(round(float(fr) / totsegwidth))
            self[segment[0]] = self.BarPos(r - l, l)
        return
