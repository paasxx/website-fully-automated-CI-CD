# Backend Architecture

## Overview

The backend is a **Django 4.2 + Django REST Framework** API. It follows **Domain-Driven Design (DDD)** — each Django app owns a single domain. There is no business logic in views; views only handle HTTP concerns. All logic lives in `services.py`.

---

## Project Structure

```
backend/
├── Dockerfile.dev          # Dev: tail -f /dev/null (manual server start)
├── Dockerfile.prod         # Prod: gunicorn + nginx, entrypoint.sh
├── entrypoint.sh           # Prod startup: wait-for-db → migrate → gunicorn
├── nginx.conf              # Nginx config: proxies /api/ to gunicorn socket
├── requirements.txt        # Pinned dependencies
└── fintrack/               # Django project root
    ├── manage.py
    ├── fintrack/           # Project package (settings, urls, wsgi)
    │   ├── settings.py
    │   ├── urls.py
    │   └── wsgi.py
    ├── identity/           # Auth domain
    ├── finances/           # Finance domain
    └── statements/         # Statement import domain
```

---

## Domains

### `identity` — Authentication & User Profile

Owns everything related to who the user is.

| File | Responsibility |
|------|---------------|
| `models.py` | `User` (custom, email-based), `UserProfile` |
| `serializers.py` | `RegisterSerializer`, `UserSerializer`, `UserProfileSerializer` |
| `views.py` | `RegisterView`, `UserDetailView` |
| `urls.py` | `/api/auth/register/`, `/api/auth/token/`, `/api/auth/token/refresh/`, `/api/auth/me/` |

**Why a custom User model?**
Django's default `auth.User` uses `username` as the login field. We set `USERNAME_FIELD = "email"` so login is always by email. This must be done before the first migration — changing it after is a painful migration.

**UserProfile** is a separate model (OneToOne with User) instead of adding fields to User directly. This keeps the auth model focused on authentication. Profile fields (display_name, phone, timezone) can grow without touching auth logic.

---

### `finances` — Core Finance Domain

Owns transactions and categories. This is the heart of the product.

| File | Responsibility |
|------|---------------|
| `models.py` | `Category`, `Transaction` |
| `serializers.py` | `TransactionSerializer`, `CategorySerializer` |
| `views.py` | `TransactionListView`, `SpendingOverTimeView` |
| `urls.py` | `/api/finances/transactions/`, `/api/finances/spending-over-time/` |

#### `Transaction` model field design

Every bank provides: `date`, `description`, `amount`. These are always present.

Some banks provide extra fields — instead of JSONField, we use **nullable columns** for known fields:

| Field | Banks | Reason |
|-------|-------|--------|
| `is_credit` | all | derived from amount sign — semantic clarity |
| `is_installment` | Nubank, Inter | parsed from "- Parcela N/M" pattern |
| `installment_number` / `installment_total` | Nubank, Inter | installment position |
| `balance_after` | Inter, BTG | running balance after transaction |
| `bank_category` | BTG | bank's own category label |
| `transaction_type` | Inter | PIX, TED, DOC, etc. |

**Design decision:** nullable columns > JSONField for known fields. JSONField is harder to query, filter, and index. If a field is known at design time, give it a real column.

#### Indexes

Three composite indexes on `(user, ...)` because every query is always user-scoped:
- `(user, date DESC)` — default sort and date filters
- `(user, bank)` — filter by bank
- `(user, category)` — filter by category

#### `SpendingOverTimeView` — aggregation pattern

```python
Transaction.objects
    .filter(user=request.user, is_credit=False)
    .annotate(month=TruncMonth("date"))
    .values("month", "bank")
    .annotate(total=Sum("amount"))
    .order_by("month", "bank")
```

`TruncMonth` truncates the date to the first day of the month (GROUP BY month equivalent). The result is pivoted in Python to `{"month": "2026-05", "nubank": 3243.64, "inter": 800.00}` for the frontend.

---

### `statements` — Statement Import Domain

Owns the import pipeline: file upload → parsing → saving transactions.

| File | Responsibility |
|------|---------------|
| `models.py` | `Statement` (tracks each imported file) |
| `services.py` | `process_statement()` — orchestrates parse + save |
| `parsers/base.py` | `StatementParser` (ABC), `TransactionDTO` |
| `parsers/nubank.py` | `NubankParser` |
| `parsers/registry.py` | maps bank name → parser instance |
| `views.py` | `StatementUploadView`, `StatementListView` |
| `urls.py` | `/api/import/upload/`, `/api/import/` |

#### Parser pattern — Strategy + Registry

Adding a new bank requires **one new file** only:

```python
# statements/parsers/mybank.py
class MyBankParser(StatementParser):
    BANK = "mybank"

    @classmethod
    def detect(cls, headers: set) -> bool:
        return {"Data", "Valor", "Descricao"}.issubset(headers)

    def parse(self, file) -> list[TransactionDTO]:
        # read CSV, return list of TransactionDTO
        ...
```

```python
# statements/parsers/registry.py
from .mybank import MyBankParser

_PARSERS = {
    "nubank": NubankParser(),
    "mybank": MyBankParser(),  # ← add here
}
```

Nothing else changes. The `services.py`, `views.py`, `models.py` don't need to know about the new bank.

#### `TransactionDTO` — the normalized interface

The DTO is the contract between parsers and the database layer. All parsers output the same DTO regardless of CSV format. The service layer maps DTO → Transaction model.

#### Duplicate prevention

Two layers:
1. **Service check** (application layer): `if Statement.objects.filter(user=user, filename=filename).exists()` → raises `ValueError` before creating anything
2. **DB constraint** (database layer): `UniqueConstraint(fields=["user", "filename"])` → enforced at DB level even if service check is bypassed

---

## Authentication

JWT via `djangorestframework-simplejwt`.

- Access token: **1 hour** TTL
- Refresh token: **7 days** TTL, rotated on use
- Header: `Authorization: Bearer <access_token>`
- `DEFAULT_PERMISSION_CLASSES = [IsAuthenticated]` → every endpoint is protected by default; only `register` and `token` use `AllowAny`

---

## Security — current state

| Setting | Dev | Should be in Prod |
|---------|-----|-------------------|
| `SECRET_KEY` | insecure default | env var |
| `DEBUG` | True | False (env var) |
| `CORS_ALLOWED_ORIGINS` | localhost:3000 | prod domain |
| `ALLOWED_HOSTS` | `*` | prod domain |

All configurable via environment variables. No code change needed for prod — only `.env` or ECS task definition vars.

---

## Running locally

```bash
make migrate       # generates + applies migrations for all apps
make start-back    # starts Django runserver on port 8000
make shell-back    # bash inside the container
make createsuperuser
```

See `Makefile` at project root for all commands.
