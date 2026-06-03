# Authentication Flow

## Overview

JWT-based authentication. Tokens are stored in `localStorage`. The `AuthContext` manages the auth state for the entire application.

---

## Token lifecycle

```
Login
  └── POST /api/auth/token/
        └── { access: "eyJ...", refresh: "eyJ..." }
              ├── access  → localStorage["access_token"]
              └── refresh → localStorage["refresh_token"]

Access token: 1 hour TTL
Refresh token: 7 days TTL, rotated on each use
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

## Axios interceptor

Every request made through `axiosInstance` automatically includes the JWT token:

```js
axiosInstance.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
        config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
});
```

This means you never need to manually pass the token in component code. Just use `axiosInstance.get(...)` and it's handled.

---

## What's not implemented yet

- **Token refresh:** When the access token expires (after 1h), requests will return 401. Currently the user needs to log in again. To fix: add a 401 response interceptor that calls `/api/auth/token/refresh/` automatically.

```js
// TODO: add to axiosConfig.js
axiosInstance.interceptors.response.use(
    res => res,
    async err => {
        if (err.response?.status === 401) {
            const refresh = localStorage.getItem('refresh_token');
            if (refresh) {
                const { data } = await axios.post('/api/auth/token/refresh/', { refresh });
                localStorage.setItem('access_token', data.access);
                localStorage.setItem('refresh_token', data.refresh);
                // retry the original request
                err.config.headers['Authorization'] = `Bearer ${data.access}`;
                return axiosInstance(err.config);
            }
        }
        return Promise.reject(err);
    }
);
```

- **Persistent login:** Access token expires in 1h. Refresh token in 7 days. After 1h, users need to re-login unless the refresh interceptor above is implemented.

- **Password reset:** No forgot-password flow yet.

- **UserProfile form:** `GET/PATCH /api/auth/profile/` endpoint exists on the backend but the Profile page has no form yet.

---

## Security notes

- Tokens in `localStorage` are accessible by JavaScript — vulnerable to XSS. For higher security, use `httpOnly` cookies. For a portfolio project, `localStorage` is acceptable.
- The backend sets `DEFAULT_PERMISSION_CLASSES = [IsAuthenticated]` — every endpoint requires auth by default. Only `register` and `token` are explicitly `AllowAny`.
- User ID is never accepted from the request body. It always comes from the JWT (`request.user`).
