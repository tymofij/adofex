# -*- coding: utf-8 -*-
from django import template
from django.db.models import get_model

from transifex.txcommon.templatetags.txcommontags import ResolverNode

Suggestion = get_model('suggestions', 'Suggestion')

register = template.Library()

class SuggestionsNode(ResolverNode):

    @classmethod
    def handle_token(cls, parser, token, name):
        bits = token.contents.split()
        tag_name = bits[0]
        kwargs = {
            'source_entity_id': cls.next_bit_for(bits, tag_name),
            'lang_code': cls.next_bit_for(bits, 'for'),
            'var_name': cls.next_bit_for(bits, 'as', name),
        }
        return cls(**kwargs)

    def __init__(self, source_entity_id, lang_code, var_name):
        self.source_entity_id = source_entity_id
        self.lang_code = lang_code
        self.var_name = var_name

    def render(self, context):
        # Get values from context
        source_entity_id = self.resolve(self.source_entity_id, context)
        lang_code = self.resolve(self.lang_code, context)
        
        # Do what's needed to be done
        suggestions = Suggestion.objects.filter(
            source_entity__id=source_entity_id,
            language__code=lang_code).order_by('-score')

        # Put the result into the context
        context[self.var_name] = suggestions
        return ''

@register.tag
def get_suggestions(parser, token):
    """
    Retrieves all suggestions associated with the given source_entity_id and
    lang_code and assigns the result to a context variable.
    
    Syntax::

        {% get_suggestions source_entity_id for lang_code %}
        {% for s in suggestions %}
            {{ s }}
        {% endfor %}

        {% get_suggestions source_entity_id for lang_code as my_suggestions %}
        
    """
    return SuggestionsNode.handle_token(parser, token, name='suggestions')