"""
NOTE: Why does Transifex have another pagination method?

Django-pagination does not work with POST method. Once the navigation among
the forms/pages of the translation wizard (webtrans app) requires a POST
method to be sent, in order to save the data in the session for each form/page,
it was necessary to implement a new templatetag for this kind of situation.

The most import part of this templatetag is the fact it allows to use a custom
template file anywhere it's needed. The template file used for the translation
wizard has its organization for each page as 'submit' buttons, so the whole
form is sent whenever a user navigates to another page.

Usage:

{% load txpagination %}
{% paginate "/items/" items current_page_number 20 6 paged_items %}
{% for item in paged_items %}
  {{ item }}
{% endfor %}
{% include "pagination.html" %}

Reference:
http://blog.awarelabs.com/2009/digg-style-pagination-in-django-revisited/
"""
import math
from django import template

register = template.Library()

class Pages:
  def __init__(self, view, page, pages, segment):
    self.view = view
    self.page = page + 1
    self.pages = pages
    self.left = []
    self.middle = []
    self.right = []
    self.next = None
    self.previous = None

    if self.page > 1:
      self.previous = self.page - 1

    p = int(1)

    while p < segment and p <= self.pages:
      self.left.append(p)
      p = p + 1

    if p < self.page - segment/2:
      p = self.page - segment/2 + 1

    if p > segment:
      while p < self.page + segment/2 and p <= self.pages:
        self.middle.append(int(p))
        p = p + 1
    else:
      while p < self.page + segment/2 and p <= self.pages:
        self.left.append(int(p))
        p = p + 1

    if p < self.pages - segment/2:
      p = self.pages - segment/2

    if p > self.pages - segment/2:
      while p < self.pages:
        self.middle.append(int(p))
        p = p + 1
    else:
      while p <= self.pages:
        self.right.append(int(p))
        p = p + 1

    if self.page < self.pages:
      self.next = self.page + 1

class PaginationNode(template.Node):
  def __init__(self, view, objects_var, page_var, step, segment, variable):
    self.view = view
    self.objects_var = objects_var
    self.page_var = page_var
    self.step = step
    self.segment = segment
    self.variable = variable

  def render(self, context):

    try:
        self.step = int(self.step)
    except ValueError:
        self.step = int(template.resolve_variable(self.step, context))

    try:
        self.segment = int(self.segment)
    except ValueError:
        self.segment = int(template.resolve_variable(self.segment, context))

    objects = template.resolve_variable(self.objects_var, context)

    page = template.resolve_variable(self.page_var, context)
    if not page:
      page = 1

    page = int(page) - 1

    count = len(objects)
    pages = math.ceil(float(count) / self.step)

    try:
      context[self.variable] = objects[page * self.step: (page + 1) * self.step]
      context['pagination'] = Pages(self.view, page, pages, self.segment)
    except:
      pass

    return ''

def paginate(parser, token):
  tokens = token.contents.split()
  if len(tokens) != 7:
    raise template.TemplateSyntaxError, "pagination tag takes view, objects, page, step, segment, and variable as arguments"
  return PaginationNode(tokens[1], tokens[2], tokens[3], tokens[4], tokens[5], tokens[6])

register.tag('txpaginate', paginate)

