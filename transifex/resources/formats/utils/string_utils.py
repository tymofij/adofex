# -*- coding: utf-8 -*-

from Levenshtein import distance

def percent_diff(a, b):
    try:
        return 100 * distance(a, b) / float(max(len(a), len(b)))
    except ZeroDivisionError:
        if len(a)==len(b): return 0
        else: return 100


def split_by_newline(text, start=0):
    """Generator to split the text in newlines.

    Args:
        text: The text to split.
        start: Where to start the split from.
    Returns:
        A line at a time.
    """
    index = start
    while 1:
        new_index = text.find('\n', index)
        if new_index == -1:
            yield (-1, text[index:])
            break
        yield (new_index + 1, text[index:new_index])
        index = new_index + 1
