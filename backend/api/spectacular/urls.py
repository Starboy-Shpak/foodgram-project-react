from drf_spectacular.views import SpectacularSwaggerView

from django.urls import path

urlpatterns = [
    path('', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]