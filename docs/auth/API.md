# Auth API Reference

Base URL: `http://localhost:8000/api/auth/` (development)

All endpoints return JSON. All mutating requests require the CSRF token in the `X-CSRFToken` header (automatically handled by the Axios interceptor).

---

## Endpoints Summary

| Method | Path | Auth Required | Description |
|--------|------|--------------|-------------|
| `POST` | `/api/auth/register/` | No | Create new account |
| `POST` | `/api/auth/login/` | No | Authenticate, receive cookies |
| `POST` | `/api/auth/logout/` | Yes | Blacklist token, clear cookies |
| `POST` | `/api/auth/refresh/` | No (cookie) | Rotate token pair |
| `GET` | `/api/auth/me/` | Yes | Get current user profile |
| `PATCH` | `/api/auth/me/` | Yes | Update current user profile |
| `POST` | `/api/auth/change-password/` | Yes | Change own password |
| `POST` | `/api/auth/password-reset/` | No | Request password reset email |
| `POST` | `/api/auth/password-reset/confirm/` | No | Confirm reset with token |
| `GET` | `/api/auth/admin/users/` | ADMIN only | List all users |
| `POST` | `/api/auth/admin/users/` | ADMIN only | Create user (admin) |
| `GET/PATCH/DELETE` | `/api/auth/admin/users/<uuid>/` | ADMIN only | User CRUD |
| `PATCH` | `/api/auth/admin/users/<uuid>/toggle-active/` | ADMIN only | Toggle active status |

---

## POST /api/auth/register/

Create a new user account. Role is always set to `COMMERCIAL`.

**Auth required:** No

**Request body:**
```json
{
  "email": "jean.dupont@example.com",
  "nom": "Dupont",
  "prenom": "Jean",
  "password": "SecurePass123!",
  "password2": "SecurePass123!"
}
```

**Success response (201 Created):**
```json
{
  "status": "success",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "jean.dupont@example.com",
    "nom": "Dupont",
    "prenom": "Jean",
    "role": "COMMERCIAL",
    "full_name": "Jean Dupont",
    "fonction": ""
  }
}
```

Sets HTTP-only cookies: `access_token` (10 min), `refresh_token` (7 days).

**Error responses:** `400` — duplicate email, password mismatch, weak password.

```bash
curl -c cookies.txt -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","nom":"Test","prenom":"User","password":"SecurePass123!","password2":"SecurePass123!"}'
```

---

## POST /api/auth/login/

**Auth required:** No

**Request body:**
```json
{ "email": "jean.dupont@example.com", "password": "SecurePass123!" }
```

**Success response (200 OK):** Same `user` object as register. Sets HTTP-only cookies. Writes `LOGIN` audit log.

**Error responses:**
| Status | Code | Cause |
|--------|------|-------|
| 401 | — | Wrong email or password |
| 403 | `ACCOUNT_INACTIVE` | Account disabled by admin |

```bash
curl -c cookies.txt -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"SecurePass123!"}'
```

---

## POST /api/auth/logout/

Blacklist refresh token, clear cookies, write `LOGOUT` audit log.

**Auth required:** Yes

**Response (200 OK):**
```json
{ "status": "success", "message": "Déconnexion réussie." }
```

---

## POST /api/auth/refresh/

Exchange refresh token cookie for a new access + refresh token pair (rotation). The old refresh token is blacklisted immediately.

**Auth required:** No (uses `refresh_token` cookie)

**Response (200 OK):**
```json
{ "status": "success", "message": "Token refreshed." }
```

**Error:** `401` — no cookie, expired, or blacklisted token.

---

## GET /api/auth/me/

Return authenticated user's profile. Password is never included.

**Auth required:** Yes

**Response (200 OK):**
```json
{
  "status": "success",
  "user": {
    "id": "...", "email": "...", "nom": "...", "prenom": "...",
    "role": "COMMERCIAL", "full_name": "...", "fonction": "..."
  }
}
```

---

## PATCH /api/auth/me/

Update own profile. Only `nom`, `prenom`, `fonction` are editable. `role` and `email` are read-only via this endpoint.

**Auth required:** Yes

**Request body (partial):**
```json
{ "prenom": "Jean-Pierre", "fonction": "Senior Account Manager" }
```

---

## POST /api/auth/change-password/

**Auth required:** Yes

**Request body:**
```json
{
  "old_password": "OldPass123!",
  "new_password": "NewPass456!",
  "confirm_password": "NewPass456!"
}
```

**Error:** `400` — old password incorrect, mismatch, or weak new password.

---

## POST /api/auth/password-reset/

Request a reset email. Always returns success to prevent email enumeration.

**Auth required:** No

**Request body:** `{ "email": "user@example.com" }`

**Response:** `{ "status": "success", "message": "Si l'email existe, un lien de réinitialisation a été envoyé." }`

Token expires in **24 hours**. Link format: `<FRONTEND_URL>/reset-password?token=<uuid>`

> In `DEBUG=True`, if email sending fails, `token_debug` is included in the response.

---

## POST /api/auth/password-reset/confirm/

**Auth required:** No

**Request body:**
```json
{
  "token": "550e8400-e29b-41d4-a716-446655440000",
  "password": "NewPass456!",
  "password2": "NewPass456!"
}
```

**Error:** `400` — token expired, already used, or passwords don't match.

---

## Admin User Management Endpoints

All require `ADMIN` role.

### GET /api/auth/admin/users/

Query params: `role`, `is_active`, `search` (name/email).

### POST /api/auth/admin/users/

```json
{ "email": "...", "nom": "...", "prenom": "...", "role": "CEO", "password": "...", "is_active": true }
```

### GET|PATCH|DELETE /api/auth/admin/users/\<uuid\>/

- `PATCH` accepts: `nom`, `prenom`, `email`, `role`, `is_active`, `fonction`
- `DELETE` is blocked on ADMIN accounts (returns `403`)

### PATCH /api/auth/admin/users/\<uuid\>/toggle-active/

Toggles `is_active`. Blocked on ADMIN accounts.

**Response:** `{ "message": "Utilisateur activé.", "is_active": true }`

---

## Standard Error Format

```json
{
  "status": "error",
  "code": 400,
  "errors": { "email": ["This field is required."] }
}
```
