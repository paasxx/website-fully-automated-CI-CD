import io
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from finances.models import Transaction
from statements.models import Statement
from statements.parsers.base import TransactionDTO
from statements.services import process_statement

User = get_user_model()


def _dto(**kwargs):
    defaults = dict(
        date=date(2026, 5, 1),
        description="Test Transaction",
        amount=Decimal("100.00"),
        bank="nubank",
        is_credit=False,
    )
    defaults.update(kwargs)
    return TransactionDTO(**defaults)


class TestProcessStatement(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="test@example.com", email="test@example.com", password="pass123")
        self.fake_file = io.BytesIO(b"fake content")

    # ── Duplicate detection ────────────────────────────────────────────────────

    def test_duplicate_filename_raises_value_error(self):
        Statement.objects.create(user=self.user, bank="nubank", filename="fatura.csv", status="processed")
        with self.assertRaises(ValueError) as ctx:
            process_statement(self.user, self.fake_file, "fatura.csv", "nubank")
        self.assertIn("fatura.csv", str(ctx.exception))

    def test_duplicate_check_is_user_scoped(self):
        # Same filename for a different user must not block this user
        other = User.objects.create_user(username="other@example.com", email="other@example.com", password="pass123")
        Statement.objects.create(user=other, bank="nubank", filename="fatura.csv", status="processed")
        with patch("statements.services.get_parser") as mock:
            mock.return_value.parse.return_value = []
            # Should not raise
            process_statement(self.user, self.fake_file, "fatura.csv", "nubank")

    # ── Successful processing ──────────────────────────────────────────────────

    @patch("statements.services.get_parser")
    def test_success_creates_transactions(self, mock_get_parser):
        dtos = [_dto(description=f"TX {i}") for i in range(3)]
        mock_get_parser.return_value.parse.return_value = dtos

        stmt = process_statement(self.user, self.fake_file, "fatura.csv", "nubank")

        self.assertEqual(stmt.status, "processed")
        self.assertEqual(stmt.transaction_count, 3)
        self.assertEqual(Transaction.objects.filter(statement=stmt).count(), 3)

    @patch("statements.services.get_parser")
    def test_transactions_linked_to_user_and_statement(self, mock_get_parser):
        mock_get_parser.return_value.parse.return_value = [_dto()]

        stmt = process_statement(self.user, self.fake_file, "fatura.csv", "nubank")
        tx = Transaction.objects.get(statement=stmt)

        self.assertEqual(tx.user, self.user)
        self.assertEqual(tx.statement, stmt)

    @patch("statements.services.get_parser")
    def test_dto_fields_mapped_to_transaction(self, mock_get_parser):
        dto = _dto(
            date=date(2026, 5, 15),
            description="Netflix",
            amount=Decimal("22.90"),
            bank="nubank",
            is_credit=False,
            is_installment=True,
            installment_number=2,
            installment_total=6,
        )
        mock_get_parser.return_value.parse.return_value = [dto]

        stmt = process_statement(self.user, self.fake_file, "fatura.csv", "nubank")
        tx = Transaction.objects.get(statement=stmt)

        self.assertEqual(tx.date, date(2026, 5, 15))
        self.assertEqual(tx.description, "Netflix")
        self.assertEqual(tx.amount, Decimal("22.90"))
        self.assertTrue(tx.is_installment)
        self.assertEqual(tx.installment_number, 2)
        self.assertEqual(tx.installment_total, 6)

    @patch("statements.services.get_parser")
    def test_empty_statement_zero_count(self, mock_get_parser):
        mock_get_parser.return_value.parse.return_value = []

        stmt = process_statement(self.user, self.fake_file, "fatura.csv", "nubank")
        self.assertEqual(stmt.transaction_count, 0)
        self.assertEqual(stmt.status, "processed")

    @patch("statements.services.get_parser")
    def test_password_forwarded_to_parser(self, mock_get_parser):
        mock_parser = mock_get_parser.return_value
        mock_parser.parse.return_value = []

        process_statement(self.user, self.fake_file, "fatura.csv", "nubank", password="secret")
        mock_parser.parse.assert_called_once_with(self.fake_file, password="secret")

    # ── Failure handling ───────────────────────────────────────────────────────

    @patch("statements.services.get_parser")
    def test_parser_error_marks_statement_failed(self, mock_get_parser):
        mock_get_parser.return_value.parse.side_effect = RuntimeError("Parse exploded")

        with self.assertRaises(RuntimeError):
            process_statement(self.user, self.fake_file, "fatura.csv", "nubank")

        stmt = Statement.objects.get(user=self.user, filename="fatura.csv")
        self.assertEqual(stmt.status, "failed")

    @patch("statements.services.get_parser")
    def test_parser_error_reraises_exception(self, mock_get_parser):
        mock_get_parser.return_value.parse.side_effect = ValueError("Bad format")

        with self.assertRaises(ValueError, msg="Bad format"):
            process_statement(self.user, self.fake_file, "fatura.csv", "nubank")
