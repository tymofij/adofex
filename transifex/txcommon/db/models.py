# -*- coding: utf-8 -*-
import base64, datetime, re
from django import forms
from django.conf import settings
from django.db.models.signals import post_save
from django.db.models.fields.related import OneToOneField
from django.db import models
from django.utils.text import compress_string
from django.utils.translation import ugettext_lazy as _
from south.modelsinspector import add_introspection_rules

import cPickle as pickle

def uncompress_string(s):
    """Helper function to reverse django.utils.text.compress_string."""
    import cStringIO, gzip
    try:
        zbuf = cStringIO.StringIO(s)
        zfile = gzip.GzipFile(fileobj=zbuf)
        ret = zfile.read()
        zfile.close()
    except:
        ret = s
    return ret


class ChainerManager(models.Manager):
    """
    Custom manager that has the ability to chain its methods to each other or
    to standard queryset filters.

    It needs to receive a custom ``django.db.model.query.QuerySet`` in order
    to be able to chain the methods.

    Example:

    NewsQuerySet(models.query.QuerySet):
        def live(self):
            return self.filter(state='published')

        def interesting(self):
            return self.filter(interesting=True)

    ChainerManager(NewsQuerySet).live().interesting()
    [<NewsItem: ...>]

    Usually a model will use this manager in the following way:

    NewsItem(models.Model):
        objects = ChainerManager(NewsQuerySet)

    Reference: http://djangosnippets.org/snippets/562/

    """
    def __init__(self, qs_class=models.query.QuerySet):
        super(ChainerManager,self).__init__()
        self.queryset_class = qs_class

    def get_query_set(self):
        return self.queryset_class(self.model)

    def __getattr__(self, attr, *args):
        try:
            return getattr(self.__class__, attr, *args)
        except AttributeError:
            return getattr(self.get_query_set(), attr, *args)


class IntegerTupleField(models.CharField):
    """
    A field type for holding a tuple of integers. Stores as a string
    with the integers delimited by colons.
    """
    __metaclass__ = models.SubfieldBase

    def formfield(self, **kwargs):
        defaults = {
            'form_class': forms.RegexField,
            # We include the final comma so as to not penalize Python
            # programmers for their inside knowledge
            'regex': r'^\((\s*[+-]?\d+\s*(,\s*[+-]?\d+)*)\s*,?\s*\)$',
            'max_length': self.max_length,
            'error_messages': {
                'invalid': _('Enter 0 or more comma-separated integers '
                    'in parentheses.'),
                'required': _('You must enter at least a pair of '
                    'parentheses containing nothing.'),
            },
        }
        defaults.update(kwargs)
        return super(IntegerTupleField, self).formfield(**defaults)

    def to_python(self, value):
        if type(value) == tuple:
            return value
        if type(value) == unicode and value.startswith('(') and \
            value.endswith(')'):
            return eval(value)
        if value == '':
            return ()
        if value is None:
            return None
        return tuple(int(x) for x in value.split(u':'))

    def get_db_prep_value(self, value, connection=None, prepared=False):
        if value is None:
            return None
        return u':'.join(unicode(x) for x in value)

    def get_db_prep_lookup(self, lookup_type, value, connection=None, prepared=False):
        if lookup_type == 'exact':
            return [self.get_db_prep_value(value)]
        else:
            raise TypeError('Lookup type %r not supported' %
                lookup_type)

    def value_to_string(self, obj):
        return self.get_db_prep_value(obj)


class ListCharField(models.CharField):
    """
    A field type for storing concatenated strings using the colon (:) char.

    This field received the values that must be concatenated as a list of
    string object, return also a list of string object whenever the database
    content is required too.
    """
    __metaclass__ = models.SubfieldBase

    def _replace(self, value):
        return [re.sub(r'(?<!\\)\:', '\:', unicode(v)) for v in value]

    # This is also called whenever setting the field value, it means that 
    # values other than a list can be attributed, such as string object.
    def to_python(self, value):
        if type(value) == list:
            return self._replace(value)
        if type(value) == unicode and value.startswith('[') and \
            value.endswith(']'):
            try:
                return self._replace(eval(value))
            except NameError:
                pass
        if value == '':
            return []
        if value is None:
            return None
        return self._replace(re.split(r'(?<!\\)\:', value))

    def get_db_prep_value(self, value, connection=None, prepared=False):
        if value is None:
            return None
        assert isinstance(value, list)
        return u':'.join(unicode(x) for x in value)


class CompressedTextField(models.TextField):
    """
    Transparently compress data before hitting the db and uncompress after
    fetching.
    """
    __metaclass__ = models.SubfieldBase

    def get_db_prep_value(self, value, connection=None, prepared=False):
        if value is not None:
            value = base64.encodestring(compress_string(pickle.dumps(value)))
        return value

    def to_python(self, value):
        if value is None: return
        try:
            value = pickle.loads(uncompress_string(base64.decodestring(value)))
        except:
            # if we can't unpickle it it's not pickled. probably we got a
            # normal string. pass
            pass
        return value

    def post_init(self, instance=None, **kwargs):
        value = self._get_val_from_obj(instance)
        if value:
            setattr(instance, self.attname, value)

    def contribute_to_class(self, cls, name):
        super(CompressedTextField, self).contribute_to_class(cls, name)
        models.signals.post_init.connect(self.post_init, sender=cls)


    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return value

    def get_internal_type(self):
        return "TextField"

    def db_type(self, connection):
        db_types = {'django.db.backends.mysql':'longblob',
                    'django.db.backends.sqlite3':'blob',
                    'django.db.backends.postgres':'text',
                    'django.db.backends.postgresql_psycopg2':'text'}
        try:
            return db_types[connection.settings_dict['ENGINE']]
        except KeyError, e:
            print str(e)
            raise Exception, '%s currently works only with: %s' % (
                self.__class__.__name__,', '.join(db_types.keys()))


"""
South Introspection Extending for Custom fields
Reference: http://south.aeracode.org/docs/customfields.html#extending-introspection
"""

rules = {}
rules['IntegerTupleField'] = [
    (
        [IntegerTupleField],
        [],
        {
            "blank": ["blank", {"default": True}],
            "null": ["null", {"default": True}],
            "max_length": ["max_length", {"default": 64}],
        },
    ),
]

rules['CompressedTextField'] = [
    (
        [CompressedTextField],
        [],
        {
            "blank": ["blank", {"default": True}],
            "null": ["null", {"default": True}],
        },
    ),
]

rules['ListCharField'] = [
    (
        [ListCharField],
        [],
        {
            "blank": ["blank", {"default": True}],
            "null": ["null", {"default": True}],
        },
    ),
]

for f in rules.keys():
    add_introspection_rules(rules[f], ["^transifex\.txcommon\.db\.models\.%s" % f])
