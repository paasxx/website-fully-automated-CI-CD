from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def health(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health),
    path("api/auth/", include("identity.urls")),
    path("api/finances/", include("finances.urls")),
    path("api/import/", include("statements.urls")),
]
