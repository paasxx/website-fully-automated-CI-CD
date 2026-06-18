from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from django.test import TestCase

from statements.models import Statement

User = get_user_model()


class TestStatementModel(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="test@example.com", email="test@example.com", password="pass123")

    def _stmt(self, filename="fatura.csv", bank="nubank", status="processed"):
        return Statement.objects.create(user=self.user, bank=bank, filename=filename, status=status)

    def test_str_contains_bank_and_filename(self):
        stmt = self._stmt()
        self.assertIn("nubank", str(stmt))
        self.assertIn("fatura.csv", str(stmt))

    def test_default_status_is_pending(self):
        stmt = Statement.objects.create(user=self.user, bank="nubank", filename="f.csv")
        self.assertEqual(stmt.status, "pending")

    def test_unique_user_filename_constraint(self):
        self._stmt(filename="fatura.csv")
        with self.assertRaises(IntegrityError):
            self._stmt(filename="fatura.csv")

    def test_different_users_same_filename_allowed(self):
        user2 = User.objects.create_user(username="other@example.com", email="other@example.com", password="pass123")
        self._stmt(filename="fatura.csv")
        # Should not raise — different user, same filename is fine
        Statement.objects.create(user=user2, bank="nubank", filename="fatura.csv")

    def test_ordering_newest_first(self):
        stmt1 = self._stmt(filename="first.csv")
        stmt2 = self._stmt(filename="second.csv")
        stmts = list(Statement.objects.filter(user=self.user))
        # Most recently created should appear first
        self.assertEqual(stmts[0].pk, stmt2.pk)

    def test_default_transaction_count_zero(self):
        stmt = Statement.objects.create(user=self.user, bank="nubank", filename="f.csv")
        self.assertEqual(stmt.transaction_count, 0)
