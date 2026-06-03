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
Get current user data.

**Response 200:**
```json
{
  "id": 1,
  "email": "user@email.com",
  "first_name": "",
  "last_name": ""
}
```

---

## Statements — `/api/import/`

### `POST /api/import/upload/`
Upload a bank statement CSV file.

**Request:** `multipart/form-data`
- `file`: CSV file
- `bank`: `nubank` | `inter` | `btg`

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
