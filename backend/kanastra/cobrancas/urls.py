from django.urls import path
from .views import upload_csv, list_files, save_file_name, health_check

urlpatterns = [
    path("upload-csv/", upload_csv, name="upload_csv"),
    path("list-files/", list_files, name="list_file"),
    path("save-file-name/", save_file_name, name="save_file_name"),
    path("health/", health_check, name="health_check"),
    # Add other URL patterns as needed
]
