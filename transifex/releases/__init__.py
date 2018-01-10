
# Config settings for the "All Resources" release (refer to
# transifex.releases.handlers for more info).
# FIXME: This is too ugly. For now placing it here to avoid circular 
# dependencies.
RELEASE_ALL_DATA = {
    'slug': 'all-resources',
    'name': 'All Resources',
    'description': "A collection of all the resources of this project (auto-managed by Transifex)"}

# List of slugs which are reserved and should not be used by users.
RESERVED_RELEASE_SLUGS = [RELEASE_ALL_DATA['slug'],]

from transifex.releases import handlers
