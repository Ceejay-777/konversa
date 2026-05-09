from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from accounts.views import health
import django_eventstream


urlpatterns = [
    path('docs', SpectacularSwaggerView.as_view(url_name='schema'), name='redoc'),
    path('api/raw', SpectacularAPIView.as_view(), name='schema'),
    path('api/redoc', SpectacularRedocView.as_view(url_name='schema'), name='swagger-ui'),
    
    path("health/", health, name="health"),
    
    path("events/", include("django_eventstream.urls")),
    
    path("api/", include("accounts.urls")),
    path("api/", include("products.urls")),
    path("api/", include("stores.urls")),
]

