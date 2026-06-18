from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from django.test import TestCase

from finances.models import Category, Transaction

User = get_user_model()


class TestCategoryModel(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="test@example.com", email="test@example.com", password="pass123")

    def test_str_returns_name(self):
        cat = Category.objects.create(name="Food")
        self.assertEqual(str(cat), "Food")

    def test_system_category_has_no_user(self):
        cat = Category.objects.create(name="System Default")
        self.assertIsNone(cat.user)

    def test_user_category_unique_per_user(self):
        Category.objects.create(name="Food", user=self.user)
        with self.assertRaises(IntegrityError):
            Category.objects.create(name="Food", user=self.user)

    def test_same_name_different_users_allowed(self):
        user2 = User.objects.create_user(username="other@example.com", email="other@example.com", password="pass123")
        Category.objects.create(name="Food", user=self.user)
        # Should not raise
        Category.objects.create(name="Food", user=user2)

    def test_default_color(self):
        cat = Category.objects.create(name="Test")
        self.assertEqual(cat.color, "#4caf50")

    def test_ordering_by_name(self):
        Category.objects.create(name="Zzz")
        Category.objects.create(name="Aaa")
        names = list(Category.objects.values_list("name", flat=True))
        self.assertEqual(names[0], "Aaa")


class TestTransactionModel(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="test@example.com", email="test@example.com", password="pass123")

    def _tx(self, **kwargs):
        defaults = dict(
            user=self.user,
            date=date(2026, 5, 1),
            description="Test",
            amount=Decimal("100.00"),
            bank="nubank",
        )
        defaults.update(kwargs)
        return Transaction.objects.create(**defaults)

    def test_str_contains_date_description_amount(self):
        tx = self._tx(description="Netflix", amount=Decimal("22.90"))
        s = str(tx)
        self.assertIn("Netflix", s)
        self.assertIn("22.90", s)

    def test_defaults_are_false_and_null(self):
        tx = self._tx()
        self.assertFalse(tx.is_credit)
        self.assertFalse(tx.is_installment)
        self.assertIsNone(tx.installment_number)
        self.assertIsNone(tx.installment_total)
        self.assertIsNone(tx.balance_after)
        self.assertIsNone(tx.bank_category)
        self.assertIsNone(tx.transaction_type)
        self.assertIsNone(tx.category)

    def test_ordering_newest_first(self):
        tx1 = self._tx(date=date(2026, 4, 1))
        tx2 = self._tx(date=date(2026, 5, 1))
        txs = list(Transaction.objects.filter(user=self.user))
        self.assertEqual(txs[0].pk, tx2.pk)  # May before April

    def test_statement_nullable(self):
        tx = self._tx()
        self.assertIsNone(tx.statement)

    def test_bank_choices(self):
        for bank in ("nubank", "inter", "btg"):
            tx = self._tx(bank=bank)
            self.assertEqual(tx.bank, bank)
