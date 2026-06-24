import io
import re
from datetime import date as date_

import pdfplumber
from dateutil.relativedelta import relativedelta

from .base import StatementParser, TransactionDTO, parse_amount

# Portuguese month abbreviations → month number
_MONTH = {
    'jan': 1, 'fev': 2, 'mar': 3, 'abr': 4,
    'mai': 5, 'jun': 6, 'jul': 7, 'ago': 8,
    'set': 9, 'out': 10, 'nov': 11, 'dez': 12,
}

# Matches: "DD de MMM. YYYY  DESCRIPTION - [+] R$ AMOUNT"
# The " - " is Inter's visual separator between description and amount.
# An optional "+" before "R$" marks a credit (payment/refund).
_TX_RE = re.compile(
    r'^(\d{2})\s+de\s+(\w{3})\.?\s+(\d{4})\s+'  # date parts
    r'(.+?)'                                       # description (lazy)
    r'\s+-\s+'                                     # separator
    r'(\+?)\s*R\$\s*([\d.,]+)',                    # optional +, amount
    re.DOTALL,
)

# Matches installment annotations e.g. "(Parcela 04 de 10)"
_INST_RE = re.compile(r'\(Parcela\s+(\d+)\s+de\s+(\d+)\)', re.IGNORECASE)

# Amount parsing now lives in base.parse_amount (shared across parsers and
# robust to signed/spaced values). Kept under the old name for internal use
# and the existing test import.
_parse_br_decimal = parse_amount


class InterParser(StatementParser):
    BANK = "inter"

    @classmethod
    def detect(cls, headers: set) -> bool:
        return False  # Inter statements are PDFs — bank must be selected manually

    def parse(self, file, password=None) -> list[TransactionDTO]:
        raw = file.read()
        transactions = []

        with pdfplumber.open(io.BytesIO(raw), password=password or "") as pdf:
            for page in pdf.pages:
                for table in page.extract_tables():
                    transactions.extend(self._parse_table(table))

        return transactions

    def _parse_table(self, table: list[list]) -> list[TransactionDTO]:
        """Parse one pdfplumber table.

        Inter statements use a single-column layout where each transaction row
        is one concatenated string:

            "08 de fev. 2026 CP PARC SHOPPING INTER (Parcela 04 de 10) - R$ 134,58"
            "05 de mai. 2026 PAGAMENTO ON LINE - + R$ 134,58"

        The " - " is a visual separator. A "+" immediately after marks a credit
        (payment or refund); absence of "+" means debit (expense).

        Non-transaction tables (rates, payment slip, summaries) produce no
        _TX_RE matches and are silently skipped.
        """
        dtos = []
        for row in table:
            if not row or not row[0]:
                continue

            cell = str(row[0]).replace('\n', ' ').strip()
            m = _TX_RE.match(cell)
            if not m:
                continue

            day_s, month_s, year_s, desc, credit_sign, amount_s = m.groups()

            month_n = _MONTH.get(month_s.lower())
            if not month_n:
                continue

            try:
                tx_date = date_(int(year_s), month_n, int(day_s))
            except ValueError:
                continue

            amount = _parse_br_decimal(amount_s)
            if amount is None:
                continue

            inst = _INST_RE.search(desc)
            clean_desc = _INST_RE.sub('', desc).strip()

            inst_num = int(inst.group(1)) if inst else None
            inst_tot = int(inst.group(2)) if inst else None

            # Inter records the purchase date for every installment row.
            # Shift to the actual billing month: purchase + (installment_number - 1) months.
            # Non-installment transactions are already dated to their billing month.
            if inst_num is not None:
                billing_date = tx_date + relativedelta(months=inst_num - 1)
            else:
                billing_date = tx_date

            dtos.append(TransactionDTO(
                date=billing_date,
                description=clean_desc,
                amount=amount,
                bank=self.BANK,
                is_credit=bool(credit_sign),  # "+" = payment/refund; absence = expense
                is_installment=bool(inst),
                installment_number=inst_num,
                installment_total=inst_tot,
                balance_after=None,
            ))

        return dtos
