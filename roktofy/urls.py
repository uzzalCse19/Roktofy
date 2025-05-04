from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from roktofy.views import api_root_view
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

import debug_toolbar

schema_view = get_schema_view(
    openapi.Info(
        title="Blood Bank Project",
        default_version='v1',
        description="API documentation for Blood Bank Project",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@roktory.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('', api_root_view),
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls'),name='api-root'),
    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.jwt')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('api/', include('users.urls')),
    path('api/', include('core.urls')),  
 
]

if settings.DEBUG:
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
