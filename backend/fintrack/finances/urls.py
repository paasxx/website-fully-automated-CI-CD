from django.urls import path
from .views import TransactionListView, SpendingOverTimeView

urlpatterns = [
    path("transactions/", TransactionListView.as_view(), name="transaction-list"),
    path("spending-over-time/", SpendingOverTimeView.as_view(), name="spending-over-time"),
]
