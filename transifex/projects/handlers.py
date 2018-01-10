# -*- coding: utf-8 -*-

from __future__ import absolute_import
from transifex.txcommon.cache import update_template_cache


def on_outsource_change(sender, **kwargs):
    """Signal handler for changes in the outsource project."""
    if sender is None:
        return
    project = sender
    update_template_cache(
        'projects/project_hub_projects.html', ['hub_projects', ],
        key_vars=[project, ],
        context={
            'project': project,
            'outsourcing_projects': project.outsourcing.all()
        }
    )
