from django.urls import path
from .views import StatementUploadView, StatementListView

urlpatterns = [
    path("upload/", StatementUploadView.as_view(), name="statement-upload"),
    path("", StatementListView.as_view(), name="statement-list"),
]
