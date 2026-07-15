from rest_framework import serializers
from .models import Transaction, Category
from .categorizer import FALLBACK_CATEGORY


class CategorySerializer(serializers.ModelSerializer):
    is_locked = serializers.SerializerMethodField()

    def get_is_locked(self, obj):
        # The fallback category ("Other") can't be edited or deleted by the user.
        return obj.name == FALLBACK_CATEGORY

    class Meta:
        model = Category
        fields = ["id", "name", "color", "is_locked"]
        read_only_fields = ["id", "is_locked"]


class UserCategoryField(serializers.PrimaryKeyRelatedField):
    """A ``category_id`` must reference a category owned by the requesting user.

    PrimaryKeyRelatedField with a static ``queryset=`` validates the id against
    the whole table, which lets one user point a transaction at another user's
    category (an IDOR leak). Overriding ``get_queryset`` instead scopes the
    validation queryset per-request — DRF calls it at validation time, when the
    ``request`` already exists in the serializer context.
    """

    def get_queryset(self):
        request = self.context.get("request", None)
        if request is None:
            return Category.objects.none()
        return Category.objects.filter(user=request.user)


class TransactionSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = UserCategoryField(source="category", write_only=True)


    class Meta:
        model = Transaction
        fields = [
            "id",
            "date",
            "description",
            "amount",
            "bank",
            "is_credit",
            "is_installment",
            "installment_number",
            "installment_total",
            "balance_after",
            "bank_category",
            "transaction_type",
            "category",
            "category_id",
        ]
        read_only_fields = ["id"]
