# Authentication Architecture

## Overview

The system uses **HTTP-only cookie-based JWT authentication**. Tokens are never exposed to JavaScript — they are stored in cookies the browser manages automatically, protecting against XSS token theft.

---

## End-to-End Auth Flow

```
User enters credentials
        │
        ▼
┌─────────────────────────┐
│  LoginPage.vue          │  ← Collects email + password
│  handleLogin()          │  ← Local validation first
└───────────┬─────────────┘
            │  POST /api/auth/login/  (JSON body, withCredentials: true)
            ▼
┌─────────────────────────────────────────────────────┐
│  Django: LoginView                                   │
│  1. LoginSerializer validates email/password fields  │
│  2. authenticate(email, password) → User or None     │
│  3. Check user.is_active                             │
│  4. RefreshToken.for_user(user) → JWT pair           │
│  5. set_auth_cookies(response, access, refresh)      │
│  6. log_action(LOGIN) → AuditLog                    │
└───────────┬─────────────────────────────────────────┘
            │  HTTP 200 + Set-Cookie: access_token (10m), refresh_token (7d)
            │  Both cookies: HttpOnly=true, SameSite=Lax
            ▼
┌─────────────────────────┐
│  useAuth.login()        │  ← Stores user object in reactive ref
│  user.value = data.user │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Vue Router             │  ← Redirects to role-specific dashboard
│  getDashboardRedirect() │    ADMIN→/admin, CEO→/manager, COMMERCIAL→/commercial
└─────────────────────────┘
```

---

## Token Lifecycle & Silent Refresh

```
Browser has access_token cookie (valid 10 min)
        │
        ▼
Request hits protected endpoint
        │
        ├─ Token valid ──────────────────────────────► Response OK
        │
        └─ Token expired (401 from backend)
                │
                ▼
        axios response interceptor catches 401
                │
                ├─ Is this an auth endpoint? → reject immediately
                │
                ▼
        POST /api/auth/refresh/
        (browser sends refresh_token cookie automatically)
                │
                ├─ Refresh valid → new access_token + rotated refresh_token cookies set
                │                   original request retried transparently
                │
                └─ Refresh invalid/expired → forceLogout()
                        └─ window.dispatchEvent('auth:session-expired')
                        └─ Redirect to /login?redirect=<current_path>&reason=session_expired
```

Multiple concurrent requests during a refresh are queued in `pendingRequests[]` and replayed after the refresh completes. This prevents duplicate `/auth/refresh/` calls.

---

## Session Verification on Navigation

On every page load (first navigation), the router calls `fetchUser()` which hits `GET /api/auth/me/`. This silently restores session state from the cookie without requiring JavaScript to store anything.

On subsequent navigations to protected routes, the router re-validates the session against the backend every **15 minutes** (`SESSION_TTL = 15 * 60 * 1000`). This catches token expiry without polling continuously.

```
Router.beforeEach(to)
    │
    ├─ user === null (first load) ──► fetchUser() → GET /api/auth/me/
    │
    ├─ requiresAuth && elapsed > 15min ──► fetchUser() (silent re-check)
    │
    ├─ requiresAuth && !isAuthenticated ──► redirect /login?redirect=<to>
    │
    ├─ guestOnly && isAuthenticated ──► redirect role dashboard
    │
    ├─ allowedRoles && user.role not in roles ──► redirect role dashboard
    │
    └─ to.name === "Dashboard" ──► redirect role dashboard
```

---

## Where Auth State Lives

| Layer | Storage | Contents |
|-------|---------|----------|
| **Backend** | PostgreSQL: `user_sessions` table | Refresh token tracking (not used for active lookup) |
| **Backend** | `rest_framework_simplejwt` token blacklist | Blacklisted refresh tokens post-logout |
| **Browser** | HTTP-only cookies | `access_token` (10min), `refresh_token` (7 days) |
| **Frontend** | `useAuth.js` module-level `ref` | `user` object (id, email, nom, prenom, role, fonction) |
| **Frontend** | Nothing in localStorage/sessionStorage | — intentionally never stored there |

---

## How Protected Routes Work

Routes are defined with `meta` flags in `router/index.js`:

```js
meta: { requiresAuth: true }              // Any authenticated user
meta: { requiresAuth: true, roles: ["ADMIN"] }   // ADMIN only
meta: { requiresAuth: false, guestOnly: true }   // Redirect to dashboard if logged in
```

The `beforeEach` guard enforces these rules on every navigation.

> ⚠️ **Important distinction**: Router guards are **UI-only protection**. All sensitive API endpoints are independently protected by DRF permission classes on the backend. A user who manipulates the frontend cannot bypass backend checks.

---

## How Role-Based Navigation Works

After login, `getDashboardRedirect(role)` maps role to dashboard:

| Role | Dashboard Route | URL |
|------|----------------|-----|
| `ADMIN` | `AdminDashboard` | `/admin` |
| `CEO` | `ManagerDashboard` | `/manager` |
| `COMMERCIAL` | `CommercialDashboard` | `/commercial` |

Role sub-routes are protected individually:
- `/admin/*` → `roles: ["ADMIN"]`
- `/manager/*` → `roles: ["CEO"]`
- `/commercial/*` → `roles: ["COMMERCIAL"]`

If a user navigates to a route not allowed for their role, they are silently redirected to their own dashboard (not shown an error). This is a UX choice — no "access denied" page.

---

## Communication Protocol

```
Frontend (Vite dev: :5173)          Backend (Django: :8000)
     │                                      │
     │  Vite proxy: /api → :8000            │
     │  withCredentials: true               │
     │  X-CSRFToken: <from csrftoken cookie>│
     │                                      │
     │──── POST /api/auth/login/ ──────────►│
     │◄─── 200 + Set-Cookie ───────────────│
     │                                      │
     │──── GET /api/auth/me/ ──────────────►│  Cookie sent automatically by browser
     │◄─── 200 {user} ─────────────────────│  CookieJWTAuthentication reads access_token
```

In production, both are served from the same domain (or with proper `CORS_ALLOWED_ORIGINS` + `CORS_ALLOW_CREDENTIALS = True`).
