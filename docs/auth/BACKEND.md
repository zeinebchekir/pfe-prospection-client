# Backend Authentication — Django Implementation

## File Map

```
backend/
  apps/users/
    models.py          # User, UserSession, PasswordResetToken
    views.py           # All auth views + @extend_schema decorators
    serializers.py     # Request/response validation + help_text fields
    authentication.py  # CookieJWTAuthentication (reads JWT from cookie)
    permissions.py     # IsAdmin custom permission
    utils.py           # set_auth_cookies / unset_auth_cookies helpers
    exceptions.py      # Custom DRF exception handler
    urls.py            # /api/auth/* URL patterns
    tests.py           # pytest-compatible test suite
  config/settings/
    base.py            # JWT, CORS, CSRF, cookie settings, SPECTACULAR_SETTINGS
    dev.py             # Development overrides (insecure cookies OK)
    prod.py            # Production security hardening
  config/
    urls.py            # Root URL config including /api/docs/ /api/redoc/ /api/schema/
```

---

## Swagger / OpenAPI Setup

The project uses [`drf-spectacular`](https://github.com/tfranzel/drf-spectacular) (v0.27.2) for OpenAPI 3.0 schema generation.

### Access Points

| URL | Interface |
|-----|-----------|
| `GET /api/docs/` | Swagger UI (interactive, try requests) |
| `GET /api/redoc/` | Redoc (clean read-only documentation) |
| `GET /api/schema/` | Raw OpenAPI JSON/YAML |

### How Decorators Work

Each view has a `@extend_schema` or `@extend_schema_view` decorator added **above** the class definition. These decorators add only metadata — they do not change view behavior, routing, or authentication logic.

```python
@extend_schema(
    tags=["Authentication"],
    summary="Authenticate user (login)",
    description="...",
    request=LoginSerializer,
    responses={200: ..., 401: ..., 403: ...}
)
class LoginView(APIView):
    ...
```

The decorator is processed by `drf-spectacular` at schema generation time (when `/api/schema/` is accessed). At runtime, the decorator has zero overhead.

### Serializer Field Descriptions

All serializer fields have `help_text` set. These appear as field descriptions in Swagger UI's request body schemas, making it clear what each field expects without reading the source code.

### Cookie Auth in Swagger

> **Important:** Swagger UI cannot automatically send HTTP-only cookies. The `cookieAuth` security scheme is defined in `SPECTACULAR_SETTINGS` but browsers prevent Swagger from attaching cookies set by a different origin.
>
> **Workaround to test authenticated endpoints in Swagger:**
> 1. Open `http://localhost:8000/api/docs/` in Chrome/Firefox.
> 2. In DevTools Console: `fetch('/api/auth/login/', {method:'POST', credentials:'include', headers:{'Content-Type':'application/json'}, body:'{"email":"...","password":"..."}'})`
> 3. Cookies are now set. Click "Try it out" in Swagger — cookies will be sent automatically by the browser.

---

## User Model (`apps/users/models.py`)

### `User` (extends `AbstractBaseUser`, `PermissionsMixin`)

Django's default user model is replaced entirely. Authentication is via email (not username).

| Field | Type | Notes |
|-------|------|-------|
| `id` | `UUIDField` | Primary key, auto-generated |
| `email` | `EmailField` | Unique, used as `USERNAME_FIELD` |
| `nom` | `CharField` | Last name |
| `prenom` | `CharField` | First name |
| `role` | `CharField` | Choices: `ADMIN`, `CEO`, `COMMERCIAL`. Default: `COMMERCIAL` |
| `fonction` | `CharField` | Job title, optional |
| `equipe_id` | `UUIDField` | Team reference, optional |
| `is_active` | `BooleanField` | Controls login access |
| `is_staff` | `BooleanField` | Django admin access |
| `date_creation` | `DateTimeField` | Account creation timestamp |
| `last_login` | `DateTimeField` | Updated by `SimpleJWT` (`UPDATE_LAST_LOGIN = True`) |

**Role methods:** `is_admin()`, `is_ceo()`, `is_commercial()` — convenience helpers.

**`UserManager`:** Overrides `create_user` to normalize email and use `set_password` (bcrypt via Django default). `create_superuser` forces role `ADMIN`.

### `UserSession`
Tracks refresh tokens per user with IP and user-agent. Currently persisted but not actively queried for auth decisions (SimpleJWT blacklist handles invalidation).

### `PasswordResetToken`
UUID-based one-time token. Expires in 24 hours. `is_valid` property checks both `est_utilise` and `expire_le`.

---

## Authentication Backend (`apps/users/authentication.py`)

**`CookieJWTAuthentication`** extends `rest_framework_simplejwt.authentication.JWTAuthentication`.

Overrides `authenticate()` to read the access token from the `access_token` cookie instead of the `Authorization` header.

```
Request arrives
    │
    ├─ Cookie `access_token` absent → return None (anonymous)
    │
    ├─ Token present but invalid/expired → return None (let permissions deny)
    │
    └─ Token valid → return (user, validated_token)
```

Configured as the **global default** in `REST_FRAMEWORK`:
```python
"DEFAULT_AUTHENTICATION_CLASSES": ["apps.users.authentication.CookieJWTAuthentication"]
```

---

## Views (`apps/users/views.py`)

### `RegisterView` — `POST /api/auth/register/`
- `permission_classes = [AllowAny]`, `authentication_classes = []`
- Validates via `RegisterSerializer` (email unique, passwords match, Django password validators)
- Creates user with `User.objects.create_user(...)` which calls `set_password()` (bcrypt)
- Generates JWT pair with `RefreshToken.for_user(user)`
- Calls `set_auth_cookies(response, access, refresh)`

### `LoginView` — `POST /api/auth/login/`
- `permission_classes = [AllowAny]`, `authentication_classes = []`
- Uses Django's `authenticate(request, email, password)` which checks password hash
- Distinguishes inactive accounts (403) from wrong credentials (401)
- Generates JWT pair, sets cookies, writes audit log

### `LogoutView` — `POST /api/auth/logout/`
- `permission_classes = [IsAuthenticated]`
- Reads refresh token from `request.COOKIES[AUTH_COOKIE_REFRESH]`
- Calls `token.blacklist()` — adds to SimpleJWT blacklist table
- Calls `unset_auth_cookies(response)` — deletes cookies client-side
- Writes audit log

### `RefreshView` — `POST /api/auth/refresh/`
- `permission_classes = [AllowAny]`, `authentication_classes = []`
- Reads refresh cookie, validates with `RefreshToken(token)`
- Issues new access + refresh (rotation); old refresh is blacklisted due to `BLACKLIST_AFTER_ROTATION = True`

### `MeView` — `GET|PATCH /api/auth/me/`
- `permission_classes = [IsAuthenticated]`
- `GET`: returns `UserProfileSerializer(request.user).data`
- `PATCH`: uses `ProfileUpdateSerializer` (only `nom`, `prenom`, `fonction`)

### `ChangePasswordView` — `POST /api/auth/change-password/`
- Verifies old password with `user.check_password()`
- Sets new password with `user.set_password()` (rehashes)

### `PasswordResetRequestView` — `POST /api/auth/password-reset/`
- Always returns success message (prevents email enumeration)
- Creates `PasswordResetToken` record (24h expiry)
- Sends reset email via Django SMTP (`send_mail`)

### `PasswordResetConfirmView` — `POST /api/auth/password-reset/confirm/`
- Validates UUID token, checks `is_valid` property
- Sets new password, marks token `est_utilise = True`

### Admin views (`UserListCreateView`, `UserDetailView`, `ToggleUserActiveView`)
- All require `IsAdmin` permission
- `UserListCreateView.get_queryset()` excludes ADMIN accounts from listing
- `destroy()` prevents deletion of ADMIN accounts (returns 403)
- All mutations write to `audit_logs`

---

## Serializers (`apps/users/serializers.py`)

| Serializer | Used By | Editable Fields |
|-----------|---------|----------------|
| `LoginSerializer` | `LoginView` | `email`, `password` |
| `RegisterSerializer` | `RegisterView` | `email`, `nom`, `prenom`, `password`, `password2` |
| `UserProfileSerializer` | `MeView` GET, login/register response | Read-only profile |
| `ProfileUpdateSerializer` | `MeView` PATCH | `nom`, `prenom`, `fonction` |
| `UserSerializer` | Admin list/detail | Full user read |
| `UserCreateSerializer` | Admin create | All fields + password |
| `UserUpdateSerializer` | Admin update | `nom`, `prenom`, `email`, `role`, `is_active`, `fonction` |
| `ChangePasswordSerializer` | `ChangePasswordView` | `old_password`, `new_password`, `confirm_password` |
| `PasswordResetRequestSerializer` | Reset request | `email` |
| `PasswordResetConfirmSerializer` | Reset confirm | `token`, `password`, `password2` |

Password fields use `validators=[validate_password]` (Django's built-in strength checker).

---

## Permissions (`apps/users/permissions.py`)

**`IsAdmin`**: Grants access only if `request.user.is_authenticated` and `request.user.role == 'ADMIN'`.

The default global permission is `IsAuthenticated` (configured in `REST_FRAMEWORK`). Views that need to be public override with `permission_classes = [AllowAny]`.

There is currently **no `IsCEO` or `IsCommercial` permission class**. Role-based access to leads and other data is enforced via frontend routing guards, not backend permissions — see [SECURITY_NOTES.md](./SECURITY_NOTES.md).

---

## Cookie Utilities (`apps/users/utils.py`)

`set_auth_cookies(response, access_token, refresh_token)` — attaches tokens as HTTP-only cookies using settings:
- `httponly = True` — JavaScript cannot read these cookies
- `secure = AUTH_COOKIE_SECURE` — `False` in dev, `True` in production
- `samesite = "Lax"` — sent on same-site requests and top-level navigations; not on cross-site sub-requests
- `path = "/"` — available to all routes
- `max_age`: access = 600s (10 min), refresh = 604800s (7 days)

`unset_auth_cookies(response)` — calls `delete_cookie()` which sets the cookie to empty string with `max_age=0`.

---

## JWT Settings (`config/settings/base.py`)

```python
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=10),   # Short-lived; auto-refreshed
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,          # Each refresh issues a new refresh token
    "BLACKLIST_AFTER_ROTATION": True,       # Old refresh token invalidated immediately
    "UPDATE_LAST_LOGIN": True,              # Updates User.last_login on token issue
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,             # Uses Django SECRET_KEY
    "USER_ID_FIELD": "id",                 # UUIDs stored in token claims
    "USER_ID_CLAIM": "user_id",
}
```

Cookie names: `access_token`, `refresh_token` (configurable via `AUTH_COOKIE_ACCESS` / `AUTH_COOKIE_REFRESH`).

---

## CORS Settings

```python
CORS_ALLOW_CREDENTIALS = True          # Required for cookie-based auth cross-origin
CORS_ALLOWED_ORIGINS = [...]           # From CORS_ALLOWED_ORIGINS env var
```

`CORS_ALLOW_CREDENTIALS = True` is critical — without it, browsers block cross-origin cookie transmission.

---

## CSRF Settings

```python
CSRF_COOKIE_HTTPONLY = False    # Axios must read csrftoken cookie to send X-CSRFToken header
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_TRUSTED_ORIGINS = [...]   # From env var
```

The `csrftoken` cookie is **not** HttpOnly (unlike auth tokens) so that the frontend JavaScript can read it and attach it to the `X-CSRFToken` request header. Django's CSRF middleware validates this on mutating requests.

---

## Password Hashing

Django uses PBKDF2-SHA256 by default (configured in `AUTH_PASSWORD_VALIDATORS`). `set_password()` handles the hashing. Passwords are never stored in plaintext. The response serializers explicitly exclude password fields.

---

## Login Flow Step by Step

1. `LoginSerializer` validates that `email` and `password` are present.
2. `authenticate(request, email=email, password=password)` checks credentials against the DB using Django's auth backend (PBKDF2 comparison).
3. If `None` returned, check if user exists but is inactive → `403 ACCOUNT_INACTIVE`.
4. Otherwise → `401 Invalid credentials`.
5. On success: `RefreshToken.for_user(user)` issues a signed JWT pair.
6. `set_auth_cookies()` writes both as HTTP-only cookies.
7. `UserProfileSerializer(user).data` is returned in the response body (no tokens).
8. `log_action(LOGIN)` writes to `audit_logs`.

---

## Audit Logging

The `apps/audit` app logs auth events automatically. Events: `LOGIN`, `LOGOUT`, `CREATE`, `UPDATE`, `DELETE`.

Each log entry captures: `user`, `action`, `target` (email), `ip_address` (from `X-Forwarded-For` or `REMOTE_ADDR`), `details` (JSON), `timestamp`.

The `AuditLogListView` at `/api/audit/` is accessible to ADMIN only.
