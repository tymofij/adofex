from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import get_object_or_404, render_to_response
from django.utils.translation import ugettext_lazy as _
from django.views.generic.list_detail import object_list
from transifex.projects.models import Project
from transifex.projects.permissions import pr_project_add_change
from transifex.projects.permissions.project import ProjectPermission
from transifex.txcommon.decorators import one_perm_required_or_403
from transifex.txcommon.views import permission_denied

from cla.forms import ClaForm
from cla.models import Cla
from cla.handlers import handle_pre_team

@login_required
def view(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    cla = get_object_or_404(Cla, project=project)
    return render_to_response(
        "view_cla.html",
        {'project': project, 'cla': cla},
        context_instance= RequestContext(request)
    )
    
@login_required
def cla_project_sign(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    cla = get_object_or_404(Cla, project=project)

    check = ProjectPermission(request.user)
    if not check.submit_translations(project, any_team=True):
        return permission_denied(request)
    
    try:
        signed_cla = request.user.cla_set.filter(project=project)[0]
    except IndexError:
        signed_cla = None
    
    if request.method == 'POST' and not signed_cla:
        form = ClaForm(request.POST)
        if form.is_valid():
            kwargs = {'cla_sign':True, 'project':project, 'user':request.user}
            handle_pre_team(None, **kwargs)
            
            messages.success(request, _("You have signed the CLA."))

            return HttpResponseRedirect(reverse('cla_project_sign',
                args=[project_slug]),)
    else:
        form = ClaForm()
    
    return render_to_response(
        "project_cla.html",
        {'project': project, 
         'cla': cla, 
         'signed_cla': signed_cla,
         'form': form},
        context_instance= RequestContext(request)
    )

@login_required
@one_perm_required_or_403(pr_project_add_change,
    (Project, 'slug__exact', 'project_slug'))
def users(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    cla = get_object_or_404(Cla, project=project)
    
    signed_user_ids = cla.users.values_list('id', flat=True).query
    
    unsigned_user_list = User.objects.filter(
        Q(team_coordinators__project=project) | 
        Q(team_members__project=project) |
        Q(teamrequest__project=project) |
        Q(teamaccessrequest__team__project=project)
        ).exclude(id__in=signed_user_ids).distinct()

    return render_to_response(
        "user_list.html",
        {'project': project, 
         'cla': cla,
         'signed_user_list': cla.users.all().order_by('username'),
         'unsigned_user_list': unsigned_user_list.order_by('username')},
        context_instance= RequestContext(request)
    )
