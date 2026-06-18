from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Optional


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
