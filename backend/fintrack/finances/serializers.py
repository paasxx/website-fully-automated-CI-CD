from rest_framework import serializers
from .models import Transaction, Category


class CategorySerializer(serializers.ModelSerializer):
    is_system = serializers.SerializerMethodField()

    def get_is_system(self, obj):
        return obj.user is None
    
    
    class Meta:
        model = Category
        fields = ["id", "name", "color", "is_system"]
        read_only_fields = ["id", "is_system"]


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
