# Statement Parsers

## How it works

Each bank statement has a different format (CSV, XLSX, PDF). The parser system isolates all bank-specific logic so the rest of the application is completely unaware of format differences.

```
File (any bank/format)
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
├── nubank.py     ← NubankParser   (CSV)
├── inter.py      ← InterParser    (PDF)
├── btg.py        ← BTGParser      (XLSX encrypted)
└── registry.py   ← maps "nubank" / "inter" / "btg" → parser instance
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

    # Installment — Nubank, Inter, BTG (parsed from description or PDF layout)
    is_installment: bool = False
    installment_number: Optional[int] = None
    installment_total: Optional[int] = None

    # Bank-specific nullable — not all banks provide these
    balance_after: Optional[Decimal] = None   # Inter (not used)
    bank_category: Optional[str] = None       # BTG native category
    transaction_type: Optional[str] = None    # BTG: "Parcela sem juros", "Compra à vista", etc.
```

---

## Nubank — CSV, separator `,`, UTF-8

```csv
date,title,amount
2026-05-29,DAKI - NuPay,118.81
2026-05-25,Pagamento recebido,-4801.32
2026-05-20,Amazon Marketplace - Parcela 8/10,54.77
```

- Date format: `YYYY-MM-DD` (already the billing date — no shift needed)
- Negative amount = credit (payment received)
- Installments: `"- Parcela N/M"` suffix in title, stripped from description

```python
REQUIRED_HEADERS = {"date", "title", "amount"}

def detect(cls, headers):
    return cls.REQUIRED_HEADERS.issubset(headers)
```

---

## Inter — PDF, password = first 6 CPF digits

Inter exports its statement as a password-protected PDF. The parser uses `pdfplumber` to extract tables.

**Layout:** single-column — each transaction is one concatenated string per row:

```
"08 de fev. 2026 CP PARC SHOPPING INTER (Parcela 04 de 10) - R$ 134,58"
"05 de mai. 2026 PAGAMENTO ON LINE - + R$ 134,58"
```

Parsing rules:
- Date: `DD de MMM. YYYY` (Portuguese month abbreviation)
- Separator: `" - "` between description and amount
- `"+"` before `R$` = credit (payment / refund); absence = debit (expense)
- Installments: `(Parcela N de M)` pattern, stripped from description
- `detect()` always returns `False` — bank is identified by the `bank` field in the upload request

**Non-transaction tables** (rates, boleto, summaries) contain no `DD de MMM.` date — the regex produces no match, so those rows are silently skipped.

### Installment date normalization (same as BTG)

The date in the PDF is the **purchase date**, not the billing month. The parser shifts:

```python
billing_date = purchase_date + relativedelta(months=installment_number - 1)
# Parcela 04 de 10, purchase 2026-02-08 → billing 2026-05-08  ✓
```

---

## BTG — XLSX encrypted, password = CPF without punctuation

BTG exports its fatura as a `.xlsx` file encrypted with the account holder's CPF (digits only).

Steps in the parser:
1. Read raw bytes into `io.BytesIO`
2. If `password` provided: decrypt with `msoffcrypto`, then read with `openpyxl`
3. Locate the header row **dynamically** (finds the row where `col[1]=="Data"` and `col[2]=="Descrição"`) — needed because the first ~24 rows are a fatura summary
4. Iterate transaction rows: `col[1]=date`, `col[2]=description`, `col[4]=amount`, `col[5]=transaction_type`
5. Installments detected by regex `(N/M)` in description
6. **Installment date normalization** (see below)

`detect()` always returns `False` — BTG is never identified by CSV headers.

**Dependencies:** `msoffcrypto-tool`, `openpyxl`, `python-dateutil`

### Installment date normalization (same as Inter)

**Problem:** BTG lists all N installments of a purchase with the original purchase date. Nubank reports each installment on its actual billing month. Without normalization, a 3x purchase in April would show all R$600 in April on the chart instead of R$200/month.

**Solution:** shift each installment by `(installment_number - 1)` months:

```python
billing_date = purchase_date + relativedelta(months=installment_number - 1)
# (1/3) → +0 months → April    ✓
# (2/3) → +1 month  → May      ✓
# (3/3) → +2 months → June     ✓
```

`relativedelta` handles month-end edge cases: Jan 31 + 1 month = Feb 28.

**Warning:** this logic assumes BTG exports all N installments with the purchase date in a single statement. If BTG ever changes to report only the current month's installment (like Nubank), the normalization would double-shift an already-correct date. Validate with future statements.

---

## Registry

```python
# statements/parsers/registry.py
_PARSERS = {
    "nubank": NubankParser(),
    "inter":  InterParser(),
    "btg":    BTGParser(),
}

def get_parser(bank: str) -> StatementParser:
    parser = _PARSERS.get(bank)
    if not parser:
        raise ValueError(f"No parser registered for bank: '{bank}'")
    return parser
```

---

## Adding a new bank

### CSV bank

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

    def parse(self, file, password=None) -> list[TransactionDTO]:
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

### PDF bank (like Inter)

1. Create `statements/parsers/mybank.py` using `pdfplumber`
2. `detect()` must return `False` — PDF banks are always identified manually
3. `parse(self, file, password=None)` receives the file object and optional password

### After creating the parser

2. Register in `statements/parsers/registry.py`:
```python
from .mybank import MyBankParser
_PARSERS["mybank"] = MyBankParser()
```

3. Add to `Statement.BANK_CHOICES` in `statements/models.py`

4. If password-protected: add to `BANK_PASSWORD_CONFIG` in `UploadCard.jsx`

5. Add bank option to the `<select>` in `UploadCard.jsx`

Nothing else changes. Views, services, and models are completely bank-agnostic.
