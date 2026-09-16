import csv
import re
from datetime import datetime
from io import TextIOWrapper

from .base import StatementParser, TransactionDTO, parse_amount

# Matches "- Parcela 2/6" or "- Parcela 2/6 " at end of title (case-insensitive)
INSTALLMENT_RE = re.compile(r"\s*-\s*Parcela\s+(\d+)/(\d+)\s*$", re.IGNORECASE)


class NubankParser(StatementParser):
    BANK = "nubank"
    REQUIRED_HEADERS = {"date", "title", "amount"}

    @classmethod
    def detect(cls, headers: set) -> bool:
        return cls.REQUIRED_HEADERS.issubset(headers)

    def parse(self, file, password=None) -> list[TransactionDTO]:
        reader = csv.DictReader(TextIOWrapper(file, encoding="utf-8"))

        # Validate the format BEFORE parsing. Without this, a wrong-format file
        # (e.g. a Nubank account statement — "extrato" — whose columns are
        # Data/Valor/Identificador/Descrição) blows up mid-loop with a raw
        # KeyError, which the upload view can only surface as an opaque 500.
        # Raising a ValueError here lets the view turn it into a clear 400.
        if not self.detect(set(reader.fieldnames or [])):
            raise ValueError(
                "This file doesn't look like a Nubank credit-card invoice "
                "(expected columns: date, title, amount). A Nubank account "
                "statement ('extrato da conta') has a different format and is not supported."
            )

        transactions = []
        skipped = 0

        for row in reader:
            title = row["title"].strip()
            raw_amount = row["amount"].strip()
            raw_date = row["date"].strip()

            amount = parse_amount(raw_amount)
            if amount is None:
                skipped += 1
                continue  # tolerate the odd malformed row (see fail-loud check below)

            date = datetime.strptime(raw_date, "%Y-%m-%d").date()

            # Parse installment suffix from description
            match = INSTALLMENT_RE.search(title)
            is_installment = bool(match)
            installment_number = int(match.group(1)) if match else None
            installment_total = int(match.group(2)) if match else None
            description = INSTALLMENT_RE.sub("", title).strip()

            transactions.append(
                TransactionDTO(
                    date=date,
                    description=description,
                    amount=amount,
                    bank=self.BANK,
                    is_credit=amount < 0,
                    is_installment=is_installment,
                    installment_number=installment_number,
                    installment_total=installment_total,
                )
            )

        # Fail loud instead of returning nothing: if the file had rows but none
        # parsed, the format is wrong (e.g. unrecognized amounts) — not just
        # noise. This is exactly what silently produced "0 transactions" before.
        if not transactions and skipped:
            raise ValueError(
                f"Could not parse any of the {skipped} rows — the amount format "
                "wasn't recognized. Is this really a Nubank credit-card invoice CSV?"
            )

        return transactions
