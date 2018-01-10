from django import template

register = template.Library()

@register.filter(name='entity_translation')
def entity_translation(source_entity, language):
    return source_entity.get_translation(language.code)


@register.filter
def sort_source_langs_first(rlstats, source_language_codes):
    """
    Take a RLStats aggregated queryset and move the entries related to the
    source_languages to the top of the list.
    """
    rlstats_source_list, rlstats_list = [], []
    for r in rlstats:
        if r.object.code in source_language_codes:
            rlstats_source_list.append(r)
        else:
            rlstats_list.append(r)
    # 'tag' first translation entry in the list
    if rlstats_list:
        stat = rlstats_list[0]
        stat.first_translation = True
        rlstats_list = [stat] + rlstats_list[1:]

    return rlstats_source_list + rlstats_list


@register.filter
def language_codes_list(languages):
    """Get a Language queryset and return a list of language codes."""
    return set(languages.values_list('code', flat=True))
