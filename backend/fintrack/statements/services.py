from django.db import transaction as db_transaction
from finances.models import Transaction
from .models import Statement
from .parsers.registry import get_parser


def process_statement(user, file, filename: str, bank: str, password: str = None) -> Statement:
    if Statement.objects.filter(user=user, filename=filename).exists():
        raise ValueError(f"'{filename}' has already been imported.")

    statement = Statement.objects.create(
        user=user,
        bank=bank,
        filename=filename,
        status="pending",
    )

    try:
        parser = get_parser(bank)
        dtos = parser.parse(file, password=password)

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
