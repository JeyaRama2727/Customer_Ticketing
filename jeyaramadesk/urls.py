"""
JeyaRamaDesk — Root URL Configuration
"""

from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

_urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # App routes (template views)
    path('', include('dashboard.urls')),
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('allauth.urls')),      # Google OAuth routes
    path('tickets/', include('tickets.urls')),
    path('sla/', include('sla.urls')),
    path('automation/', include('automation.urls')),
    path('knowledge-base/', include('knowledge_base.urls')),
    path('reports/', include('reports.urls')),
    path('notifications/', include('notifications.urls')),
    path('chat/', include('livechat.urls')),

    # API routes
    path('api/accounts/', include('accounts.api.urls')),
    path('api/tickets/', include('tickets.api.urls')),
    path('api/sla/', include('sla.api.urls')),
    path('api/dashboard/', include('dashboard.api.urls')),
    path('api/notifications/', include('notifications.api.urls')),
    path('api/reports/', include('reports.api.urls')),
    path('api/knowledge-base/', include('knowledge_base.api.urls')),
]

# In production, wrap under /desk/
if getattr(settings, 'URL_PREFIX', None):
    urlpatterns = [path('desk/', include(_urlpatterns))]
else:
    urlpatterns = _urlpatterns

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom admin site branding
admin.site.site_header = 'JeyaRamaDesk Administration'
admin.site.site_title = 'JeyaRamaDesk Admin'
admin.site.index_title = 'Support Platform Management'
