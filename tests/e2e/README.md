# E2E Tests

End-to-end tests for the Fintrack application.

## What goes here

E2E tests cover full user flows from the browser through the API to the database.
Each test file maps to a feature or user journey.

Planned coverage:

| File | Flow |
|------|------|
| `auth.spec.js` | Register → Login → Logout → Session expiry |
| `upload_nubank.spec.js` | Upload Nubank CSV → verify transactions appear |
| `upload_btg.spec.js` | Upload BTG XLSX with password modal → verify |
| `upload_inter.spec.js` | Upload Inter PDF with password modal → verify |
| `transactions.spec.js` | Search, filter by bank/type/date, pagination |
| `charts.spec.js` | Spending over time chart renders with correct data |
| `profile.spec.js` | Edit profile fields → changes persisted |

## Recommended tool

**Playwright** — supports Chromium/Firefox/WebKit, has good Python and JS bindings,
and handles file uploads and modal flows natively.

```bash
# Install
npm install -D @playwright/test
npx playwright install

# Run
npx playwright test

# Run with UI (debug mode)
npx playwright test --ui
```

## Setup notes

- Start the local stack with `make dev` before running E2E tests
- Frontend at `http://localhost:3000`, backend at `http://localhost:8000`
- Use a dedicated test database or reset state between runs
- Store test credentials in `.env.test` (not committed)
