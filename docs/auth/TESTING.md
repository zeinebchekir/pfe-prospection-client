# Auth Testing Guide

## Prerequisites

- Docker running (`docker-compose up`)  
  OR Django dev server + Postgres running locally
- Frontend dev server running (`cd frontend && npm run dev`)

---

## 1. Running Automated Backend Tests

```bash
# From the backend container or locally
cd backend
python manage.py test apps.users.tests

# Run with verbose output
python manage.py test apps.users.tests -v 2

# Run a specific test class
python manage.py test apps.users.tests.TestLogin

# Run a specific test
python manage.py test apps.users.tests.TestLogin.test_login_wrong_password_returns_401
```

Test classes in `apps/users/tests.py`:

| Class | Tests |
|-------|-------|
| `TestRegister` | Success (201 + cookies), duplicate email, password mismatch, weak password, missing fields |
| `TestLogin` | Valid credentials (200 + cookies), wrong password (401), inactive user (403) |
| `TestLogout` | Authenticated logout (200 + cleared cookies), unauthenticated (401) |
| `TestRefresh` | Valid cookie (200 + new cookies), no cookie (401), invalid token (401) |
| `TestMe` | Valid cookie returns profile, no cookie (401), password not in response |

---

## 2. Manual Testing with curl

All curl examples below store/send cookies via `cookies.txt`.

### Register a New User

```bash
curl -c cookies.txt -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "nom": "Test",
    "prenom": "User",
    "password": "SecurePass123!",
    "password2": "SecurePass123!"
  }'
# Expected: 201, user object, Set-Cookie headers
```

### Login

```bash
curl -c cookies.txt -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "SecurePass123!"}'
# Expected: 200, user object with role, Set-Cookie headers
```

### Get Current User

```bash
curl -b cookies.txt http://localhost:8000/api/auth/me/
# Expected: 200, user profile without password field
```

### Refresh Tokens

```bash
curl -b cookies.txt -c cookies.txt -X POST http://localhost:8000/api/auth/refresh/
# Expected: 200, new Set-Cookie headers (rotated tokens)
```

### Logout

```bash
# First get CSRF token
CSRF=$(grep csrftoken cookies.txt | awk '{print $7}')

curl -b cookies.txt -c cookies.txt -X POST http://localhost:8000/api/auth/logout/ \
  -H "X-CSRFToken: $CSRF"
# Expected: 200, cookies cleared (empty value in response)
```

### Access Protected Route Without Auth

```bash
curl http://localhost:8000/api/auth/me/
# Expected: 401 Unauthorized
```

### Test Wrong Password

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "WrongPassword!"}'
# Expected: 401 {"status":"error","message":"Email ou mot de passe invalide."}
```

### Test Inactive Account

```bash
# First deactivate via admin panel or Django shell
# python manage.py shell
# User.objects.filter(email="test@example.com").update(is_active=False)

curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "SecurePass123!"}'
# Expected: 403 {"status":"error","code":"ACCOUNT_INACTIVE","message":"Votre accès est bloqué..."}
```

### Test Admin-Only Endpoint Without ADMIN Role

```bash
# Login as COMMERCIAL user first (saves cookies)
curl -b cookies.txt http://localhost:8000/api/auth/admin/users/
# Expected: 403 Forbidden
```

### Test Password Reset Flow

```bash
# 1. Request reset
curl -X POST http://localhost:8000/api/auth/password-reset/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
# Expected: 200 (same message whether email exists or not)

# 2. In DEBUG mode, check the token from the response or Django console
# token_debug: "<uuid>" will be in the response if email sending fails

# 3. Confirm reset
curl -X POST http://localhost:8000/api/auth/password-reset/confirm/ \
  -H "Content-Type: application/json" \
  -d '{
    "token": "<uuid-from-step-2>",
    "password": "NewSecurePass456!",
    "password2": "NewSecurePass456!"
  }'
