# Frontend Architecture

## Stack

| Tool | Version | Why |
|------|---------|-----|
| React | 18 | component model, hooks |
| Vite | 5 | fast dev server, no CRA legacy issues |
| React Router | 6 | client-side routing |
| Axios | 1.6 | HTTP client with interceptors + auto token refresh |
| Recharts | 3 | React-native charting library |
| SCSS | via `sass` | variables, mixins, nesting |
| react-phone-input-2 | 2.15 | phone input with country flag and DDI selector |
| react-timezone-select | 3.3 | searchable timezone selector (portaled to body) |

---

## Folder structure

```
src/
├── api/
│   └── axiosConfig.js         # axios instance: base URL + JWT interceptor + auto-refresh
├── components/
│   ├── Dashboard/
│   │   ├── Dashboard.jsx          # layout: left column (cards) + right column (transactions)
│   │   ├── UploadCard.jsx         # file upload form with password modal (BTG/Inter)
│   │   ├── TransactionList.jsx    # filterable, paginated transaction list
│   │   ├── RecentUploadsCard.jsx  # last 10 uploaded statements with bank medallions
│   │   └── UserDetailCard.jsx     # profile edit form (Account Settings page)
│   ├── Navbar/
│   │   ├── Navbar.jsx             # auth-aware nav links + avatar + logout
│   │   └── ThemeToggleButton.jsx  # dark/light toggle
│   └── PrivateRoute.jsx           # redirects to /login if not authenticated
├── context/
│   ├── AuthContext.jsx         # user state, login(), logout(), loading, sessionExpired
│   └── ThemeContext.jsx        # dark/light mode, localStorage persistence
├── pages/
│   ├── Login.jsx
│   ├── Register.jsx
│   ├── Dashboard.jsx           # thin wrapper: passes refreshKey to Dashboard component
│   ├── Charts.jsx              # spending over time (bar/line chart) with custom legend
│   └── Profile.jsx             # Account Settings — renders UserDetailCard
├── styles/
│   ├── main.scss               # imports everything in order
│   ├── global/
│   │   ├── Variables.scss      # spacing, font sizes, radii, shadows
│   │   ├── Mixins.scss         # card-base, button-base, flex-center, custom-scrollbar
│   │   └── Reset.scss          # CSS reset
│   ├── components/
│   │   ├── Dashboard/
│   │   │   └── Dashboard.scss  # all dashboard cards, filters, pagination, overlays
│   │   ├── Login/
│   │   │   └── Login.scss
│   │   ├── Profile/
│   │   │   └── Profile.scss
│   │   ├── Navbar.scss
│   │   └── Spinner.scss
│   └── layouts/
│       └── Background.scss     # CSS custom properties for dark/light theme
├── App.jsx                  # route definitions + provider tree
└── index.jsx                # React root mount
```

---

## Component hierarchy

```
App
├── ThemeProvider          (theme: dark | light)
└── AuthProvider           (user, login, logout, loading, sessionExpired)
    └── Router
        ├── Navbar         (reads user from AuthContext)
        └── Routes
            ├── /login        → Login (public)
            ├── /register     → Register (public)
            ├── /dashboard    → PrivateRoute → Dashboard page → Dashboard component
            ├── /charts       → PrivateRoute → Charts
            ├── /profile      → PrivateRoute → Profile
            └── /             → PrivateRoute → Navigate to /dashboard
```

**Rule:** `pages/` = screens (one per route). `components/` = reusable UI blocks. Pages import components, not the other way around.

---

## Key component details

### `TransactionList.jsx`

Filterable, paginated list of transactions. All filtering is server-side.

**State:**
- `transactions` / `loading` / `count` / `currentPage`
- `searchInput` (raw) / `debouncedSearch` (300ms debounced) — prevents a request per keystroke
- `bank` / `isCredit` / `dateFrom` / `dateTo`

**Pagination:** `buildPageItems()` produces an array with page numbers and `null` as ellipsis placeholders. Displays first page, last page, and ±2 around the current page.

**Loading states:**
- First load (no previous data): blank spinner
- Filter/page change: spinner overlay on top of existing list — card size stays stable

**Card width:** fixed at `660px` (no `flex-grow`) to prevent resizing when description lengths vary across pages.

