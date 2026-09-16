import io
from datetime import date
from decimal import Decimal

from django.test import SimpleTestCase

from statements.parsers.nubank import NubankParser

# ── Fixtures ──────────────────────────────────────────────────────────────────

CSV_SIMPLE = b"date,title,amount\n2026-05-29,DAKI - NuPay,118.81\n"
CSV_CREDIT = b"date,title,amount\n2026-05-25,Pagamento recebido,-4801.32\n"
CSV_INSTALLMENT = b"date,title,amount\n2026-05-20,Amazon Marketplace - Parcela 8/10,54.77\n"
CSV_MALFORMED = b"date,title,amount\n2026-05-20,Loja XYZ,not-a-number\n"
CSV_MIXED = (
    b"date,title,amount\n"
    b"2026-05-29,DAKI - NuPay,118.81\n"      # valid
    b"2026-05-20,Loja XYZ,not-a-number\n"    # malformed → skipped, valid row survives
)
CSV_MULTI = (
    b"date,title,amount\n"
    b"2026-05-29,DAKI - NuPay,118.81\n"
    b"2026-05-25,Pagamento recebido,-4801.32\n"
    b"2026-05-20,Amazon Marketplace - Parcela 8/10,54.77\n"
)
# Real Nubank invoice in BRAZILIAN number format (the format the export switched
# to): comma decimals, dot thousands, a space between the minus sign and digits,
# and quoted fields. The parser must handle this AND the older US format above.
CSV_BR = (
    'date,title,amount\n'
    '2026-04-13,Conectc*Pedrosilve,"150,00"\n'
    '2026-04-10,"Estorno de ""Amazon Marketplace"" (Amazon)","- 5,17"\n'
    '2026-03-26,Pagamento recebido,"- 2.675,73"\n'
    '2026-03-20,Amazon Marketplace Cc - Parcela 5/12,"289,81"\n'
).encode("utf-8")
# Nubank ACCOUNT statement ("extrato da conta") — a DIFFERENT export from the
# credit-card invoice: Portuguese columns, no "title"/"amount". Must be rejected.
CSV_ACCOUNT_STATEMENT = (
    "Data,Valor,Identificador,Descrição\n"
    "12/09/2025,831.94,68c49fb1-43dd,Transferência Recebida - Bruno\n"
).encode("utf-8")


class TestNubankDetect(SimpleTestCase):
    def test_exact_headers(self):
        self.assertTrue(NubankParser.detect({"date", "title", "amount"}))

    def test_superset_headers(self):
        self.assertTrue(NubankParser.detect({"date", "title", "amount", "category"}))

    def test_missing_one_header(self):
        self.assertFalse(NubankParser.detect({"date", "title"}))

    def test_empty_headers(self):
        self.assertFalse(NubankParser.detect(set()))

    def test_wrong_headers(self):
        self.assertFalse(NubankParser.detect({"Data", "Historico", "Valor"}))


class TestNubankParse(SimpleTestCase):
    def setUp(self):
        self.parser = NubankParser()

    def _parse(self, csv_bytes):
        return self.parser.parse(io.BytesIO(csv_bytes))

    def test_simple_expense(self):
        txs = self._parse(CSV_SIMPLE)
        self.assertEqual(len(txs), 1)
        tx = txs[0]
        self.assertEqual(tx.date, date(2026, 5, 29))
        self.assertEqual(tx.description, "DAKI - NuPay")
        self.assertEqual(tx.amount, Decimal("118.81"))
        self.assertEqual(tx.bank, "nubank")
        self.assertFalse(tx.is_credit)
        self.assertFalse(tx.is_installment)
        self.assertIsNone(tx.installment_number)
        self.assertIsNone(tx.installment_total)

    def test_credit_negative_amount(self):
        txs = self._parse(CSV_CREDIT)
        self.assertEqual(len(txs), 1)
        tx = txs[0]
        self.assertEqual(tx.amount, Decimal("-4801.32"))
        self.assertTrue(tx.is_credit)  # amount < 0 → credit

    def test_installment_detection(self):
        txs = self._parse(CSV_INSTALLMENT)
        self.assertEqual(len(txs), 1)
        tx = txs[0]
        self.assertEqual(tx.description, "Amazon Marketplace")
        self.assertTrue(tx.is_installment)
        self.assertEqual(tx.installment_number, 8)
        self.assertEqual(tx.installment_total, 10)

    def test_nubank_installment_date_not_shifted(self):
        # Nubank already reports the billing month date for each installment.
        # The parser must NOT apply any date shift.
        txs = self._parse(CSV_INSTALLMENT)
        self.assertEqual(txs[0].date, date(2026, 5, 20))

    def test_brazilian_amount_format(self):
        # Nubank invoices switched to BR number format ("150,00", "- 2.675,73");
        # the parser must handle both BR and the older US format ("118.81").
        txs = self._parse(CSV_BR)
        self.assertEqual(len(txs), 4)
        by_desc = {t.description: t for t in txs}

        self.assertEqual(by_desc["Conectc*Pedrosilve"].amount, Decimal("150.00"))
        # negative with internal space + thousands separator
        self.assertEqual(by_desc["Pagamento recebido"].amount, Decimal("-2675.73"))
        self.assertTrue(by_desc["Pagamento recebido"].is_credit)
        # refund (estorno): negative with space; embedded quotes preserved
        self.assertEqual(
            by_desc['Estorno de "Amazon Marketplace" (Amazon)'].amount,
            Decimal("-5.17"),
        )
        # installment suffix stripped, BR amount parsed
        amz = by_desc["Amazon Marketplace Cc"]
        self.assertEqual(amz.amount, Decimal("289.81"))
        self.assertEqual(amz.installment_number, 5)
        self.assertEqual(amz.installment_total, 12)

    def test_malformed_row_skipped_among_valid(self):
        # A bad row among good ones is tolerated (skipped); the good rows survive.
        txs = self._parse(CSV_MIXED)
        self.assertEqual(len(txs), 1)
        self.assertEqual(txs[0].description, "DAKI - NuPay")

    def test_all_rows_malformed_raises(self):
        # If EVERY row fails, that's a format problem, not noise — fail loud
        # instead of silently returning 0 transactions.
        with self.assertRaises(ValueError):
            self._parse(CSV_MALFORMED)

    def test_multiple_rows(self):
        txs = self._parse(CSV_MULTI)
        self.assertEqual(len(txs), 3)

    def test_empty_csv_header_only(self):
        txs = self._parse(b"date,title,amount\n")
        self.assertEqual(len(txs), 0)

    def test_description_cleaned_of_installment_suffix(self):
        csv = b"date,title,amount\n2026-05-01,Mercado Livre - Parcela 1/3,99.90\n"
        txs = self._parse(csv)
        self.assertEqual(txs[0].description, "Mercado Livre")
        self.assertNotIn("Parcela", txs[0].description)

    def test_password_arg_ignored(self):
        # NubankParser accepts password kwarg but ignores it (CSV needs no password)
        txs = self.parser.parse(io.BytesIO(CSV_SIMPLE), password="irrelevant")
        self.assertEqual(len(txs), 1)

    def test_account_statement_format_rejected(self):
        # Wrong format (account statement, not a credit-card invoice) must raise a
        # clear ValueError — which the upload view maps to a 400 — instead of a raw
        # KeyError that would surface as an opaque 500.
        with self.assertRaisesRegex(ValueError, "credit-card invoice"):
            self._parse(CSV_ACCOUNT_STATEMENT)
