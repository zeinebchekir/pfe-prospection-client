# Authentication System — Developer Documentation

> **crmPfe / Qualifix** · Django 4 + Vite/Vue 3 · HTTP-only Cookie JWT

---

## What the Auth System Does

The authentication system:

1. **Authenticates users** (proves identity) via email + password, issuing JWT tokens stored as **HTTP-only cookies**.
2. **Authorizes access** (controls what they can do) via a `role` field on the User model enforced on both the backend (DRF permissions) and the frontend (Vue Router guards).
3. **Maintains sessions silently** using a token refresh flow: when the 10-minute access token expires, the frontend automatically exchanges the 7-day refresh token for a new pair without user interaction.
4. **Logs security events** (login, logout, user creation/update/deletion) in an `AuditLog` table.

---

## User Roles

| Role | Display Name | Default on Registration |
|------|-------------|------------------------|
| `ADMIN` | Administrateur | No (manual only) |
| `CEO` | CEO | No (manual only) |
| `COMMERCIAL` | Commercial | **Yes** (auto-assigned) |

---

## Quick Overview: Login / Register / Logout

### Login
1. User submits email + password on `/login`.
2. Frontend calls `POST /api/auth/login/`.
3. Django validates credentials, issues JWT pair, sets two HTTP-only cookies (`access_token`, `refresh_token`).
4. Frontend stores user profile in reactive state (`useAuth` composable), router redirects to role dashboard.

### Register
1. User fills form on `/register`.
2. Frontend calls `POST /api/auth/register/`.
3. Django creates user with role `COMMERCIAL`, issues JWT pair, sets cookies.
4. User is immediately logged in, redirected to `/dashboard`.

### Logout
1. User clicks logout anywhere.
2. Frontend calls `POST /api/auth/logout/`.
3. Django blacklists the refresh token, clears both cookies.
4. Frontend nulls user state, Vue Router redirects to `/login`.

---

## Quick Start for New Developers

```bash
# 1. Start backend (in Docker or locally)
cd backend && python manage.py runserver

# 2. Start frontend
cd frontend && npm run dev

# 3. Register a test user
curl -c cookies.txt -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"dev@test.com","nom":"Test","prenom":"Dev","password":"DevPass123!","password2":"DevPass123!"}'

# 4. Login
curl -c cookies.txt -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"dev@test.com","password":"DevPass123!"}'

# 5. Access your profile (authenticated)
curl -b cookies.txt http://localhost:8000/api/auth/me/
```

---

## Documentation Index

| File | Description |
|------|-------------|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | End-to-end auth flow, ASCII diagram, session lifecycle |
| [API.md](./API.md) | All auth API endpoints with request/response examples |
| [BACKEND.md](./BACKEND.md) | Django implementation: models, views, serializers, permissions |
| [FRONTEND.md](./FRONTEND.md) | Vue/Vite implementation: composable, store, router guards |
| [ROLES_AND_PERMISSIONS.md](./ROLES_AND_PERMISSIONS.md) | Role definitions, access matrix, how to add a new role |
| [SECURITY_NOTES.md](./SECURITY_NOTES.md) | Security model, risks, production recommendations |
| [TESTING.md](./TESTING.md) | How to test auth: manual, automated, curl, common errors |

---

## Key Files at a Glance

```
backend/
  apps/users/
    models.py          # User, UserSession, PasswordResetToken
    views.py           # All auth views (login, register, logout, refresh, me, admin)
    serializers.py     # Request/response validation schemas
    authentication.py  # CookieJWTAuthentication (reads JWT from cookie)
    permissions.py     # IsAdmin custom permission
    utils.py           # set_auth_cookies / unset_auth_cookies helpers
    exceptions.py      # Custom DRF exception handler
    urls.py            # /api/auth/* URL patterns
    tests.py           # pytest-compatible test suite
  config/settings/
    base.py            # JWT, CORS, CSRF, cookie settings
    dev.py             # Development overrides (insecure cookies OK)
    prod.py            # Production security hardening

frontend/src/
  api/axios.js              # Axios instance + 401 auto-refresh interceptor
  composables/useAuth.js    # Reactive auth state (login/register/logout/fetchUser)
  router/index.js           # Vue Router with navigation guards
  pages/LoginPage.vue       # Login form
  pages/RegisterPage.vue    # Registration form
  pages/ResetPasswordPage.vue # Password reset flow
  pages/ProfilePage.vue     # Authenticated user profile
```
