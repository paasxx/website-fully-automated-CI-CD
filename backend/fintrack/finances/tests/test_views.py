from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from finances.models import Transaction

User = get_user_model()

TRANSACTIONS_URL      = "/api/finances/transactions/"
SPENDING_OVER_TIME_URL = "/api/finances/spending-over-time/"


def _tx(user, **kwargs):
    defaults = dict(
        date=date(2026, 5, 1),
        description="Test",
        amount=Decimal("100.00"),
        bank="nubank",
        is_credit=False,
    )
    defaults.update(kwargs)
    return Transaction.objects.create(user=user, **defaults)


class TestTransactionListView(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="test@example.com", email="test@example.com", password="pass123")

    def test_requires_auth(self):
        resp = self.client.get(TRANSACTIONS_URL)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_returns_only_user_transactions(self):
        other = User.objects.create_user(username="other@example.com", email="other@example.com", password="pass123")
        _tx(self.user, description="Mine")
        _tx(other, description="Not mine")

        self.client.force_authenticate(self.user)
        resp = self.client.get(TRANSACTIONS_URL)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["results"][0]["description"], "Mine")

    def test_paginated_response_shape(self):
        self.client.force_authenticate(self.user)
        resp = self.client.get(TRANSACTIONS_URL)
        for key in ("count", "results", "next", "previous"):
            self.assertIn(key, resp.data)

    def test_empty_when_no_transactions(self):
        self.client.force_authenticate(self.user)
        resp = self.client.get(TRANSACTIONS_URL)
        self.assertEqual(resp.data["count"], 0)
        self.assertEqual(resp.data["results"], [])

    def test_search_filter(self):
        _tx(self.user, description="Netflix")
        _tx(self.user, description="Spotify")

        self.client.force_authenticate(self.user)
        resp = self.client.get(TRANSACTIONS_URL, {"search": "netflix"})
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["results"][0]["description"], "Netflix")

    def test_bank_filter(self):
        _tx(self.user, bank="nubank")
        _tx(self.user, bank="inter")

        self.client.force_authenticate(self.user)
        resp = self.client.get(TRANSACTIONS_URL, {"bank": "nubank"})
        self.assertEqual(resp.data["count"], 1)

    def test_date_range_filter(self):
        _tx(self.user, date=date(2026, 4, 1))   # before
        _tx(self.user, date=date(2026, 5, 15))  # inside
        _tx(self.user, date=date(2026, 6, 1))   # after

        self.client.force_authenticate(self.user)
        resp = self.client.get(TRANSACTIONS_URL, {
            "date_from": "2026-05-01", "date_to": "2026-05-31"
        })
        self.assertEqual(resp.data["count"], 1)

    def test_page_param(self):
        # Create 30 transactions (page_size=25) and verify page 2 returns the rest
        for i in range(30):
            _tx(self.user, description=f"TX {i:02d}")

        self.client.force_authenticate(self.user)
        resp_p1 = self.client.get(TRANSACTIONS_URL, {"page": 1})
        resp_p2 = self.client.get(TRANSACTIONS_URL, {"page": 2})

        self.assertEqual(resp_p1.data["count"], 30)
        self.assertEqual(len(resp_p1.data["results"]), 25)
        self.assertEqual(len(resp_p2.data["results"]), 5)

    def test_transaction_response_fields(self):
        _tx(self.user, is_installment=True, installment_number=2, installment_total=6)

        self.client.force_authenticate(self.user)
        resp = self.client.get(TRANSACTIONS_URL)
        item = resp.data["results"][0]
        # category_name is omitted by the serializer when category is None (SkipField behaviour)
        for field in ("id", "date", "description", "amount", "bank",
                      "is_credit", "is_installment", "installment_number",
                      "installment_total", "category"):
            self.assertIn(field, item)


class TestSpendingOverTimeView(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="test@example.com", email="test@example.com", password="pass123")

    def test_requires_auth(self):
        resp = self.client.get(SPENDING_OVER_TIME_URL)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_aggregates_expenses_by_month_and_bank(self):
        _tx(self.user, date=date(2026, 5, 1),  amount=Decimal("100.00"), bank="nubank")
        _tx(self.user, date=date(2026, 5, 15), amount=Decimal("50.00"),  bank="nubank")
        _tx(self.user, date=date(2026, 5, 10), amount=Decimal("200.00"), bank="inter")

        self.client.force_authenticate(self.user)
        resp = self.client.get(SPENDING_OVER_TIME_URL)
        self.assertEqual(resp.status_code, 200)

        data = resp.data["data"]
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["month"], "2026-05")
        self.assertAlmostEqual(float(data[0]["nubank"]), 150.0)
        self.assertAlmostEqual(float(data[0]["inter"]), 200.0)

    def test_excludes_credit_transactions(self):
        _tx(self.user, amount=Decimal("100.00"), is_credit=False)
        _tx(self.user, amount=Decimal("500.00"), is_credit=True)  # payment — must be excluded

        self.client.force_authenticate(self.user)
        resp = self.client.get(SPENDING_OVER_TIME_URL)
        data = resp.data["data"]
        self.assertAlmostEqual(float(data[0]["nubank"]), 100.0)

    def test_scoped_to_current_user(self):
        other = User.objects.create_user(username="other@example.com", email="other@example.com", password="pass123")
        _tx(other, amount=Decimal("9999.00"), bank="nubank")

        self.client.force_authenticate(self.user)
        resp = self.client.get(SPENDING_OVER_TIME_URL)
        self.assertEqual(resp.data["data"], [])

    def test_multiple_months_ordered(self):
        _tx(self.user, date=date(2026, 4, 1), amount=Decimal("100.00"), bank="nubank")
        _tx(self.user, date=date(2026, 5, 1), amount=Decimal("200.00"), bank="nubank")

        self.client.force_authenticate(self.user)
        resp = self.client.get(SPENDING_OVER_TIME_URL)
        months = [d["month"] for d in resp.data["data"]]
        self.assertEqual(months, ["2026-04", "2026-05"])

    def test_response_includes_banks_list(self):
        _tx(self.user, bank="nubank")
        _tx(self.user, bank="inter")

        self.client.force_authenticate(self.user)
        resp = self.client.get(SPENDING_OVER_TIME_URL)
        self.assertIn("banks", resp.data)
        self.assertIn("nubank", resp.data["banks"])
        self.assertIn("inter", resp.data["banks"])

    def test_empty_when_no_transactions(self):
        self.client.force_authenticate(self.user)
        resp = self.client.get(SPENDING_OVER_TIME_URL)
        self.assertEqual(resp.data["data"], [])
