import io
from datetime import date, datetime
from decimal import Decimal

import openpyxl
from django.test import SimpleTestCase

from statements.parsers.btg import BTGParser

# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_xlsx_bytes(*data_rows, include_header=True):
    """Build an in-memory BTG-style XLSX and return raw bytes.

    Column layout (0-indexed):
      0 → ignored
      1 → date (datetime object)
      2 → description (str)
      3 → ignored
      4 → amount (float)
      5 → transaction_type (str | None)
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    if include_header:
        ws.append([None, "Data", "Descrição", None, None, None])
    for row in data_rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _row(dt, description, amount, tx_type=None):
    return [None, dt, description, None, amount, tx_type]


class _FakeFile:
    def __init__(self, data):
        self._data = data

    def read(self):
        return self._data


class TestBTGDetect(SimpleTestCase):
    def test_always_false(self):
        # BTG is XLSX — bank is identified by the upload field, not CSV headers
        self.assertFalse(BTGParser.detect(set()))
        self.assertFalse(BTGParser.detect({"Data", "Descrição"}))


class TestBTGParse(SimpleTestCase):
    def setUp(self):
        self.parser = BTGParser()

    def _parse(self, *data_rows, **kwargs):
        data = _make_xlsx_bytes(*data_rows, **kwargs)
        return self.parser.parse(_FakeFile(data))

    def test_simple_expense(self):
        dt = datetime(2026, 5, 10)
        txs = self._parse(_row(dt, "Ifood", 50.0))
        self.assertEqual(len(txs), 1)
        tx = txs[0]
        self.assertEqual(tx.date, date(2026, 5, 10))
        self.assertEqual(tx.description, "Ifood")
        self.assertEqual(tx.amount, Decimal("50.0"))
        self.assertEqual(tx.bank, "btg")
        self.assertFalse(tx.is_credit)
        self.assertFalse(tx.is_installment)

    def test_credit_negative_amount(self):
        dt = datetime(2026, 5, 10)
        txs = self._parse(_row(dt, "Pagamento fatura", -500.0))
        self.assertEqual(len(txs), 1)
        self.assertTrue(txs[0].is_credit)  # amount < 0 → credit

    def test_installment_date_shifted(self):
        # Purchase 2026-01-15, installment 3 of 6.
        # billing_date = 2026-01-15 + 2 months = 2026-03-15
        dt = datetime(2026, 1, 15)
        txs = self._parse(_row(dt, "Netflix (3/6)", 30.0, "Parcela sem juros"))
        self.assertEqual(len(txs), 1)
        tx = txs[0]
        self.assertEqual(tx.date, date(2026, 3, 15))
        self.assertTrue(tx.is_installment)
        self.assertEqual(tx.installment_number, 3)
        self.assertEqual(tx.installment_total, 6)
        self.assertEqual(tx.description, "Netflix")

    def test_installment_1_date_unchanged(self):
        dt = datetime(2026, 4, 20)
        txs = self._parse(_row(dt, "Amazon (1/3)", 100.0))
        self.assertEqual(txs[0].date, date(2026, 4, 20))

    def test_installment_month_end_safe(self):
        # Jan 31 + 1 month via relativedelta = Feb 28 (not a crash)
        dt = datetime(2026, 1, 31)
        txs = self._parse(_row(dt, "Loja (2/3)", 10.0))
        self.assertEqual(txs[0].date, date(2026, 2, 28))

    def test_description_cleaned_of_installment_suffix(self):
        dt = datetime(2026, 5, 1)
        txs = self._parse(_row(dt, "Apple TV (2/12)", 15.0))
        self.assertEqual(txs[0].description, "Apple TV")
        self.assertNotIn("(2/12)", txs[0].description)

    def test_transaction_type_preserved(self):
        dt = datetime(2026, 5, 5)
        txs = self._parse(_row(dt, "Apple Store", 15.0, "Compra à vista"))
        self.assertEqual(txs[0].transaction_type, "Compra à vista")

    def test_transaction_type_none(self):
        dt = datetime(2026, 5, 5)
        txs = self._parse(_row(dt, "Spotify", 22.0))
        self.assertIsNone(txs[0].transaction_type)

    def test_skips_non_datetime_date_field(self):
        dt = datetime(2026, 5, 1)
        txs = self._parse(
            [None, "not-a-date", "Bad row", None, 50.0, None],
            _row(dt, "Good row", 10.0),
        )
        self.assertEqual(len(txs), 1)
        self.assertEqual(txs[0].description, "Good row")

    def test_no_header_raises_value_error(self):
        with self.assertRaises(ValueError):
            self._parse(include_header=False)

    def test_multiple_rows(self):
        dt = datetime(2026, 5, 1)
        txs = self._parse(
            _row(dt, "Netflix", 20.0),
            _row(dt, "Spotify", 22.0),
            _row(dt, "Amazon", 35.0),
        )
        self.assertEqual(len(txs), 3)

    def test_empty_xlsx_no_data_rows(self):
        txs = self._parse()
        self.assertEqual(len(txs), 0)