### `UploadCard.jsx`

Supports Nubank (CSV), Inter (PDF), BTG (XLSX). Password-protected banks (Inter, BTG) show a modal on submit.

**`BANK_PASSWORD_CONFIG`** drives the modal content:
```js
const BANK_PASSWORD_CONFIG = {
    btg:   { title: '...', description: '...', placeholder: 'CPF sem pontuação', infoTip: '...' },
    inter: { title: '...', description: '...', placeholder: '6 primeiros dígitos do CPF', infoTip: '...' },
};
```

**Tooltip (`BankInfoTooltip`):** rendered into `document.body` via `createPortal` to escape parent `overflow: hidden`. Positioned via `getBoundingClientRect()`.

### `Charts.jsx`

Bar chart and line chart of monthly spending by bank. Toggle between the two with a button group.

- `formatMonth("2026-05")` → `"Mai/26"` (uses `PT_MONTHS` map)
- `CustomLegend`: reads `entry.value` (not `entry.dataKey`) from Recharts legend payload
- `CustomTooltip`: shows formatted month + bank labels + total
- Both charts use `tickFormatter={formatMonth}` on XAxis

---

## Auth flow

```
App mounts
    └── AuthProvider useEffect:
            token in localStorage?
            ├── YES → GET /api/auth/me/ → setUser(data) → loading=false
            └── NO  → loading=false

User visits /dashboard:
    └── PrivateRoute:
            loading? → show "Loading..."
            !user?   → Navigate to /login
            user?    → render children

Login form submit:
    └── login(email, password)
            └── POST /api/auth/token/
                    ├── success → save tokens → GET /me/ → setUser → navigate /dashboard
                    └── fail    → throw → Login.jsx catches → show error

Logout button:
    └── logout() → clear localStorage → setUser(null) → navigate /login

401 from any request:
    └── Axios response interceptor:
            └── POST /api/auth/token/refresh/
                    ├── success → update tokens → retry original request
                    └── fail    → dispatch "auth:expired" event → AuthContext calls logout()
                                  → PrivateRoute redirects to /login with "Sessão expirada" banner
```

---

## API communication

`src/api/axiosConfig.js` creates a single axios instance used everywhere:

```js
baseURL = REACT_APP_BACKEND_URL  // set in docker-compose.dev.yml
timeout = 250s                   // for large file uploads

// Request interceptor:
// 1. Get access_token from localStorage → set Authorization: Bearer <token>
// 2. Get csrftoken from cookies → set X-CSRFToken header

// Response interceptor:
// 401 → try refresh → retry original request → on fail: dispatch auth:expired
```

**Never** create a new `axios.create()` elsewhere — always import `axiosInstance` from `api/axiosConfig.js`.

---

## State management

No Redux or Zustand — state lives close to where it's used:

| State | Where | Why |
|-------|-------|-----|
| `user`, `loading`, `sessionExpired` | AuthContext | needed by every page + Navbar |
| `theme` | ThemeContext | needed by every component for dark/light |
| `refreshKey` | Dashboard.jsx (local) | triggers transaction list refetch after upload |
| `transactions`, `loading`, filters, pagination | TransactionList.jsx (local) | only needed inside that component |
| `statements` | RecentUploadsCard.jsx (local) | same |
| `data` | Charts.jsx (local) | same |
| `dbData`, `formData`, `status` | UserDetailCard.jsx (local) | profile edit state |

**Pattern:** if state is needed by more than 2 components at different levels → Context. If it's local to a subtree → `useState` + prop passing.

---

## Routing conventions

| Path | Auth required | Component |
|------|--------------|-----------|
| `/login` | No | Login.jsx |
| `/register` | No | Register.jsx |
| `/dashboard` | Yes | Dashboard → Dashboard component |
| `/charts` | Yes | Charts |
| `/profile` | Yes | Profile |
| `/` | Yes | redirect → /dashboard |

---

## Environment variables

Set in `docker-compose/docker-compose.dev.yml`:
```yaml
REACT_APP_BACKEND_URL=http://localhost:8000/api
```

Accessed in code as `import.meta.env.REACT_APP_BACKEND_URL` (Vite syntax).
Prefix `REACT_APP_` is configured in `vite.config.js` → `envPrefix: 'REACT_APP_'`.
