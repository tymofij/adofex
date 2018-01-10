from django import template

register = template.Library()

@register.inclusion_tag("form_as_table_rows.html")
def form_as_table_rows(form):
    """
    Create a form using HTML table rows.
    """
    return {"form": form}
