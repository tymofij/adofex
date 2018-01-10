"""
Template tags to make strings shorter in various ways.
"""

from django import template

register = template.Library()


@register.filter
def truncate_chars(value, max_length):
    """
    Truncates a string after a certain number of characters.
    """
    max_length = int(max_length)
    if len(value) > max_length:
        truncd_val = value[:max_length-1]
        if value[max_length] != " ":
            truncd_val = truncd_val[:truncd_val.rfind(" ")]
        return  truncd_val + "..."
    return value

@register.filter
def truncate_chars_middle(value, max_length):
    """
    Truncate a string putting dots in the its middle after a certain number of
    characters.
    """
    max_length = int(max_length)
    value_length = len(value)
    if value_length > max_length:
        max_first = max_length/2
        div_rest = max_length%2
        truncd_val = value[:max_first-2+div_rest]
        truncd_val2 = value[-(max_first-1):]
        return truncd_val + "..." + truncd_val2
    return value