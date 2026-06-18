import io
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

import pdfplumber

from .base import StatementParser, TransactionDTO

# Matches installment patterns in Inter descriptions, e.g. "Parcela 2/6"
INSTALLMENT_RE = re.compile(r"Parcela\s+(\d+)\s*/\s*(\d+)", re.IGNORECASE)


def _parse_br_decimal(value_str: str) -> Optional[Decimal]:
    """Convert Brazilian decimal format to Decimal.

    Inter uses "1.234,56" (dot=thousands, comma=decimal).
    Strips R$, spaces, and sign — caller decides is_credit from context.
    Returns None if the string is not a valid number.
    """
    if not value_str:
        return None
    cleaned = (
        value_str
        .replace("R$", "")
        .replace("\xa0", "")   # non-breaking space
        .replace(".", "")      # remove thousands separator
        .replace(",", ".")     # decimal comma → dot
        .strip()
    )
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


class InterParser(StatementParser):
    BANK = "inter"

    @classmethod
    def detect(cls, headers: set) -> bool:
        # Inter statements are PDFs — never detected by CSV headers.
        # Identified purely by the bank field sent in the upload request.
        return False

    def parse(self, file, password=None) -> list[TransactionDTO]:
        raw = file.read()
        transactions = []

        # pdfplumber accepts password as a string; empty string = no password attempt.
        with pdfplumber.open(io.BytesIO(raw), password=password or "") as pdf:
            for page in pdf.pages:
                for table in page.extract_tables():
                    transactions.extend(self._parse_table(table))

        return transactions

    def _parse_table(self, table: list[list]) -> list[TransactionDTO]:
        """Parse one table extracted by pdfplumber.

        IMPORTANT — column mapping must be verified against a real Inter PDF.
        Run the debug helper below and adjust COL_* constants accordingly.

        Assumed layout (adjust after inspection):
          COL_DATE  = 0   → "DD/MM/YYYY"
          COL_DESC  = 1   → description / merchant
          COL_VALUE = 2   → value (negative = debit, positive = credit in Inter)
          COL_BAL   = 3   → balance after transaction (optional)

        To debug: in the Django shell inside the container:
            from statements.parsers.inter import InterParser
            import pdfplumber, io
            with open("your_inter.pdf", "rb") as f:
                raw = f.read()
            with pdfplumber.open(io.BytesIO(raw), password="123456") as pdf:
                for i, page in enumerate(pdf.pages):
                    for j, table in enumerate(page.extract_tables()):
                        print(f"Page {i} Table {j}:", table[:5])
        """
        COL_DATE  = 0
        COL_DESC  = 1
        COL_VALUE = 2
        COL_BAL   = 3

        dtos = []
        for row in table:
            if not row or len(row) <= COL_VALUE:
                continue

            date_str  = (row[COL_DATE]  or "").strip()
            desc      = (row[COL_DESC]  or "").strip()
            value_str = (row[COL_VALUE] or "").strip()
            bal_str   = (row[COL_BAL]   or "").strip() if len(row) > COL_BAL else ""

            # Skip header rows (contain column names, not data)
            if not date_str or date_str.lower() in ("data", "date", ""):
                continue

            try:
                date = datetime.strptime(date_str, "%d/%m/%Y").date()
            except ValueError:
                continue  # not a valid date row — skip

            amount = _parse_br_decimal(value_str)
            if amount is None:
                continue

            match = INSTALLMENT_RE.search(desc)
            clean_desc = INSTALLMENT_RE.sub("", desc).strip()

            balance_after = _parse_br_decimal(bal_str)

            dtos.append(TransactionDTO(
                date=date,
                description=clean_desc,
                amount=amount,
                bank=self.BANK,
                # Inter convention: negative value = expense (debit card/pix out),
                # positive value = credit (deposit, pix in, refund).
                # VERIFY against a real statement — adjust if inverted.
                is_credit=amount > 0,
                is_installment=bool(match),
                installment_number=int(match.group(1)) if match else None,
                installment_total=int(match.group(2)) if match else None,
                balance_after=balance_after,
            ))

        return dtos
