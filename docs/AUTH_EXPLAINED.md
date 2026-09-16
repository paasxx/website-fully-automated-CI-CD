# Auth System — How It Works and Why

Reference doc for the FinTrack auth system: state lifecycle, the axios interceptor,
and the custom-event bridge between them.

---

## 1. State diagram

```
app opens (mount / F5 / new tab / browser reopen)
       ↓
  loading = true
       ↓
  is there a token in localStorage?
       ├─ no  → loading = false, user stays null → /login
       └─ yes → fetchUser()
                  ├─ succeeds → user = {...}, loading = false
                  └─ fails    → logout() (clears tokens, user = null), loading = false
       ↓ (authenticated user)
  using the app normally
       ↓
  access_token expires → request gets 401 → interceptor tries a refresh
       ├─ refresh succeeds → new tokens saved, original request retried,
       │                     the user never notices
       └─ refresh fails    → dispatches 'auth:expired'
       ↓
  AuthContext listener: clears tokens, sessionExpired = true
       ↓
  modal appears over whatever screen the user is on
       ↓
  user clicks "Sign in" → logout() + navigate('/login')
       ↓
  user = null, sessionExpired = false → login page
```

Note the two separate branches after "is there a token": **no token at all** just
stops loading — there's nothing to log out from. **Invalid/expired token** is the
only branch that calls `logout()`, inside `fetchUser()`'s `.catch()`.

---

## 2. Files and their responsibilities

| File | Role |
|---|---|
| `axiosConfig.js` | Axios instance with request/response interceptors |
| `AuthContext.jsx` | Global auth state (`user`, `loading`, `sessionExpired`) |
| `App.jsx` | Renders `SessionExpiredModal` at the Router level |
| `PrivateRoute.jsx` | Guards private routes — redirects to `/login` when unauthenticated |
| `Login.jsx` | Login form |
| `Register.jsx` | Registration form |

---

## 3. The two `useEffect`s in AuthContext

Both run with an empty dependency array — each fires exactly once, when
`AuthProvider` first mounts.

