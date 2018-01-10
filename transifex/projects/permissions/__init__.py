# Project permissions required
# FIXME: It could be a dictionary with better key naming instead of a bunch of
# variables
pr_project_add = (
    ('general',  'projects.add_project'),
)

pr_project_add_change = (
    ('granular', 'project_perm.maintain'),
    ('general',  'projects.change_project'),
)

pr_project_delete = (
    ('granular', 'project_perm.maintain'),
    ('general',  'projects.delete_project'),
)

pr_project_add_perm = (
    ('granular', 'project_perm.maintain'),
    ('general',  'authority.add_permission'),
)

pr_project_approve_perm = (
    ('granular', 'project_perm.maintain'),
    ('general',  'authority.approve_permission_requests'),
)

pr_project_delete_perm = (
    ('granular', 'project_perm.maintain'),
    ('general',  'authority.delete_permission'),
)

pr_project_private_perm = (
    ('granular', 'project_perm.private'),
)

# Release permissions required

pr_release_add_change = (
    ('granular', 'project_perm.maintain'),
    ('general',  'projects.add_release'),
    ('general',  'projects.change_release'),
)

pr_release_delete = (
    ('granular', 'project_perm.maintain'),
    ('general',  'projects.delete_release'),
)

# Resource Permissions

pr_resource_translations_delete=(
    ("granular", "project_perm.maintain"),
    ("general",  "resources.delete_resource"),)

pr_resource_add_change=(
    ("granular", "project_perm.maintain"),
    ('general',  'resources.add_resource'),
    ("general",  "resources.change_resource"),)

pr_resource_delete=(
    ("granular", "project_perm.maintain"),
    ("general",  "resources.delete_resource"),)

pr_resource_priority=(
    ("granular", "project_perm.maintain"),)
