from rest_framework import generics, permissions, status
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from rest_framework.response import Response
from .decorators import log_execution_time
from .models import Transaction, Category
from .serializers import TransactionSerializer, CategorySerializer
from .categorizer import FALLBACK_CATEGORY
from .filters import TransactionFilter
from .pagination import TransactionPagePagination


class CategoryListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CategorySerializer

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user).order_by("name")


class CategoryCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CategorySerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CategoryDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CategorySerializer

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.name == FALLBACK_CATEGORY:
            return Response(
                {"error": f'The "{FALLBACK_CATEGORY}" category cannot be deleted.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)

    def perform_destroy(self, instance):
        # Reassign this category's transactions to the user's fallback before deleting,
        # so no transaction is left pointing at a category that no longer exists.
        fallback = Category.objects.filter(
            user=self.request.user, name=FALLBACK_CATEGORY
        ).first()
        if fallback:
            Transaction.objects.filter(
                user=self.request.user, category=instance
            ).update(category=fallback)
        instance.delete()


class CategoryUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CategorySerializer

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.name == FALLBACK_CATEGORY:
            return Response(
                {"error": f'The "{FALLBACK_CATEGORY}" category cannot be edited.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().update(request, *args, **kwargs)


class TransactionListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TransactionSerializer
    pagination_class = TransactionPagePagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = TransactionFilter

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user).select_related(
            "category"
        )


class TransactionUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TransactionSerializer

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)


class SpendingOverTimeByCategoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @log_execution_time
    def get(self, request):
        from collections import defaultdict

        rows = (
            Transaction.objects.filter(user=request.user, is_credit=False)
            .annotate(month=TruncMonth("date"))
            .values("month", "category__name", "category__color")
            .annotate(total=Sum("amount"))
            .order_by("month", "category__name")
        )

        monthly = defaultdict(dict)
        category_colors = {}

        for row in rows:
            key = row["month"].strftime("%Y-%m")
            name = row["category__name"]
            color = row["category__color"]
            monthly[key][name] = float(row["total"])
            category_colors[name] = color

        data = [{"month": month, **values} for month, values in sorted(monthly.items())]
        categories = [
            {"name": name, "color": color}
            for name, color in sorted(category_colors.items())
        ]

        return Response({"data": data, "categories": categories})

class DashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @log_execution_time
    def get(self, request):
        from collections import defaultdict

        month_str = request.query_params.get("month")
        year, month = map(int, month_str.split("-"))

        rows_top_categories = (
            Transaction.objects.filter(
                user=request.user, 
                is_credit=False, 
                date__year=year, 
                date__month = month)
            .values("category__name", "category__color")
            .annotate(total=Sum("amount"))
            .order_by("-total")[:3]
        )

        rows_top_merchants = (
            Transaction.objects.filter(
                user=request.user, 
                is_credit=False, 
                date__year=year, 
                date__month = month)
            .values("description")
            .annotate(total=Sum("amount"))
            .order_by("-total")[:3]
        )

        rows_biggest_transactions = (
            Transaction.objects.filter(
                user=request.user,
                is_credit=False,
                date__year=year,
                date__month=month
            )
            .values("description", "amount")
            .order_by("-amount")[:3]
            )
        
        total_by_month = (
            Transaction.objects.filter(
                user=request.user,
                is_credit=False,
                date__year=year,
                date__month=month
            )
            .aggregate(total=Sum("amount"))
        )

        if month == 1:
            total_by_month_previous = (
                Transaction.objects.filter(
                    user=request.user,
                    is_credit=False,
                    date__year=year-1,
                    date__month=12
                )
                .aggregate(total=Sum("amount"))
            )
        else:

            total_by_month_previous = (
                Transaction.objects.filter(
                    user=request.user,
                    is_credit=False,
                    date__year=year,
                    date__month=month-1
                )
                .aggregate(total=Sum("amount"))
            )
        percentual_change = 100*(total_by_month["total"] - total_by_month_previous["total"])/total_by_month_previous["total"] if total_by_month_previous["total"] and total_by_month["total"] is not None else None
        
        data_top_categories = {"top_categories": []}
        data_top_merchants = {"top_merchants": []}
        data_biggest_transactions = {"biggest_transactions": []}

        for row in rows_top_categories:
            data_top_categories["top_categories"].append(
                {
                    "name": row["category__name"], 
                    "total": row["total"], 
                    "color": row["category__color"]
                },
            )

        for row in rows_top_merchants:
            data_top_merchants["top_merchants"].append(
                {
                    "name": row["description"],
                    "total": row["total"]
                }
            )
        
        for row in rows_biggest_transactions:
            data_biggest_transactions["biggest_transactions"].append(
                {
                    "description": row["description"],
                    "amount": row["amount"]
                }
            )
        data = {
                    **total_by_month, 
                    "variation": percentual_change,
                    **data_top_categories,
                    **data_top_merchants,
                    **data_biggest_transactions
                }
        
        return Response(data)


class TransactionsMonthsView(APIView):
    permissions_classes = [permissions.IsAuthenticated]

    def get(self,request):

        rows = (Transaction.objects.filter(user=request.user)
        .annotate(total=TruncMonth("date"))
        .order_by()
        .values("total").distinct().order_by("total"))

        
        data = [{"month": row["total"].strftime("%Y-%m")}  for row in rows]

        return Response(data)
    

class SpendingOverTimeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @log_execution_time
    def get(self, request):
        from collections import defaultdict

        rows = (
            Transaction.objects.filter(user=request.user, is_credit=False)
            .annotate(month=TruncMonth("date"))
            .values("month", "bank")
            .annotate(total=Sum("amount"))
            .order_by("month", "bank")
        )

        monthly = defaultdict(dict)
        banks = set()

        for row in rows:
            key = row["month"].strftime("%Y-%m")
            bank = row["bank"]
            monthly[key][bank] = float(row["total"])
            banks.add(bank)

        data = [{"month": month, **values} for month, values in sorted(monthly.items())]

        return Response({"data": data, "banks": sorted(banks)})
