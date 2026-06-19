from django.urls import path
from .views import TransactionListView, SpendingOverTimeView, CategoryListView

urlpatterns = [
    path("transactions/", TransactionListView.as_view(), name="transaction-list"),
    path("spending-over-time/", SpendingOverTimeView.as_view(), name="spending-over-time"),
    path("categories/", CategoryListView.as_view(), name="category-list"),
]
