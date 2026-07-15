from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Optional


def parse_amount(raw: str) -> Optional[Decimal]:
    """Parse a bank money string into a Decimal, or None if unparseable.

    Handles the Brazilian format that Nubank/Inter exports actually use:

        "1.234,56"  → 1234.56   (dot = thousands, comma = decimal)
        "- 5,17"    → -5.17      (space between sign and digits)
        "R$ 87,61"  → 87.61

    A plain dotted decimal ("118.81") is left as-is, so older US-format Nubank
    invoices keep working. Does NOT handle the US thousands format ("1,234.56")
    — these banks never emit it. Returns None on anything unparseable so callers
    can skip/aggregate instead of crashing mid-row.
    """
    if raw is None:
        return None
    cleaned = raw.replace("R$", "").replace("\xa0", "").replace(" ", "")
    if "," in cleaned:                                   # Brazilian decimal
        cleaned = cleaned.replace(".", "").replace(",", ".")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


@dataclass
class TransactionDTO:
    """Normalized transaction data — bank-agnostic. All parsers output this."""

    date: date
    description: str
    amount: Decimal
    bank: str
    is_credit: bool

    # Installment fields — populated when parser detects "Parcela N/M" patterns
    is_installment: bool = False
    installment_number: Optional[int] = None
    installment_total: Optional[int] = None

    # Bank-specific nullable fields
    balance_after: Optional[Decimal] = None     # Inter, BTG
    bank_category: Optional[str] = None         # BTG native category
    transaction_type: Optional[str] = None      # Inter: PIX, TED, etc.


class StatementParser(ABC):
    BANK: str = ""

    @abstractmethod
    def parse(self, file, password=None) -> list[TransactionDTO]:
        """Parse a file object and return a list of TransactionDTOs."""
        ...

    @classmethod
    @abstractmethod
    def detect(cls, headers: set) -> bool:
        """Return True if the given CSV headers match this bank's format."""
        ...
