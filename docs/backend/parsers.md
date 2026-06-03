# Statement Parsers

## How it works

Each bank statement has a different CSV format. The parser system isolates all bank-specific logic so the rest of the application is completely unaware of format differences.

```
CSV file (any bank)
        ↓
  StatementParser (per bank)
        ↓
  list[TransactionDTO]   ← normalized, bank-agnostic
        ↓
  process_statement()    ← saves to DB
        ↓
  Transaction rows (same schema for all banks)
```

---

## Files

```
statements/parsers/
├── __init__.py
├── base.py       ← StatementParser (ABC) + TransactionDTO
├── nubank.py     ← NubankParser
└── registry.py   ← maps "nubank" → NubankParser()
```

---

## `TransactionDTO`

The normalized data contract. All parsers output this:

```python
@dataclass
class TransactionDTO:
    # Required — all banks have these
    date: date
    description: str
    amount: Decimal
    bank: str
    is_credit: bool

    # Installment — Nubank, Inter (parsed from description)
    is_installment: bool = False
    installment_number: Optional[int] = None
    installment_total: Optional[int] = None

    # Bank-specific nullable — not all banks provide these
    balance_after: Optional[Decimal] = None   # Inter, BTG
    bank_category: Optional[str] = None       # BTG
    transaction_type: Optional[str] = None    # Inter: PIX, TED, DOC
```

---

## Nubank CSV format

```csv
date,title,amount
2026-05-29,DAKI - NuPay,118.81
2026-05-25,Pagamento recebido,-4801.32
2026-05-20,Amazon Marketplace - Parcela 8/10,54.77
```

- Separator: `,`
- Date format: `YYYY-MM-DD`
- Negative amount = credit (payment received)
- Installments: `"- Parcela N/M"` suffix in title, removed from description
- Encoding: UTF-8

**Installment regex:**
```python
INSTALLMENT_RE = re.compile(r"\s*-\s*Parcela\s+(\d+)/(\d+)\s*$", re.IGNORECASE)
```

---

## Adding a new bank

1. Create `statements/parsers/mybank.py`:

```python
from .base import StatementParser, TransactionDTO
import csv
from io import TextIOWrapper
from decimal import Decimal
from datetime import datetime

class MyBankParser(StatementParser):
    BANK = "mybank"
    REQUIRED_HEADERS = {"Data", "Historico", "Valor"}

    @classmethod
    def detect(cls, headers: set) -> bool:
        return cls.REQUIRED_HEADERS.issubset(headers)

    def parse(self, file) -> list[TransactionDTO]:
        reader = csv.DictReader(TextIOWrapper(file, encoding="utf-8"))
        transactions = []

        for row in reader:
            amount = Decimal(row["Valor"].replace(",", "."))
            date = datetime.strptime(row["Data"], "%d/%m/%Y").date()

            transactions.append(TransactionDTO(
                date=date,
                description=row["Historico"].strip(),
                amount=amount,
                bank=self.BANK,
                is_credit=amount > 0,
            ))

        return transactions
```

2. Register in `statements/parsers/registry.py`:

```python
from .mybank import MyBankParser

_PARSERS = {
    "nubank": NubankParser(),
    "mybank": MyBankParser(),  # ← add here
}
```

3. Add to `Statement.BANK_CHOICES` in `statements/models.py`:

```python
BANK_CHOICES = [
    ("nubank", "Nubank"),
    ("inter", "Inter"),
    ("btg", "BTG"),
    ("mybank", "My Bank"),  # ← add here
]
```

4. Add to `UploadCard.jsx` frontend BANKS array.

5. Run `make migrate` (BANK_CHOICES change doesn't require migration, but good practice to check).

Nothing else changes. Views, services, and models are completely bank-agnostic.
