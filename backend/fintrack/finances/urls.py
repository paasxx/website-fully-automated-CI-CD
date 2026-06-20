from django.urls import path
from .views import TransactionListView, SpendingOverTimeView, CategoryListView, TransactionUpdateView

urlpatterns = [
    path("transactions/", TransactionListView.as_view(), name="transaction-list"),
    path("transactions/<int:pk>/", TransactionUpdateView.as_view(), name="transaction-update"),
    path("spending-over-time/", SpendingOverTimeView.as_view(), name="spending-over-time"),
    path("categories/", CategoryListView.as_view(), name="category-list"),
]
