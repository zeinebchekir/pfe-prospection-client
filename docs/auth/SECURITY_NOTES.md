# Security Notes

> **Quick reference — things that MUST be fixed before production:**
>
> | # | Issue | Risk | Action |
> |---|-------|------|--------|
> | 1 | No backend role enforcement on leads/CEO endpoints | Medium-High | Add `IsCommercial`, `IsCEO` permission classes |
> | 2 | No rate limiting on login | Medium | Add `django-ratelimit` or Nginx rate limit |
> | 3 | SMTP password hardcoded in `base.py` | **High** | Move to env var, rotate the password immediately |
> | 4 | Google SSO button not implemented | Low | Remove the button or implement OAuth |
> | 5 | Self-registration is open (`AllowAny`) | Low | Add domain validation or disable if invite-only |
> | 6 | Password change does not revoke sessions | Low | Blacklist all user refresh tokens on password change |

---

## Current Security Model

The system uses **HTTP-only cookie JWT authentication** — a solid foundation that avoids the most common JWT pitfalls (XSS token theft via localStorage). This section documents both the strengths and the gaps that exist in the current implementation.

---

## What Is Well Implemented ✅

### Token Storage — XSS Resistance
Access and refresh tokens are stored exclusively in **HttpOnly cookies**. JavaScript (including injected malicious scripts) cannot read them via `document.cookie`. This is the most important XSS defense for token-based auth.

