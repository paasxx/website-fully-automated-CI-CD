from django.urls import path
from .views import (
    CategoryDeleteView,
    CategoryUpdateView,
    TransactionListView,
    SpendingOverTimeView,
    SpendingOverTimeByCategoryView,
    DashboardView,
    CategoryListView,
    CategoryCreateView,
    TransactionsMonthsView,
    TransactionUpdateView,
)

urlpatterns = [
    path("transactions/", TransactionListView.as_view(), name="transaction-list"),
    path(
        "transactions/<int:pk>/",
        TransactionUpdateView.as_view(),
        name="transaction-update",
    ),
    path(
        "spending-over-time/", SpendingOverTimeView.as_view(), name="spending-over-time"
    ),
    path(
        "spending-over-time-by-category/",
        SpendingOverTimeByCategoryView.as_view(),
        name="spending-over-time-by-category",
    ),
    path("months/", TransactionsMonthsView.as_view(), name="months" ),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("categories/create/", CategoryCreateView.as_view(), name="category-create"),
    path("categories/<int:pk>/", CategoryUpdateView.as_view(), name="category-update"),
    path(
        "categories/<int:pk>/delete/",
        CategoryDeleteView.as_view(),
        name="category-delete",
    ),
]
