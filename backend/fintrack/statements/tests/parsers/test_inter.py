from datetime import date
from decimal import Decimal

from django.test import SimpleTestCase

from statements.parsers.inter import InterParser, _parse_br_decimal

# ── Helpers ───────────────────────────────────────────────────────────────────

def _table(*rows):
    """Wrap raw strings in single-element lists (single-column pdfplumber table)."""
    return [[r] for r in rows]


class TestParseBrDecimal(SimpleTestCase):
    def test_simple_comma_decimal(self):
        self.assertEqual(_parse_br_decimal("99,90"), Decimal("99.90"))

    def test_thousands_dot_separator(self):
        self.assertEqual(_parse_br_decimal("1.234,56"), Decimal("1234.56"))

    def test_strips_real_sign(self):
        self.assertEqual(_parse_br_decimal("R$ 134,58"), Decimal("134.58"))

    def test_strips_non_breaking_space(self):
        self.assertEqual(_parse_br_decimal("R$\xa0134,58"), Decimal("134.58"))

    def test_empty_string_returns_none(self):
        self.assertIsNone(_parse_br_decimal(""))

    def test_non_numeric_returns_none(self):
        self.assertIsNone(_parse_br_decimal("abc"))


class TestInterDetect(SimpleTestCase):
    def test_always_false(self):
        # InterParser is a PDF — bank is identified by the upload field, not headers
        self.assertFalse(InterParser.detect(set()))
        self.assertFalse(InterParser.detect({"date", "title", "amount"}))


class TestInterParseTable(SimpleTestCase):
    def setUp(self):
        self.parser = InterParser()

    def test_expense_row(self):
        result = self.parser._parse_table(_table(
            "08 de fev. 2026 MERCADO LIVRE - R$ 99,90"
        ))
        self.assertEqual(len(result), 1)
        tx = result[0]
        self.assertEqual(tx.date, date(2026, 2, 8))
        self.assertEqual(tx.description, "MERCADO LIVRE")
        self.assertEqual(tx.amount, Decimal("99.90"))
        self.assertFalse(tx.is_credit)
        self.assertEqual(tx.bank, "inter")

    def test_credit_row_plus_prefix(self):
        # "+" before R$ marks a payment/refund (credit)
        result = self.parser._parse_table(_table(
            "05 de mai. 2026 PAGAMENTO ON LINE - + R$ 134,58"
        ))
        self.assertEqual(len(result), 1)
        tx = result[0]
        self.assertEqual(tx.date, date(2026, 5, 5))
        self.assertTrue(tx.is_credit)
        self.assertEqual(tx.amount, Decimal("134.58"))

    def test_installment_date_shifted(self):
        # Purchase date 2026-02-08, installment 4 of 10.
        # billing_date = 2026-02-08 + 3 months = 2026-05-08
        result = self.parser._parse_table(_table(
            "08 de fev. 2026 CP PARC SHOPPING INTER (Parcela 04 de 10) - R$ 134,58"
        ))
        self.assertEqual(len(result), 1)
        tx = result[0]
        self.assertEqual(tx.date, date(2026, 5, 8))
        self.assertTrue(tx.is_installment)
        self.assertEqual(tx.installment_number, 4)
        self.assertEqual(tx.installment_total, 10)
        self.assertEqual(tx.description, "CP PARC SHOPPING INTER")

    def test_installment_1_date_unchanged(self):
        # First installment: +0 months, date stays the same as purchase
        result = self.parser._parse_table(_table(
            "10 de jan. 2026 LOJA XPTO (Parcela 01 de 06) - R$ 50,00"
        ))
        self.assertEqual(result[0].date, date(2026, 1, 10))

    def test_installment_description_cleaned(self):
        result = self.parser._parse_table(_table(
            "01 de mar. 2026 NETFLIX (Parcela 02 de 12) - R$ 20,90"
        ))
        self.assertEqual(result[0].description, "NETFLIX")
        self.assertNotIn("Parcela", result[0].description)

    def test_non_transaction_rows_skipped(self):
        result = self.parser._parse_table(_table(
            "Pagamento mínimo: R$ 20,19",
            "Encargos rotativos 12,90% am",
            "Despesas do mês R$ 134,58",
        ))
        self.assertEqual(len(result), 0)

    def test_none_cell_skipped(self):
        result = self.parser._parse_table([[None]])
        self.assertEqual(len(result), 0)

    def test_empty_table(self):
        result = self.parser._parse_table([])
        self.assertEqual(len(result), 0)

    def test_all_twelve_months(self):
        months = [
            ("jan", 1), ("fev", 2), ("mar", 3), ("abr", 4),
            ("mai", 5), ("jun", 6), ("jul", 7), ("ago", 8),
            ("set", 9), ("out", 10), ("nov", 11), ("dez", 12),
        ]
        for abbr, expected_month in months:
            result = self.parser._parse_table(_table(f"15 de {abbr}. 2026 TESTE - R$ 10,00"))
            self.assertEqual(len(result), 1, msg=f"Failed for month '{abbr}'")
            self.assertEqual(result[0].date.month, expected_month, msg=f"Wrong month for '{abbr}'")

    def test_month_without_dot(self):
        # Some rows may omit the period after the month abbreviation
        result = self.parser._parse_table(_table(
            "15 de jun 2026 SPOTIFY - R$ 21,90"
        ))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].date, date(2026, 6, 15))

    def test_mixed_table(self):
        result = self.parser._parse_table(_table(
            "Saldo total de compras parceladas R$ 134,58",  # skipped
            "08 de fev. 2026 MERCADO LIVRE - R$ 99,90",    # parsed
            "05 de mai. 2026 PAGAMENTO - + R$ 99,90",      # parsed
        ))
        self.assertEqual(len(result), 2)