### Token Rotation with Blacklisting
`ROTATE_REFRESH_TOKENS = True` + `BLACKLIST_AFTER_ROTATION = True` means every refresh call invalidates the previous refresh token. If an old refresh token is presented after rotation, it will be rejected (it's in the blacklist).

### Short Access Token Lifetime
10-minute access tokens limit the window of damage if a token is somehow captured. The silent refresh extends sessions transparently.

### CSRF Protection (Active)
The `csrftoken` cookie (non-HttpOnly) allows Axios to inject `X-CSRFToken` headers. Django's `CsrfViewMiddleware` validates these on all mutating requests. This defends against CSRF attacks even with cookie-based auth.

### SameSite=Lax Cookies
Both auth cookies use `SameSite=Lax`. This means cookies are not sent on cross-site sub-requests (e.g., from a third-party site embedding content). Provides CSRF defense in depth alongside the explicit CSRF token.

### Admin Account Protection
Admins cannot be deleted or deactivated via the API. The `destroy()` and `toggle-active()` views explicitly check and reject requests targeting ADMIN accounts.

### Email Enumeration Prevention
`PasswordResetRequestView` always returns the same success message regardless of whether the email exists.

### Error Response Sanitization
The custom exception handler (`exceptions.py`) wraps all errors in a uniform format without exposing stack traces or internal details.

### Audit Logging
Login, logout, user creation, and user modification events are logged to the `audit_logs` table with user, action, target, IP, and timestamp.

### Production Settings Hardening (`settings/prod.py`)
- `AUTH_COOKIE_SECURE = True` — cookies only sent over HTTPS
- `SECURE_HSTS_SECONDS = 31536000` — forces HTTPS for 1 year
- `SECURE_SSL_REDIRECT = True` — redirects all HTTP to HTTPS
- `X_FRAME_OPTIONS = DENY` — prevents clickjacking
- `SECURE_CONTENT_TYPE_NOSNIFF = True`

---

## Known Gaps and Risks ⚠️

### 1. Leads API — No Role-Based Backend Enforcement

**Risk: Medium-High**

`/api/leads/*` endpoints use `IsAuthenticated` only. A CEO or ADMIN user with a valid access token can query commercial leads data through the API directly, bypassing frontend routing guards.

**Recommendation:** Add role-specific permission classes to sensitive leads endpoints. Example:
```python
class IsCommercial(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'COMMERCIAL'
```

### 2. No Rate Limiting on Login Endpoint

**Risk: Medium**

`/api/auth/login/` has no brute-force protection. An attacker can make unlimited password attempts.

**Recommendation:** Add `django-ratelimit` or configure rate limiting at the reverse proxy (Nginx) level:
```python
# Example with django-ratelimit
@ratelimit(key='ip', rate='10/m', method='POST', block=True)
def post(self, request): ...
```

### 3. Credential in Settings File

**Risk: High (if committed to version control)**

`base.py` contains a hardcoded Gmail SMTP password (`EMAIL_HOST_PASSWORD`). This credential is visible in the repository.

**Recommendation:** Move to an environment variable immediately:
```python
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
```
And rotate the exposed password.

### 4. Frontend-Only Role Enforcement for CEO/COMMERCIAL

**Risk: Low-Medium (internal threat model)**

CEO and COMMERCIAL route restrictions exist only in the Vue Router. A user who knows a direct API URL and holds a valid token of the wrong role can access those endpoints if the backend doesn't check role.

Currently only `ADMIN` endpoints are backend-enforced. This is acceptable for a trusted internal team but should be hardened for a production multi-tenant system.

### 5. Google SSO Button Has No Backend

**Risk: Low (UX confusion)**

The Google SSO button on the login page is a UI placeholder. Clicking it has no effect. It should either be removed or implemented. A partial OAuth implementation is worse than no button (users may try it and get confused).

### 6. Self-Registration Creates COMMERCIAL Accounts

**Risk: Low**

The `/register` endpoint is `AllowAny`, meaning anyone who knows the API can create a `COMMERCIAL` account. This may be intentional (open signup) or a risk depending on the intended deployment model.

**Recommendation:** If registration should be invite-only or admin-controlled, disable the `RegisterView` or add email domain validation.

### 7. No Refresh Token Revocation on Password Change

**Risk: Low**

Changing a password does not invalidate existing sessions. A user who suspects their account was compromised should manually log out, but existing refresh tokens remain valid until they expire (7 days).

**Recommendation:** On password change, call `RefreshToken(old_refresh).blacklist()` for all of the user's active sessions.

### 8. UserSession Table Not Actively Used

The `UserSession` model records session data but is not read during authentication decisions. Stale records may accumulate over time. Consider either removing this model or integrating it for session management (e.g., listing/revoking active sessions).

---

## Logout Behavior

Logout blacklists the current refresh token only. The access token (valid for 10 minutes) is not invalidated — there is no token revocation mechanism for access tokens (this is inherent to stateless JWTs). After logout, if someone has captured the access token cookie, they could use it for up to 10 minutes.

The cookie deletion on logout means the browser no longer sends the tokens automatically. For a stolen token scenario, the attacker would need to have already captured the raw cookie value.

---

## CORS Configuration

`CORS_ALLOW_CREDENTIALS = True` with explicit `CORS_ALLOWED_ORIGINS`. Avoid using `CORS_ALLOW_ALL_ORIGINS = True` in production — this would allow any origin to send authenticated requests.

---

## Production Deployment Checklist

- [ ] Set `COOKIE_SECURE=True` in environment (prod.py sets this automatically but verify `.env`)
- [ ] Configure `CORS_ALLOWED_ORIGINS` to production domain only
- [ ] Configure `CSRF_TRUSTED_ORIGINS` to production domain only
- [ ] Move `EMAIL_HOST_PASSWORD` to environment variable and rotate it
- [ ] Enable rate limiting on `/api/auth/login/` and `/api/auth/register/`
- [ ] Serve everything over HTTPS (HSTS is configured in prod.py)
- [ ] Consider adding role-based permissions to leads and other data endpoints
- [ ] Remove or implement the Google SSO button
- [ ] Set `DEBUG=False` (prod.py enforces this)
- [ ] Use a strong, randomly generated `SECRET_KEY` (used as JWT signing key)
- [ ] Review `ALLOWED_HOSTS` — must be set explicitly in production
