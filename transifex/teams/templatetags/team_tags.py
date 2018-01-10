# -*- coding: utf-8 -*-
from django import template
from transifex.resources.models import RLStats
from transifex.teams.models import Team
from transifex.txcommon.utils import StatBarsPositions

register = template.Library()

@register.filter
def language_has_team(lang_code, project):
    """
    Return if the specific language has a corresponding team for the project.

    Example: {% if language_obj.code|language_has_team:stat.object.project %}
    """

    return Team.objects.get_or_none(project, lang_code)
