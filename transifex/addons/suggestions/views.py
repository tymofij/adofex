# -*- coding: utf-8 -*-
from django.http import (HttpResponse, HttpResponseBadRequest)
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext as _

from authority.views import permission_denied

from transifex.languages.models import Language
from transifex.projects.permissions.project import ProjectPermission
from transifex.resources.models import SourceEntity

from models import Suggestion

#FIXME: Get this into Piston instead, as part of the normal API.
def suggestion_create(request, entity_id, lang_code):
    """Create a suggestion for an entity and a language."""

    source_entity = get_object_or_404(SourceEntity, pk=entity_id)

    # Permissions handling
    check = ProjectPermission(request.user)
    if not check.private(source_entity.resource.project):
        return permission_denied(request)

    #FIXME: All basic POST checks could be done in a decorator.
    if not request.method == "POST":
        return HttpResponseBadRequest(_("POST method only allowed."))
    suggestion_string = request.POST['suggestion_string']
    if not suggestion_string:
        return HttpResponseBadRequest(_("POST variable 'suggestion_string' missing."))

    language = Language.objects.by_code_or_alias(lang_code)
    source_entity.suggestions.create(language=language,
                                     string=request.POST['suggestion_string'],
                                     user=request.user)
    return HttpResponse(status=200)


#FIXME: Get this into Piston instead, as part of the normal API.
def suggestion_vote(request, entity_id, lang_code, suggestion_id, direction):
    
    """Vote up or down for a suggestion."""

    suggestion = get_object_or_404(Suggestion, pk=suggestion_id)

    # Permissions handling
    check = ProjectPermission(request.user)
    if not check.private(suggestion.source_entity.resource.project):
        return permission_denied(request)

    #FIXME: All basic POST checks could be done in a decorator.
    if not request.method == "POST":
        return HttpResponseBadRequest(_("POST method only allowed."))

    if direction == 'up':
        suggestion.vote_up(request.user)
    elif direction == 'down':
        suggestion.vote_down(request.user)

    return HttpResponse(status=200)
