from django import template
from django.utils.timesince import timesince
from transifex.languages.models import Language
from transifex.resources.models import RLStats
from transifex.txcommon.utils import StatBarsPositions

register = template.Library()

def calculate_stats(stat, width=100):
    """
    Create a HTML bar to present the statistics of an object.

    The object should have attributes trans_percent/untrans_percent.
    Accepts an optional parameter to specify the width of the total bar.

    We do a bit of calculations ourselfs here to reduce the pressure on
    the database.
    """
    total = stat.total
    trans = stat.translated
    reviewed = 0
    show_reviewed_stats = False
    if isinstance(stat, RLStats):
        reviewed = stat.reviewed
        resource = stat.resource
        if resource.source_language != stat.language:
            show_reviewed_stats = True

    # Fail-safe check
    # TODO add to the setting part, not getting.
    if trans > total:
        trans = 0

    try:
        trans_percent = (trans * 100 / total)
    except ZeroDivisionError:
        trans_percent = 100

    untrans_percent = 100 - trans_percent
    untrans = total - trans

    return {'untrans_percent': untrans_percent,
            'trans_percent': trans_percent,
            'untrans': untrans,
            'trans': trans,
            'pos': StatBarsPositions([('trans', trans_percent),
                                      ('untrans', untrans_percent)], width),
            'width':width,
            'reviewed': reviewed,
            'show_reviewed_stats': show_reviewed_stats}


@register.inclusion_tag("resources/stats_bar_simple.html")
def stats_bar_simple(stat, width=100):

    return calculate_stats(stat, width)

@register.inclusion_tag("resources/stats_bar_simple.html")
def stats_bar_simple_args(translated, total, width=100):

    class Stats(object):
        def __init__(self, translated, total):
            self.translated = translated
            self.total = total

    return calculate_stats(Stats(translated, total), width)


@register.inclusion_tag("resources/stats_bar_actions.html")
def stats_bar_actions(stat, width=100):
    """
    Create a HTML bar to present the statistics of an object.

    The object should have attributes trans_percent/untrans_percent.
    Accepts an optional parameter to specify the width of the total bar.
    """
    try:
        trans_percent = (stat.translated * 100 / stat.total)
    except ZeroDivisionError:
        trans_percent = 100
    untrans_percent = 100 - trans_percent
    return {'untrans_percent': untrans_percent,
            'trans_percent': trans_percent,
            'pos': StatBarsPositions([('trans', trans_percent),
                                      ('untrans', untrans_percent)], width),
            'width':width}

@register.filter(name='percentage')
def percentage(fraction, population):
    try:
        return "%s%%" % int(((fraction)*100 / (population)) )
    except ZeroDivisionError:
        if population == fraction:
            return "100%%"
        else:
            return ''
    except ValueError:
        return ''

