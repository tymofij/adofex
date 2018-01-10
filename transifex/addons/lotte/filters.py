# -*- coding: utf-8 -*-
import re, datetime
from django.db.models import Q

# Filters allowed in Lotte search box
SEARCH_FILTERS = {
    'after': {
        'validator': lambda date: validate_date(date),
        'query': lambda date: Q(last_update__gte=date)
        },
    'before': {
        'validator': lambda date: validate_date(date),
        'query': lambda date: Q(last_update__lte=date)
        },
    'file': {
        'validator': lambda fpath: re.match(r'^[\w\-\/\.\\]+$', fpath),
        'query': lambda fpath: Q(source_entity__occurrences__icontains=fpath)
        }
    }

def validate_date(date):
    """
    Check whether a date is valid. Match values in the following format
    AAAA-MM-DD.
    """
    regex = r'^[0-9]{4}\-(1[0-2]|0[1-9])\-(3[01]|[12][0-9]|0[1-9])$'
    if re.match(regex, date):
        year, month, day = map(int, date.split('-'))
        try:
            datetime.date(year, month, day)
            return True
        except ValueError:
            pass
    return False

def get_search_filter_query(search):
    """
    Create a query for eventual filters found within the search text and also
    drops theses filter keywords from the search.
    
    Return a tuple with the modified search text and the created query.
    """
    # Expression to match 'key:value' entries within the search box
    search_filter_expr = r'(?P<key>\w+)\:(?P<value>[\w\-\/\.\\]+)'
    search_filter_query = Q()
    # Check for filter entries
    for match in re.finditer(search_filter_expr, search):
        k, v = match.group('key'), match.group('value')
        # In case it's a valid filter
        if k in SEARCH_FILTERS.keys():
            # Drop filter from search text
            search = search.replace(':'.join([k,v]), '')
            # If value of the filter passes the validation, add it to the query
            if SEARCH_FILTERS[k]['validator'](v):
                search_filter_query &= SEARCH_FILTERS[k]['query'](v)
                
    return search, search_filter_query
