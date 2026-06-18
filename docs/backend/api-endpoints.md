# API Endpoints

Base URL: `http://localhost:8000/api` (dev) / `https://api.candlefarm.com.br/api` (prod)

All endpoints except `/auth/register/` and `/auth/token/` require:
```
Authorization: Bearer <access_token>
```

---

## Auth — `/api/auth/`

### `POST /api/auth/register/`
Create a new account.

**Request:**
```json
{ "email": "user@email.com", "password": "min8chars" }
```
**Response 201:**
```json
{ "email": "user@email.com", "first_name": "", "last_name": "" }
```

---

### `POST /api/auth/token/`
Login — returns JWT token pair.

**Request:**
```json
{ "email": "user@email.com", "password": "yourpassword" }
```
**Response 200:**
```json
{
  "access": "eyJ...",
  "refresh": "eyJ..."
}
```

---

### `POST /api/auth/token/refresh/`
Refresh access token.

**Request:**
```json
{ "refresh": "eyJ..." }
```
**Response 200:**
```json
{ "access": "eyJ...", "refresh": "eyJ..." }
```
Note: refresh token is rotated on each use (old token invalidated).

---

### `GET /api/auth/me/`
Get current user data including profile.

**Response 200:**
```json
{
  "id": 1,
  "email": "user@email.com",
  "first_name": "Pedro",
  "last_name": "Silveira",
  "is_staff": false,
  "is_active": true,
  "date_joined": "2026-06-01T12:00:00Z",
  "last_login": "2026-06-12T09:30:00Z",
  "profile": {
    "display_name": "pedro.dev",
    "notification_email": "alerts@email.com",
    "phone": "5511987654321",
    "timezone": "America/Sao_Paulo"
  }
}
```

---

### `PUT /api/auth/me/`
Update user data and/or profile. Supports partial updates — omit any field to leave it unchanged.

**Request:**
```json
{
  "first_name": "Pedro",
  "last_name": "Silveira",
  "profile": {
    "display_name": "pedro.dev",
    "notification_email": "alerts@email.com",
    "phone": "5511987654321",
    "timezone": "America/Sao_Paulo"
  }
}
```

**Response 200:** same shape as `GET /api/auth/me/` with updated values.

**Notes:**
- `email`, `id`, `date_joined`, `last_login`, `is_staff`, `is_active` are read-only — included in response but ignored in request body.
- `profile.user` is read-only and excluded from the writable fields.
- `UserProfile` is auto-created on first edit via `get_or_create` if it doesn't exist yet.

---

## Statements — `/api/import/`

### `POST /api/import/upload/`
Upload a bank statement file (CSV or XLSX).

**Request:** `multipart/form-data`
- `file`: `.csv` (Nubank, Inter) or `.xlsx` (BTG)
- `bank`: `nubank` | `inter` | `btg`
- `password` *(optional)*: required for BTG — the file is encrypted; default password is the account holder's CPF (digits only)

**Response 201:**
```json
{
  "id": 1,
  "filename": "Nubank_2026-06-27.csv",
  "bank": "nubank",
  "transaction_count": 16,
  "status": "processed"
}
```

**Error 400** (duplicate):
```json
{ "error": "'Nubank_2026-06-27.csv' has already been imported." }
```

---

### `GET /api/import/`
List recent statements (last 10).

**Response 200:**
```json
[
  {
    "id": 1,
    "filename": "Nubank_2026-06-27.csv",
    "bank": "nubank",
    "transaction_count": 16,
    "status": "processed",
    "uploaded_at": "27/06/2026 14:30"
  }
]
```

---

## Finances — `/api/finances/`

### `GET /api/finances/transactions/`
List transactions. All scoped to authenticated user.

**Query params (optional):**
- `year=2026`
- `month=5`
- `bank=nubank`

**Response 200:**
```json
[
  {
    "id": 1,
    "date": "2026-05-29",
    "description": "DAKI - NuPay",
    "amount": "118.81",
    "bank": "nubank",
    "is_credit": false,
    "is_installment": false,
    "installment_number": null,
    "installment_total": null,
    "balance_after": null,
    "bank_category": null,
    "transaction_type": null,
    "category": null,
    "category_name": null
  }
]
```

---

### `GET /api/finances/spending-over-time/`
Aggregated monthly spending by bank. Credits excluded.

**Response 200:**
```json
{
  "data": [
    { "month": "2026-05", "nubank": 3243.64, "inter": 800.00 }
  ],
  "banks": ["inter", "nubank"]
}
```
