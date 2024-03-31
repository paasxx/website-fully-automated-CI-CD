from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("cobrancas.urls")),  # Include cobrancas app URLs
    # Add other URL patterns as needed
]
