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


class TransactionSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
    queryset=Category.objects.all(), source="category", write_only=True)


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
