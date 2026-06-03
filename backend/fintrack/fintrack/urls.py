from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("identity.urls")),
    path("api/finances/", include("finances.urls")),
    path("api/import/", include("statements.urls")),
]
