from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from core.views import aboutpage, contact, frontpage
from django.views.generic.base import TemplateView


urlpatterns = [
    path('', include('store.urls')),
    path('', include('userprofile.urls')),
    path('', frontpage, name='frontpage'),
    path('admin/', admin.site.urls),
    path('about/', aboutpage, name='about'),
    path('contact/', contact, name='contact'),
    path('__debug__/', include('debug_toolbar.urls')),
    path('robots.txt/', TemplateView.as_view(
        template_name='robots.txt', content_type='text/plain')),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += [path('silk/', include('silk.urls', namespace='silk'))]
