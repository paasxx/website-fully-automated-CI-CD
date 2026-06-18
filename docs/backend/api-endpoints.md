# API Endpoints

Base URL: `http://localhost:8000/api` (dev) / `https://api.yourdomain.com/api` (prod)

All endpoints except `/auth/register/` and `/auth/token/` require:
```
Authorization: Bearer <access_token>
```

---

## Auth — `/api/auth/`

### `POST /api/auth/register/`
Create a new account. No authentication required.

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
{ "access": "eyJ...", "refresh": "eyJ..." }
```

---

### `POST /api/auth/token/refresh/`
Refresh access token. Refresh token is rotated on use (old token invalidated).

**Request:**
```json
{ "refresh": "eyJ..." }
```
**Response 200:**
```json
{ "access": "eyJ...", "refresh": "eyJ..." }
```

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
Update user data and/or profile. Partial update — omit any field to leave it unchanged.

**Request:**
```json
{
  "first_name": "Pedro",
  "profile": {
    "display_name": "pedro.dev",
    "timezone": "America/Sao_Paulo"
  }
}
```

**Response 200:** same shape as `GET /api/auth/me/`.

**Notes:**
- `email`, `id`, `date_joined`, `last_login`, `is_staff`, `is_active` are read-only — ignored in request body.
- `UserProfile` is auto-created via `get_or_create` if it doesn't exist.

---

## Statements — `/api/import/`

### `POST /api/import/upload/`
Upload a bank statement file.

**Request:** `multipart/form-data`
- `file`: `.csv` (Nubank) or `.xlsx` (BTG) or `.pdf` (Inter)
- `bank`: `nubank` | `inter` | `btg`
- `password` *(optional)*: required for BTG (CPF without punctuation) and Inter (first 6 CPF digits)

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

**Error 400** (invalid bank):
```json
{ "error": "Invalid bank. Supported: nubank, inter, btg" }
```

**Error 500** (parse failure):
```json
{ "error": "Processing failed.", "detail": "..." }
```

---

### `GET /api/import/`
List recent statements (last 10, newest first).

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
List transactions. Scoped to authenticated user. Paginated and filterable.

**Query params:**

| Param | Type | Description |
|-------|------|-------------|
| `search` | string | Case-insensitive substring match on `description` |
| `bank` | string | Exact match: `nubank`, `inter`, `btg` |
| `is_credit` | boolean | `true` = credits/payments, `false` = expenses |
| `is_installment` | boolean | Filter installment transactions |
| `date_from` | date | `YYYY-MM-DD` — results on or after this date |
| `date_to` | date | `YYYY-MM-DD` — results on or before this date |
| `page` | int | Page number (default: 1) |
| `page_size` | int | Results per page (default: 25, max: 200) |

**Response 200:**
```json
{
  "count": 143,
  "next": "http://localhost:8000/api/finances/transactions/?page=2",
  "previous": null,
  "results": [
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
      "category": null
    }
  ]
}
```

Note: `category_name` is included in the response only when `category` is not null (DRF omits it via SkipField when the source traversal hits None).

---

### `GET /api/finances/spending-over-time/`
Monthly spending aggregated by bank. Credits excluded.

**Response 200:**
```json
{
  "data": [
    { "month": "2026-04", "nubank": 1200.00 },
    { "month": "2026-05", "nubank": 3243.64, "inter": 800.00 }
  ],
  "banks": ["inter", "nubank"]
}
```

Each entry in `data` only includes keys for banks that have transactions in that month.
