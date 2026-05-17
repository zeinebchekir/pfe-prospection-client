# Authentication Architecture

## System Overview — How It All Fits Together

> **For new developers** — read this first before diving into code.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         Full Request Lifecycle                           │
│                                                                          │
│  USER                                                                    │
│   │  types credentials / navigates to page                               │
│   ▼                                                                      │
│  BROWSER                                                                 │
│   │  sends HTTP request                                                  │
│   │  ← attaches cookies AUTOMATICALLY (no JS code needed for this)       │
│   ▼                                                                      │
│  AXIOS  (frontend/src/api/axios.js)                                      │
│   │  adds X-CSRFToken header (read from csrftoken cookie)                │
│   │  withCredentials: true  ← tells browser to send cookies              │
│   ▼                                                                      │
│  DJANGO API  (backend)                                                   │
│   │  CookieJWTAuthentication reads access_token from cookie              │
│   │  validates JWT signature + expiry                                    │
│   │  checks DRF permission class (IsAuthenticated / IsAdmin)             │
│   ▼                                                                      │
│  JWT COOKIES  (browser only, inaccessible to JS)                         │
│   │  access_token  — 10 min — authenticates every API call               │
│   │  refresh_token — 7 days — rotates session silently                   │
│   ▼                                                                      │
│  AUTH STATE  (frontend/src/composables/useAuth.js)                       │
│   │  user.value = { id, email, nom, prenom, role, fonction }             │
│   │  ← only the PROFILE is stored in JS, never the raw token             │
│   ▼                                                                      │
│  VUE ROUTER GUARDS  (frontend/src/router/index.js)                       │
│   │  checks meta.requiresAuth, meta.roles on every navigation            │
│   │  redirects if not authenticated or wrong role                        │
│   ▼                                                                      │
│  PROTECTED PAGE COMPONENTS                                               │
│                                                                          │
│  DATABASE (PostgreSQL)                                                   │
│   ├─ users              — accounts, roles, hashed passwords              │
│   ├─ simplejwt_blacklist — invalidated refresh tokens                    │
│   └─ audit_logs         — LOGIN / LOGOUT / CREATE / UPDATE / DELETE      │
└──────────────────────────────────────────────────────────────────────────┘
```

**Key takeaways:**
- The browser sends cookies automatically — Axios does not manually attach auth headers.
- JS **cannot read** `access_token` or `refresh_token` (they are `HttpOnly`).
- Django validates the cookie on every request; the frontend stores only the user profile object.
- Router guards protect the **UI**. Backend permissions protect the **API**. Both are needed.

---

## Token Lifecycle

| Token | Lifetime | Stored Where | HttpOnly | Readable by JS | Purpose |
|-------|----------|-------------|----------|---------------|---------|
| `access_token` | **10 minutes** | HTTP-only browser cookie | ✅ Yes | ❌ No | Authenticates every API request. Short lifetime limits damage if captured. |
| `refresh_token` | **7 days** | HTTP-only browser cookie | ✅ Yes | ❌ No | Exchanged at `/api/auth/refresh/` for a new token pair when access token expires. Old refresh token is immediately blacklisted. |
| `csrftoken` | Django session | Readable browser cookie | ❌ **No** | ✅ **Yes** | Read by Axios (`document.cookie`) to populate the `X-CSRFToken` request header. Required for POST/PATCH/DELETE. |

**Why `access_token` is HttpOnly:** An XSS payload cannot steal what JavaScript cannot read, even if arbitrary JS runs on the page.

**Why `csrftoken` is NOT HttpOnly:** Axios must read it from JS to include it as a header. This is intentional — CSRF tokens protect against cross-site attacks, which is a different threat model than XSS.

**Why token rotation:** `ROTATE_REFRESH_TOKENS = True` means every `/refresh/` call blacklists the old refresh token and issues a new one. An attacker who intercepts an old refresh token cannot reuse it.

---

## Authentication vs. Authorization

> Confusing these two concepts is the root of most auth security bugs.

| | Authentication | Authorization |
|--|---------------|--------------|
| **Question** | *Who is this user?* | *What can this user do?* |
| **Backend mechanism** | `CookieJWTAuthentication` + `authenticate()` | DRF permission classes (`IsAuthenticated`, `IsAdmin`) |
| **Frontend mechanism** | `fetchUser()` → `GET /api/auth/me/` | Vue Router `meta.requiresAuth`, `meta.roles` |
| **Enforced by** | Both layers | **Must be enforced by backend. Frontend is UI-only.** |

### Frontend Route Guards — UX, Not Security

```
✅ Improve experience — prevent wrong-role users from seeing pages
✅ Redirect to login on expired session
✅ Redirect to correct dashboard by role

❌ Can be bypassed in the browser console
❌ Do not protect API endpoints
❌ Not a substitute for backend permissions
```

### Practical Example

```
Scenario: A COMMERCIAL user tries to access manager/admin data.

  Via browser navigation:
    COMMERCIAL → /manager  →  Router guard redirects to /commercial  ✅

  Via direct API call (curl / Postman):
    GET  /api/auth/admin/users/  →  403 Forbidden (IsAdmin enforced)  ✅
    GET  /api/leads/             →  200 OK (IsAuthenticated only — no role check!)  ⚠️

Conclusion:
  - Admin endpoints are secure at the API level.
  - Leads endpoints depend on frontend guards only → see SECURITY_NOTES.md Gap #1.
```

> **Rule:** Every sensitive API endpoint must have a backend permission class. Frontend guards are never sufficient on their own.

---

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
                ├─ Is this an auth endpoint? → reject immediately (avoid loop)
                │
                ├─ isRefreshing === true? → push to pendingRequests[] and wait
                │
                ▼
        isRefreshing = true
        POST /api/auth/refresh/
        (browser sends refresh_token cookie automatically)
                │
                ├─ Refresh valid:
                │   isRefreshing = false
                │   flush pendingRequests[] → all queued requests retried
                │   original request retried → user sees no interruption
                │
                └─ Refresh invalid/expired → forceLogout()
                        └─ window.dispatchEvent('auth:session-expired')
                        └─ useAuth.user.value = null  (clear state first)
                        └─ Redirect to /login?redirect=<path>&reason=session_expired
```

**pendingRequests[] queue:** If multiple requests fail with 401 simultaneously (e.g., on a dashboard loading 5 widgets in parallel), only **one** `/refresh/` call is made. The other requests are queued and replayed after the refresh completes. Without this, each would trigger its own refresh and each would blacklist the others' tokens, causing cascading failures.

**forceLogout:** When the refresh token itself is invalid or expired, the user cannot silently recover. `forceLogout()` fires the `auth:session-expired` event (caught by `useAuth.js` to clear state) and then hard-navigates to `/login?reason=session_expired` so the login page can display a "Your session has expired" message.

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
