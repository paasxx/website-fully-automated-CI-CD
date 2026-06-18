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

Adding a new bank requires **one new file** only. The registry maps bank name → parser instance; `services.py` calls `get_parser(bank)` without knowing which parser handles which bank.

```python
# statements/parsers/registry.py
_PARSERS = {
    "nubank": NubankParser(),
    "btg":    BTGParser(),
    "mybank": MyBankParser(),  # ← add here
}
```

---

#### `NubankParser` — CSV, separador `,`, encoding UTF-8

Colunas: `date` (YYYY-MM-DD), `title`, `amount` (negativo = crédito).

Parcelas detectadas por sufixo na descrição: `"- Parcela 2/6"` → removido da descrição, preenchido em `installment_number` e `installment_total`.

```python
REQUIRED_HEADERS = {"date", "title", "amount"}

def detect(cls, headers):
    return cls.REQUIRED_HEADERS.issubset(headers)
```

---

#### `BTGParser` — XLSX criptografado, senha = CPF do titular

O BTG exporta faturas como `.xlsx` protegido por senha (padrão: CPF sem pontuação). O parser:

1. Lê o arquivo como bytes e carrega em `io.BytesIO`
2. Se `password` fornecida: descriptografa com `msoffcrypto`, depois lê com `openpyxl`
3. Localiza o header **dinamicamente** (busca linha com `'Data'` na col 1, `'Descrição'` na col 2) — necessário porque as primeiras 24 linhas são resumo da fatura
4. Itera as linhas de transação: col 1 = data, col 2 = descrição, col 4 = valor, col 5 = tipo de compra
5. Parcelas detectadas por regex `(N/M)` embutido na descrição
6. **Normalização de data de parcelas** (ver seção abaixo)

Tipos de compra mapeados para `transaction_type`: `'Parcela sem juros'`, `'Compra à vista'`, `'Compra internacional'`.

`detect()` retorna sempre `False` — BTG nunca é detectado por headers CSV. A identificação é feita pelo campo `bank` enviado no upload.

**Dependências adicionais:** `msoffcrypto-tool`, `openpyxl`, `python-dateutil` (em `requirements.txt`).

#### Normalização de datas de parcelas BTG

**Problema:** o extrato BTG lista todas as N parcelas de uma compra com a data original da compra. O Nubank, por contraste, registra cada parcela na data em que ela caiu na fatura mensal.

Sem normalização, uma compra de R$600 em 3x feita em abril apareceria assim no BTG:

```
Netflix (1/3)  date=01/04  R$200
Netflix (2/3)  date=01/04  R$200   ← errado: deveria ser maio
Netflix (3/3)  date=01/04  R$200   ← errado: deveria ser junho
```

Isso empilharia R$600 em abril no gráfico, distorcendo o spending-over-time.

**Solução implementada:** o parser aplica `billing_date = purchase_date + relativedelta(months=N-1)` para cada parcela:

```python
billing_date = purchase_date + relativedelta(months=installment_number - 1)
# (1/3) → +0 meses  → abril   ✓
# (2/3) → +1 mês    → maio    ✓
# (3/3) → +2 meses  → junho   ✓
```

`relativedelta` (do `python-dateutil`) é usado no lugar de `timedelta(days=30)` porque respeita os limites do calendário — `Jan 31 + 1 mês = Fev 28`, não um erro.

**Atenção:** essa lógica assume que o BTG exporta todas as N parcelas de uma compra com a data original em um único extrato. Se o BTG mudar o comportamento e passar a exportar apenas a parcela do mês corrente (como o Nubank), a normalização ficaria errada — deslocaria uma data que já está correta. Validar com extratos futuros.

**Upload flow:** o frontend exibe um modal pedindo a senha quando o banco BTG é selecionado. A senha é enviada no campo `password` do `multipart/form-data`. O `views.py` repassa para `services.py` que repassa para `BTGParser.parse(file, password=password)`.

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
