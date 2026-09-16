import django_filters
from .models import Transaction


class TransactionFilter(django_filters.FilterSet):
    # Text search on description — icontains = case-insensitive substring match.
    # At scale, add a GIN trigram index on description for faster ILIKE queries.
    search = django_filters.CharFilter(field_name="description", lookup_expr="icontains")
    category = django_filters.NumberFilter(field_name="category__id", lookup_expr="exact")
    # Date range — ISO format (YYYY-MM-DD) expected from the frontend date inputs.
    date_from = django_filters.DateFilter(field_name="date", lookup_expr="gte")
    date_to   = django_filters.DateFilter(field_name="date", lookup_expr="lte")

    class Meta:
        model = Transaction
        # Exact-match fields declared here; range/search fields declared above.
        fields = ["bank", "is_credit", "is_installment"]
