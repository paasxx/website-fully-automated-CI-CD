# Frontend Architecture

## Stack

| Tool | Version | Why |
|------|---------|-----|
| React | 18 | component model, hooks |
| Vite | 5 | fast dev server, no CRA legacy issues |
| React Router | 6 | client-side routing |
| Axios | 1.6 | HTTP client with interceptors |
| Recharts | 3 | React-native charting library |
| SCSS | via `sass` | variables, mixins, nesting |
| react-phone-input-2 | 2.15 | phone input with country flag and DDI selector |
| react-timezone-select | 3.3 | searchable timezone selector (portaled to body) |

---

## Folder structure

```
src/
├── api/
│   └── axiosConfig.js       # axios instance: base URL + JWT interceptor
├── components/
│   ├── Dashboard/
│   │   ├── Dashboard.jsx       # layout: left column + right column
│   │   ├── UploadCard.jsx      # file upload form
│   │   ├── TransactionList.jsx # fetches + renders transactions
│   │   ├── RecentUploadsCard.jsx
│   │   └── UserDetailCard.jsx  # profile edit form (Account Settings page)
│   ├── Navbar/
│   │   ├── Navbar.jsx          # auth-aware nav links + avatar + logout
│   │   └── ThemeToggleButton.jsx
│   └── PrivateRoute.jsx        # redirects to /login if not authenticated
├── context/
│   ├── AuthContext.jsx         # user state, login(), logout(), loading
│   └── ThemeContext.jsx        # dark/light mode, localStorage persistence
├── pages/
│   ├── Login.jsx
│   ├── Register.jsx
│   ├── Dashboard.jsx           # thin wrapper around Dashboard component
│   ├── Charts.jsx              # spending over time (bar + line)
│   └── Profile.jsx             # Account Settings — renders UserDetailCard
├── styles/
│   ├── main.scss               # imports everything in order
│   ├── global/
│   │   ├── Variables.scss      # spacing, font sizes, radii, shadows
│   │   ├── Mixins.scss         # card-base, button-base, flex-center, etc.
│   │   └── Reset.scss          # CSS reset (box-sizing, margin/padding zero)
│   ├── components/
│   │   ├── Dashboard/
│   │   │   └── Dashboard.scss
│   │   ├── Login/
│   │   │   └── Login.scss
│   │   ├── Profile/
│   │   │   └── Profile.scss    # profile card, form grid, phone/tz overrides
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
└── AuthProvider           (user, login, logout, loading)
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
```

---

## API communication

`src/api/axiosConfig.js` creates a single axios instance used everywhere:

```js
baseURL = REACT_APP_BACKEND_URL  // set in docker-compose.dev.yml
timeout = 250s                   // for large file uploads

// Request interceptor (runs before every request):
1. Get access_token from localStorage
2. Set Authorization: Bearer <token>
3. Get csrftoken from cookies
4. Set X-CSRFToken header
```

**Never** create a new `axios.create()` elsewhere — always import `axiosInstance` from `api/axiosConfig.js`. This ensures every request is authenticated.

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

## State management

No Redux or Zustand — state lives close to where it's used:

| State | Where | Why |
|-------|-------|-----|
| `user`, `loading` | AuthContext | needed by every page + Navbar |
| `theme` | ThemeContext | needed by every component for dark/light |
| `refreshKey` | Dashboard.jsx (local) | triggers transaction list refetch after upload |
| `transactions` | TransactionList.jsx (local) | only needed inside that component |
| `statements` | RecentUploadsCard.jsx (local) | same |
| `data` | Charts.jsx (local) | same |
| `dbData`, `formData`, `status` | UserDetailCard.jsx (local) | profile edit state; `status`: idle \| saving \| success \| no-changes |

**Pattern:** if state is needed by more than 2 components at different levels → Context. If it's local to a subtree → `useState` + prop passing.

---

## Environment variables

Set in `docker-compose/docker-compose.dev.yml`:
```yaml
REACT_APP_BACKEND_URL=http://localhost:8000/api
```

Accessed in code as `import.meta.env.REACT_APP_BACKEND_URL` (Vite syntax).
Prefix `REACT_APP_` is configured in `vite.config.js` → `envPrefix: 'REACT_APP_'`.
