from rest_framework import generics, permissions
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Transaction, Category
from .serializers import TransactionSerializer, CategorySerializer
from .filters import TransactionFilter
from .pagination import TransactionPagePagination

class CategoryListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CategorySerializer


    def get_queryset(self):
        return Category.objects.filter(user=None).order_by("name")
    
    
class TransactionListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TransactionSerializer
    pagination_class = TransactionPagePagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = TransactionFilter

    def get_queryset(self):
        return (
            Transaction.objects
            .filter(user=self.request.user)
            .select_related("category")
        )
    
class TransactionUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TransactionSerializer

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)
    



class SpendingOverTimeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from collections import defaultdict

        rows = (
            Transaction.objects
            .filter(user=request.user, is_credit=False)
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

        data = [
            {"month": month, **values}
            for month, values in sorted(monthly.items())
        ]

        return Response({"data": data, "banks": sorted(banks)})
