import copy
from django import template
from django import forms
from django.utils.datastructures import SortedDict

register = template.Library()

class FieldsetNode(template.Node):
    def __init__(self, fields, variable_name, form_variable):
        self.fields = fields
        self.variable_name = variable_name
        self.form_variable = form_variable

    def render(self, context):
        form = template.Variable(self.form_variable).resolve(context)
        new_form = copy.copy(form)
        new_form.fields = SortedDict(
            [(key, form.fields[key]) for key in self.fields]
        )
        context[self.variable_name] = new_form
        return u''

@register.tag(name='get_fieldset')
def get_fieldset(parser, token):
    """
    A simple templatetag to split form fields into fieldsets from the template.

    Usage:
    {% load fieldsets %}

    {% get_fieldset slug,name,description,maintainers,tags as simple_fields from project_form %}
    {% for field in simple_fields %}
        {{ field }}
    </div>
    {% endfor %}
    """
    try:
        name, fields, as_, variable_name, from_, form = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError('Bad arguments for %r' % token.split_contents()[0])

    return FieldsetNode(fields.split(','), variable_name, form)