# Expected: 200 success
```

---

## 3. Manual Frontend Testing

### Basic Login/Logout Flow

1. Navigate to `http://localhost:5173/login`
2. Enter valid credentials → should redirect to role-specific dashboard
3. Open browser DevTools → Application → Cookies — verify `access_token` and `refresh_token` are present and marked HttpOnly
4. Click logout → verify cookies are removed, redirected to `/login`

### Protected Route Test

1. Without logging in, navigate to `http://localhost:5173/commercial`
2. Should redirect to `/login?redirect=%2Fcommercial`
3. Login → should redirect back to `/commercial`

### Role-Based Route Test

1. Login as COMMERCIAL user
2. Try to navigate to `http://localhost:5173/admin` manually (change URL)
3. Should be redirected to `/commercial` (no "Access Denied" page)

### Token Expiry Simulation

1. Login and open DevTools → Application → Cookies
2. Delete `access_token` cookie (keep `refresh_token`)
3. Make any API call (e.g., navigate to a page that fetches data)
4. Observe: Axios interceptor calls `/api/auth/refresh/`, gets new access token, retries request transparently
5. The user should see no error — the page loads normally

### Full Session Expiry Test

1. Login
2. Delete **both** `access_token` and `refresh_token` cookies
3. Navigate to a protected page
4. Should redirect to `/login?redirect=<page>&reason=session_expired`

---

## 4. Testing with Postman/Insomnia

1. Create a collection for `http://localhost:8000/api/auth/`
2. In collection settings: enable "Send cookies" and use a cookie jar
3. Send `POST /api/auth/login/` — cookies will be stored automatically
4. All subsequent requests will automatically include cookies

---

## 5. Common Errors and Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `401` on any request after login | Access token expired, refresh failed, or no cookie | Check cookies in DevTools; try logout + login again |
| `403 ACCOUNT_INACTIVE` on login | Account deactivated by admin | Admin must enable account via `/api/auth/admin/users/<uuid>/toggle-active/` |
| `400 email already exists` | Duplicate registration | Use a different email or log in |
| `400 passwords don't match` | `password` ≠ `password2` | Client-side validation should catch this first |
| `400 This password is too short` | Password < 8 characters | Use a stronger password |
| `400 This password is too common` | Django `CommonPasswordValidator` | Use a less common password |
| `401 No refresh token` on refresh | Refresh cookie missing or expired | Login again |
| CORS error in browser | Frontend origin not in `CORS_ALLOWED_ORIGINS` | Check `.env` `CORS_ALLOWED_ORIGINS` includes `http://localhost:5173` |
| CSRF verification failed | Missing `X-CSRFToken` header | Check Axios interceptor is reading `csrftoken` cookie correctly |
| `403` on `/api/auth/admin/users/` | User is not ADMIN | Only ADMIN role can access this endpoint |
| Login redirects to `/login` again | `fetchUser()` failed after login | Check backend is running; check browser console for errors |

---

## 6. Creating Test Users via Django Shell

```python
# python manage.py shell
from apps.users.models import User

# Create admin
User.objects.create_superuser(
    email='admin@example.com',
    password='AdminPass123!',
    nom='Admin',
    prenom='System'
)

# Create CEO
User.objects.create_user(
    email='ceo@example.com',
    password='CeoPass123!',
    nom='CEO',
    prenom='User',
    role=User.Role.CEO
)

# Create COMMERCIAL (default role)
User.objects.create_user(
    email='commercial@example.com',
    password='CommPass123!',
    nom='Commercial',
    prenom='User'
)
```

---

## 7. Checking Audit Logs

```bash
# As ADMIN, query audit logs
curl -b cookies.txt "http://localhost:8000/api/audit/?action=LOGIN"

# Filter by user
curl -b cookies.txt "http://localhost:8000/api/audit/?target=test@example.com"
```

Or via Django admin: `http://localhost:8000/admin/` → Audit Logs.
