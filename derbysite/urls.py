from django.conf.urls import *
from django.conf import settings
from django.views.static import serve
from django.contrib import admin

# Only for dev/debug mode
from django.conf.urls.static import static

from django.contrib import admin
admin.autodiscover()

app_name = 'runner'

urlpatterns = [
    url(r'^admin_tools/', include('admin_tools.urls')),
    url(r'^runner/', include('runner.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
]
