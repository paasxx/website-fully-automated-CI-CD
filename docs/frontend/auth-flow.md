# Authentication Flow

## Overview

JWT-based authentication. Tokens are stored in `localStorage`. The `AuthContext` manages the auth state for the entire application.

---

## Token lifecycle

```
Login
  └── POST /api/auth/token/
        └── { access: "eyJ...", refresh: "eyJ..." }
              ├── access  → localStorage["access_token"]   (1 hour TTL)
              └── refresh → localStorage["refresh_token"]  (7 days TTL, rotated on use)
```

---

## `AuthContext` — how it works

**On mount** (every time the app loads):
```js
const token = localStorage.getItem('access_token')
if (token) {
    GET /api/auth/me/ (with token in header)
    ├── success → setUser(data), loading=false
    └── fail    → logout() (clears localStorage), loading=false
```

This restores the session from a previous visit without requiring the user to log in again.

**`loading` state:**
While the token is being verified, `loading=true`. The `PrivateRoute` shows a loading screen during this time to prevent the flash of the login page for already-authenticated users.

---

## `PrivateRoute` logic

```jsx
const PrivateRoute = ({ children }) => {
    const { user, loading } = useAuth();

    if (loading) return <div>Loading...</div>;
    if (!user)   return <Navigate to="/login" replace />;
    return children;
};
```

Three states:
1. `loading=true` → show loading (session being verified)
2. `!user` → redirect to `/login`
3. `user` → render the protected page

---

## Axios interceptors

### Request interceptor

Every request made through `axiosInstance` automatically includes the JWT token:

```js
axiosInstance.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token');
    if (token) config.headers['Authorization'] = `Bearer ${token}`;
    const csrf = getCookie('csrftoken');
    if (csrf) config.headers['X-CSRFToken'] = csrf;
    return config;
});
```

### Response interceptor — auto token refresh

When a request returns 401:

```
401 received
  ├── is it the refresh endpoint itself? → clear tokens → dispatch auth:expired → done
  ├── already retried (_retry flag)? → bail
  └── try POST /auth/token/refresh/
        ├── success → update access + refresh in localStorage → retry original request
        └── fail    → dispatch "auth:expired" CustomEvent
```

`AuthContext` listens for `auth:expired` via `window.addEventListener`. When fired: calls `logout()` + sets `sessionExpired=true`. `PrivateRoute` redirects to `/login`, where a banner reads "Sua sessão expirou. Faça login novamente." The banner clears when the user logs in again.

This means users stay logged in for up to 7 days (refresh token lifetime) without any action needed.

---

## Profile update flow

`UserDetailCard` handles the full profile edit cycle:

```
Component mounts
    └── GET /api/auth/me/ → setDbData(data) + setFormData(data)
                                (formData pre-filled from server values)

User edits fields → formData changes (dbData is read-only reference)

User clicks Save:
    1. validate() — required fields, email regex, phone min-length
       └── errors? → set errors state, abort
    2. hasChanges() — deep-compare formData vs dbData
       └── no changes? → status='no-changes', auto-dismiss 3s, abort
    3. status='saving' → 500ms UX delay
    4. PUT /api/auth/me/ with full formData payload
       ├── success → setDbData(response), status='success', auto-dismiss 3s
       └── error   → status='idle', console.error
```

**Key patterns:**
- `dbData` is never mutated — it's the source of truth for "what's saved"
- `formData` is the working copy; `hasChanges()` diffs it against `dbData`
- `validate()` runs before `hasChanges()` — empty required fields must be caught even when nothing else changed
- Status auto-resets to `'idle'` after 3s so feedback doesn't linger

---

## Security notes

- Tokens in `localStorage` are accessible by JavaScript — vulnerable to XSS. For higher security, use `httpOnly` cookies. For a portfolio project, `localStorage` is acceptable.
- The backend sets `DEFAULT_PERMISSION_CLASSES = [IsAuthenticated]` — every endpoint requires auth by default. Only `register` and `token` are explicitly `AllowAny`.
- User ID is never accepted from the request body. It always comes from the JWT (`request.user`).

---

## What's not implemented

- **Password reset:** No forgot-password flow yet.
- **Email verification:** Users can register with any email — no confirmation step.
