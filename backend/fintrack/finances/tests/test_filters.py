from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from finances.filters import TransactionFilter
from finances.models import Transaction

User = get_user_model()


def _tx(user, **kwargs):
    defaults = dict(
        date=date(2026, 5, 1),
        description="Generic Transaction",
        amount=Decimal("100.00"),
        bank="nubank",
        is_credit=False,
    )
    defaults.update(kwargs)
    return Transaction.objects.create(user=user, **defaults)


class TestTransactionFilter(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="test@example.com", email="test@example.com", password="pass123")

    def _filter(self, **params):
        qs = Transaction.objects.filter(user=self.user)
        return TransactionFilter(params, queryset=qs).qs

    # ── search (icontains on description) ─────────────────────────────────────

    def test_search_matches_substring(self):
        _tx(self.user, description="Amazon Marketplace")
        _tx(self.user, description="Ifood")
        self.assertEqual(self._filter(search="amazon").count(), 1)

    def test_search_case_insensitive(self):
        _tx(self.user, description="NETFLIX")
        self.assertEqual(self._filter(search="netflix").count(), 1)
        self.assertEqual(self._filter(search="NETFLIX").count(), 1)

    def test_search_partial_match(self):
        _tx(self.user, description="Amazon Prime Video")
        self.assertEqual(self._filter(search="prime").count(), 1)

    def test_search_no_match_returns_empty(self):
        _tx(self.user, description="Spotify")
        self.assertEqual(self._filter(search="netflix").count(), 0)

    # ── date range ────────────────────────────────────────────────────────────

    def test_date_from_inclusive(self):
        _tx(self.user, date=date(2026, 4, 30))
        _tx(self.user, date=date(2026, 5, 1))
        self.assertEqual(self._filter(date_from="2026-05-01").count(), 1)

    def test_date_to_inclusive(self):
        _tx(self.user, date=date(2026, 5, 31))
        _tx(self.user, date=date(2026, 6, 1))
        self.assertEqual(self._filter(date_to="2026-05-31").count(), 1)

    def test_date_range_excludes_outside(self):
        _tx(self.user, date=date(2026, 4, 30))  # before
        _tx(self.user, date=date(2026, 5, 15))  # inside
        _tx(self.user, date=date(2026, 6, 1))   # after
        self.assertEqual(
            self._filter(date_from="2026-05-01", date_to="2026-05-31").count(), 1
        )

    # ── bank ─────────────────────────────────────────────────────────────────

    def test_bank_exact_match(self):
        _tx(self.user, bank="nubank")
        _tx(self.user, bank="inter")
        _tx(self.user, bank="btg")
        self.assertEqual(self._filter(bank="nubank").count(), 1)

    def test_bank_filter_returns_correct_bank(self):
        _tx(self.user, bank="inter")
        result = self._filter(bank="inter")
        self.assertEqual(result.first().bank, "inter")

    # ── is_credit ─────────────────────────────────────────────────────────────

    def test_is_credit_true(self):
        _tx(self.user, is_credit=True)
        _tx(self.user, is_credit=False)
        result = self._filter(is_credit="true")
        self.assertEqual(result.count(), 1)
        self.assertTrue(result.first().is_credit)

    def test_is_credit_false(self):
        _tx(self.user, is_credit=True)
        _tx(self.user, is_credit=False)
        result = self._filter(is_credit="false")
        self.assertEqual(result.count(), 1)
        self.assertFalse(result.first().is_credit)

    # ── no filters ────────────────────────────────────────────────────────────

    def test_no_filters_returns_all(self):
        _tx(self.user)
        _tx(self.user, description="Another")
        self.assertEqual(self._filter().count(), 2)

    def test_combined_filters(self):
        _tx(self.user, description="Amazon", bank="nubank", date=date(2026, 5, 10))
        _tx(self.user, description="Amazon", bank="inter",  date=date(2026, 5, 10))
        _tx(self.user, description="Spotify", bank="nubank", date=date(2026, 5, 10))
        # search + bank together
        self.assertEqual(self._filter(search="amazon", bank="nubank").count(), 1)
