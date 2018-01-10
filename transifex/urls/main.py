# Main urlconf file of Transifex used in ROOT_URLCONF
from common import urlpatterns
from extra import urlpatterns as urlpatterns_extra

urlpatterns += urlpatterns_extra