**Listener for `auth:expired`**: registers an event listener once and keeps it
alive for the component's lifetime — it does **not** touch tokens at mount time.
The actual cleanup (removing tokens, flagging the session as dead) only runs
later, whenever the custom event fires — however long after mount the access
token happens to expire and its refresh attempt fails. This is the bridge
between `axiosConfig.js` (plain JS, can't call `setState`) and this context —
see section 5.

**Session restore**: reads `localStorage` for a saved token and, if one exists,
calls `fetchUser()` to rehydrate `user`. This exists because "mounting
`AuthProvider`" doesn't mean "brand new visitor" — it happens every time the JS
runtime restarts in the browser: pressing **F5**, opening the app in a **new
tab**, or **reopening the browser** after closing it. React state lives only in
memory and is wiped on every one of those; `localStorage` survives them.
Without this effect, a logged-in user would get bounced back to `/login` on
every reload, even with a perfectly valid session already sitting in storage.

---

## 4. The Axios interceptors — request and response

Axios lets you intercept every request before it leaves and every response
before it reaches `.then()`. This is the right place for cross-cutting auth
logic: attaching the token, automatic refresh.

### Request interceptor (attaches the token)

```jsx
axiosInstance.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
        config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config; // required — otherwise the request hangs
}, (error) => Promise.reject(error));
```

Runs before any request leaves. If it doesn't return `config`, the request never fires.

### Response interceptor (automatic refresh)

```jsx
axiosInstance.interceptors.response.use(
    res => res, // ok response: pass through

    async err => {
        const original = err.config;

        // We only care about 401 (unauthorized — expired or invalid token)
        if (err.response?.status !== 401) return Promise.reject(err);

        // If the refresh call itself failed: the session is dead for good
        if (original.url?.includes('token/refresh')) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.dispatchEvent(new CustomEvent('auth:expired'));
            return Promise.reject(err);
        }

        // Prevents a loop: marks that this request already tried a retry
        if (original._retry) return Promise.reject(err);
        original._retry = true;

        const refresh = localStorage.getItem('refresh_token');
        if (!refresh) {
            window.dispatchEvent(new CustomEvent('auth:expired'));
            return Promise.reject(err);
        }

        try {
            const { data } = await axiosInstance.post('/auth/token/refresh/', { refresh });
            localStorage.setItem('access_token', data.access);
            localStorage.setItem('refresh_token', data.refresh); // token rotation
            return axiosInstance(original); // retry the original request with the new token
        } catch {
            window.dispatchEvent(new CustomEvent('auth:expired'));
            return Promise.reject(err);
        }
    }
);
```

**Full flow when the access_token expires:**
1. A component does `GET /finances/transactions/`
2. The request interceptor attaches the expired token to the header
3. Django returns 401
4. The response interceptor catches the 401
5. Checks: not the refresh URL, not `_retry` yet → attempts a refresh
6. `POST /auth/token/refresh/` with the saved refresh_token
7. Django validates and returns new tokens (`ROTATE_REFRESH_TOKENS=True`)
8. New tokens are saved to localStorage
9. The original request (`GET /finances/transactions/`) is retried with the new token
10. The component gets its response normally — it never noticed a refresh happened

---

## 5. Custom events — communication between decoupled modules

`axiosConfig.js` has no access to `AuthContext`. It can't call `setSessionExpired(true)`
directly. Solution: use `window` as an event bus.

```jsx
// In axiosConfig.js — publishes the event (doesn't know who's listening)
window.dispatchEvent(new CustomEvent('auth:expired'));

// In AuthContext.jsx — subscribes to the event (doesn't know who published it)
window.addEventListener('auth:expired', handle);
```

This is the Pub/Sub pattern. Axios publishes. AuthContext listens. Neither one
knows the other exists — that's the decoupling.

**Why not call `logout()` directly from the interceptor?**
`logout()` uses `setUser` — a React function that only works inside a component
or hook. Calling it from inside Axios (plain JavaScript, outside React) would
break the rules of hooks and throw at runtime. The custom event is the safe bridge.

---

## 6. The session-expired modal — why it lives in App.jsx

**Previous problem**: the modal used to live in `Login.jsx` as a banner. When the
session expired, `logout()` was called immediately → `user = null` →
`PrivateRoute` redirected to `/login` → only then did the banner show up. The
experience: the screen changed abruptly.

**Current solution**: the modal lives in `App.jsx`, inside the Router but outside the Routes.

The `auth:expired` handler **does not call `logout()`** — it only removes the
tokens from localStorage and sets `sessionExpired = true`. `user` stays in
state → `PrivateRoute` doesn't redirect → the modal appears on top of whatever
page the user is on.

```jsx
const SessionExpiredModal = () => {
    const { sessionExpired, logout } = useAuth();
    const navigate = useNavigate();

    if (!sessionExpired) return null;

    return (
        <div className="modal-overlay">
            <div className="modal-card">
                <div className="modal-title">Session Expired</div>
                <div className="modal-description">
                    Your session has expired. Please sign in again to continue.
                </div>
                <button className="modal-btn modal-btn--confirm" onClick={() => {
                    logout();         // only now: clears user + tokens + sessionExpired
                    navigate('/login');
                }}>
                    Sign in
                </button>
            </div>
        </div>
    );
};
```

**Why does `useNavigate` require being inside the Router?**
`useNavigate` reads React Router's context. If the component were defined
outside `<Router>`, the hook wouldn't find the context and would throw. That's
why `SessionExpiredModal` is defined inside the `App.jsx` file (but above the
`App` function itself), and rendered inside `<Router>`.

> Not yet confirmed whether this modal reliably shows up for a real user in
> every scenario — it's fully reactive (see section 1), so it only appears
> after *some* request happens to fail. Worth a dedicated test once the login/
> refresh test coverage exists.

---

## 7. Tokens in localStorage — risks and alternatives

**Risk**: XSS (Cross-Site Scripting). If a malicious script runs on your page,
it can read `localStorage.getItem('access_token')` and exfiltrate the token.

**Safer alternative**: httpOnly cookies. The browser doesn't expose `httpOnly`
cookies to JavaScript — it only sends them automatically with every request.
The backend sets them.

| | localStorage | httpOnly cookie |
|--|--|--|
| Readable by JS | Yes (XSS risk) | No (safer) |
| Sent automatically | No (manual, via header) | Yes |
| CSRF risk | No | Yes (needs a CSRF token) |
| Multi-domain | Simple | More complex |
| Current implementation | Yes | Requires a backend change |

For a personal project, localStorage is acceptable. For production with real
third-party user data, migrating to httpOnly cookies is the right call.

---

## 8. Token lifetime (settings.py)

```python
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),   # expires in 1h
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),   # expires in 7 days
    "ROTATE_REFRESH_TOKENS": True,                 # each refresh issues a new refresh token
}
```

**Why `ROTATE_REFRESH_TOKENS=True`?** On every refresh, Django invalidates the
previous refresh_token and returns a new one. This stops a stolen refresh token
from being usable for the full 7 days — if the real user keeps using the app,
the token rotates and the stolen one becomes invalid.

---

## 9. Known failure scenarios (tracked)

Two real bugs found while writing tests, not yet fixed. Both end the same way
(a broken session) but through different mechanisms.

**Blank screen on stale tokens ([#67](https://github.com/paasxx/website-fully-automated-CI-CD/issues/67))**
Needs only a single request — no concurrency involved. If both tokens are
invalid (two tabs open, logout in one; backend down during a refresh; the
refresh_token naturally expired after 7 days idle), the interceptor's error
handler (section 4) ends in a rejected Promise that reaches whatever component
made the request. The app has no Error Boundary anywhere in the tree, so an
unhandled render-time error from that rejection crashes the whole React app
instead of showing a message.

**Concurrent refresh race condition ([#61](https://github.com/paasxx/website-fully-automated-CI-CD/issues/61))**
When the access_token expires and two or more requests are in flight at the
same time (e.g. a page firing several fetches on mount), each one
independently sets its own `_retry` flag and reads the *same* refresh_token
before either has updated it. Whichever refresh call reaches the backend first
succeeds and rotates the token; the second one is rejected because that
refresh_token was just invalidated. Because that failing refresh call is
itself routed through the same interceptor, it hits the "refresh URL failed"
branch (section 4) — which clears *both* tokens from localStorage and
dispatches `auth:expired`, wiping out the valid tokens the first call just
saved, even though the session is actually fine.
