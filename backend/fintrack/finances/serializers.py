from rest_framework import serializers
from .models import Transaction, Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "color"]


class TransactionSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

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
        ]
        read_only_fields = ["id"]
