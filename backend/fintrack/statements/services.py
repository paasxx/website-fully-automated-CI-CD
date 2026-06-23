from django.db import transaction as db_transaction
from finances.models import Transaction, Category
from finances.categorizer import categorize
from .models import Statement
from .parsers.registry import get_parser


def process_statement(user, file, filename: str, bank: str, password: str = None) -> Statement:
    existing = Statement.objects.filter(user=user, filename=filename).first()
    if existing:
        if existing.status != "failed":
            raise ValueError(f"'{filename}' já foi importado.")
        existing.delete()

    statement = Statement.objects.create(
        user=user,
        bank=bank,
        filename=filename,
        status="pending",
    )

    try:
        parser = get_parser(bank)
        dtos = parser.parse(file, password=password)

        categories = {c.name: c for c in Category.objects.filter(user=user)}

        rows = [
            Transaction(
                user=user,
                statement=statement,
                date=dto.date,
                description=dto.description,
                amount=dto.amount,
                bank=dto.bank,
                is_credit=dto.is_credit,
                is_installment=dto.is_installment,
                installment_number=dto.installment_number,
                installment_total=dto.installment_total,
                balance_after=dto.balance_after,
                bank_category=dto.bank_category,
                transaction_type=dto.transaction_type,
                category=categorize(dto.description, categories),
            )
            for dto in dtos
        ]

        with db_transaction.atomic():
            Transaction.objects.bulk_create(rows)
            statement.transaction_count = len(rows)
            statement.status = "processed"
            statement.save()

    except Exception:
        statement.status = "failed"
        statement.save()
        raise

    return statement
