from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from .models import Transaction
from .serializers import TransactionSerializer


class TransactionListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = Transaction.objects.filter(user=request.user).select_related("category")

        month = request.query_params.get("month")
        year = request.query_params.get("year")
        bank = request.query_params.get("bank")

        if year:
            qs = qs.filter(date__year=year)
        if month:
            qs = qs.filter(date__month=month)
        if bank:
            qs = qs.filter(bank=bank)

        return Response(TransactionSerializer(qs, many=True).data)


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
