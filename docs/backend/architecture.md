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
    ├── pytest.ini          # pytest-django config (DJANGO_SETTINGS_MODULE)
    ├── fintrack/           # Project package (settings, urls, wsgi)
    │   ├── settings.py
    │   ├── urls.py
    │   └── wsgi.py
    ├── identity/           # Auth domain
    │   └── tests/          # Unit tests for identity app
    ├── finances/           # Finance domain
    │   └── tests/          # Unit tests for finances app
    └── statements/         # Statement import domain
        └── tests/          # Unit tests for statements + parsers
            └── parsers/    # Parser-specific unit tests
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

`username` field is kept in the model (inherited from `AbstractUser`) and set to the email value on registration, so Django internals that depend on `username` continue to work.

**UserProfile** is a separate model (OneToOne with User) instead of adding fields to User directly. Profile fields (display_name, phone, timezone) can grow without touching auth logic.

---

### `finances` — Core Finance Domain

Owns transactions and categories. This is the heart of the product.

| File | Responsibility |
|------|---------------|
| `models.py` | `Category`, `Transaction` |
| `serializers.py` | `TransactionSerializer`, `CategorySerializer` |
| `filters.py` | `TransactionFilter` — search, date range, bank, is_credit, is_installment |
| `pagination.py` | `TransactionPagePagination` — page_size=25, max=200 |
| `views.py` | `TransactionListView`, `SpendingOverTimeView` |
| `urls.py` | `/api/finances/transactions/`, `/api/finances/spending-over-time/` |

#### `Transaction` model field design

Every bank provides: `date`, `description`, `amount`. These are always present.

Some banks provide extra fields — instead of JSONField, we use **nullable columns** for known fields:

| Field | Banks | Reason |
|-------|-------|--------|
| `is_credit` | all | derived from amount sign — semantic clarity |
| `is_installment` | Nubank, Inter, BTG | parsed from description pattern |
| `installment_number` / `installment_total` | Nubank, Inter, BTG | installment position |
| `balance_after` | Inter (unused for now) | running balance after transaction |
| `bank_category` | BTG | bank's own category label |
| `transaction_type` | BTG | "Parcela sem juros", "Compra à vista", etc. |

**Design decision:** nullable columns > JSONField for known fields. JSONField is harder to query, filter, and index. If a field is known at design time, give it a real column.

#### Indexes

Three composite indexes on `(user, ...)` because every query is always user-scoped:
- `(user, date DESC)` — default sort and date filters
- `(user, bank)` — filter by bank
- `(user, category)` — filter by category

#### Filtering — `TransactionFilter`

Uses `django-filter` (`DjangoFilterBackend`). Available params:

| Param | Lookup |
|-------|--------|
| `search` | `description__icontains` |
| `date_from` | `date__gte` |
| `date_to` | `date__lte` |
| `bank` | exact |
| `is_credit` | exact |
| `is_installment` | exact |

#### Pagination — `TransactionPagePagination`

`PageNumberPagination` with `page_size=25`. Response includes `count`, `next`, `previous`, `results`. Frontend uses the `count` and page number buttons to build the paginator UI.

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
| `parsers/nubank.py` | `NubankParser` (CSV) |
| `parsers/inter.py` | `InterParser` (PDF via pdfplumber) |
| `parsers/btg.py` | `BTGParser` (XLSX via openpyxl + msoffcrypto) |
| `parsers/registry.py` | maps bank name → parser instance |
| `views.py` | `StatementUploadView`, `StatementListView` |
| `urls.py` | `/api/import/upload/`, `/api/import/` |

#### Parser pattern — Strategy + Registry

Adding a new bank requires **one new file** only. See `docs/backend/parsers.md` for full details.

#### Installment date normalization (BTG and Inter)

Both BTG and Inter record the purchase date for all installments. The parsers normalize to the actual billing month via `relativedelta`:

```python
billing_date = purchase_date + relativedelta(months=installment_number - 1)
```

Nubank already exports each installment on its billing date — no shift needed.

#### `process_statement()` flow

```
1. Check duplicate (user + filename) → raises ValueError if exists
2. Create Statement with status="pending"
3. get_parser(bank) → parser
4. parser.parse(file, password) → list[TransactionDTO]
5. bulk_create(Transaction rows)  ← atomic
6. statement.status = "processed", transaction_count = N
7. statement.save()

On any exception in steps 3-6:
   statement.status = "failed" → save → re-raise
```

#### Duplicate prevention

Two layers:
1. **Service check** (application): `if Statement.objects.filter(user=user, filename=filename).exists()` → raises `ValueError`
2. **DB constraint** (database): `UniqueConstraint(fields=["user", "filename"])` — enforced at DB level even if service check is bypassed

---

## Authentication

JWT via `djangorestframework-simplejwt`.

- Access token: **1 hour** TTL
- Refresh token: **7 days** TTL, rotated on use
- Header: `Authorization: Bearer <access_token>`
- `DEFAULT_PERMISSION_CLASSES = [IsAuthenticated]` → every endpoint is protected by default
- Axios response interceptor auto-refreshes on 401 and retries the original request

---

## Testing

### Running tests

```bash
# Inside the container (all tests)
docker exec back python manage.py test identity finances statements

# Specific app
docker exec back python manage.py test statements.tests.parsers

# With verbosity
docker exec back python manage.py test --verbosity=2
```

### Test layout

```
identity/tests/
├── test_models.py      # User, UserProfile
├── test_serializers.py # RegisterSerializer, UserSerializer
└── test_views.py       # RegisterView, UserDetailView

finances/tests/
├── test_models.py      # Category, Transaction
├── test_filters.py     # TransactionFilter (search, dates, bank, is_credit)
└── test_views.py       # TransactionListView (pagination, filters), SpendingOverTimeView

statements/tests/
├── test_models.py      # Statement (str, unique constraint, ordering)
├── test_services.py    # process_statement() (success, duplicate, failure, atomicity)
├── test_views.py       # StatementUploadView, StatementListView
└── parsers/
    ├── test_nubank.py  # NubankParser (detect, parse, installments)
    ├── test_inter.py   # InterParser (_parse_br_decimal, _parse_table, date shift)
    ├── test_btg.py     # BTGParser (XLSX parsing, installment shift, month-end)
    └── test_registry.py# get_parser (all banks, unknown, case sensitivity)
```

Parser tests use in-memory files (`io.BytesIO`, `io.StringIO`, in-memory openpyxl workbooks) — no real bank files needed. Service tests mock `get_parser` to isolate `process_statement` from parser logic.

### E2E tests

See `tests/e2e/README.md` at the repo root for planned E2E coverage with Playwright.

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
