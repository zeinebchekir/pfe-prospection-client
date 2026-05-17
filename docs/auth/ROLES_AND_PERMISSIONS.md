# Roles and Permissions

## Role Definitions

The system has three roles defined as `TextChoices` on the `User` model:

| Role Value | Display Name | Default on Self-Register |
|-----------|-------------|--------------------------|
| `ADMIN` | Administrateur | No — must be created by another admin or via `create_superuser` |
| `CEO` | CEO | No — must be created by an admin |
| `COMMERCIAL` | Commercial | **Yes** — all self-registrations default to this role |

---

## Access Matrix

### Frontend Routes

| Route | ADMIN | CEO | COMMERCIAL | Public |
|-------|-------|-----|-----------|--------|
| `/` | ✅ | ✅ | ✅ | ✅ |
| `/login` | ↪ redirect | ↪ redirect | ↪ redirect | ✅ |
| `/register` | ↪ redirect | ↪ redirect | ↪ redirect | ✅ |
| `/reset-password` | ↪ redirect | ↪ redirect | ↪ redirect | ✅ |
| `/profil` | ✅ | ✅ | ✅ | ❌ |
| `/dashboard` | ↪ /admin | ↪ /manager | ↪ /commercial | ❌ |
| `/admin` | ✅ | ❌→/manager | ❌→/commercial | ❌ |
| `/admin/users` | ✅ | ❌ | ❌ | ❌ |
| `/admin/logs` | ✅ | ❌ | ❌ | ❌ |
| `/admin/monitoring-etl` | ✅ | ❌ | ❌ | ❌ |
| `/admin/reports` | ✅ | ❌ | ❌ | ❌ |
| `/admin/etllogs` | ✅ | ❌ | ❌ | ❌ |
| `/admin/crm` | ✅ | ❌ | ❌ | ❌ |
| `/manager` | ❌ | ✅ | ❌ | ❌ |
| `/manager/team` | ❌ | ✅ | ❌ | ❌ |
| `/manager/sync` | ❌ | ✅ | ❌ | ❌ |
| `/manager/reports` | ❌ | ✅ | ❌ | ❌ |
| `/manager/segmentation` | ❌ | ✅ | ❌ | ❌ |
| `/commercial` | ❌ | ❌ | ✅ | ❌ |
| `/commercial/leads` | ❌ | ❌ | ✅ | ❌ |
| `/commercial/leads/:id` | ❌ | ❌ | ✅ | ❌ |
| `/commercial/opportunities` | ❌ | ❌ | ✅ | ❌ |
| `/commercial/prospects` | ❌ | ❌ | ✅ | ❌ |
| `/commercial/qualify` | ❌ | ❌ | ✅ | ❌ |
| `/commercial/sync` | ❌ | ❌ | ✅ | ❌ |
| `/commercial/analyse-results` | ❌ | ❌ | ✅ | ❌ |

**↪ redirect** = authenticated users are sent to their role dashboard (no "Access Denied" page shown).
**❌** = redirected to role dashboard or `/login`.

### Backend API Endpoints

| Endpoint Group | Permission Class | Who Can Access |
|---------------|-----------------|----------------|
| `/api/auth/register/` | `AllowAny` | Anyone |
| `/api/auth/login/` | `AllowAny` | Anyone |
| `/api/auth/logout/` | `IsAuthenticated` | Any authenticated user |
| `/api/auth/refresh/` | `AllowAny` | Anyone (with valid refresh cookie) |
| `/api/auth/me/` | `IsAuthenticated` | Any authenticated user |
| `/api/auth/change-password/` | `IsAuthenticated` | Any authenticated user |
| `/api/auth/password-reset/` | `AllowAny` | Anyone |
| `/api/auth/password-reset/confirm/` | `AllowAny` | Anyone |
| `/api/auth/admin/users/` | `IsAdmin` | ADMIN only |
| `/api/auth/admin/users/<uuid>/` | `IsAdmin` | ADMIN only |
| `/api/auth/admin/users/<uuid>/toggle-active/` | `IsAdmin` | ADMIN only |
| `/api/audit/` | `IsAdmin` | ADMIN only |
| `/api/leads/` | `IsAuthenticated` | **Any authenticated user** (no role filter at API level) |

> ⚠️ **Gap**: Leads endpoints are only protected by `IsAuthenticated`, not by role. A CEO or ADMIN with a valid token can access commercial leads data via the API directly. See [SECURITY_NOTES.md](./SECURITY_NOTES.md).

---

## How Role is Stored

The `role` field is a plain `CharField` on the `User` model, persisted in the `users` table in PostgreSQL. It is set at creation time and can only be changed by an ADMIN via `PATCH /api/auth/admin/users/<uuid>/`.

---

## How Role Reaches the Frontend

The role is included in every auth response (`login`, `register`, `me`) inside the `user` object:

```json
{
  "status": "success",
  "user": {
    "id": "...",
    "email": "...",
    "role": "COMMERCIAL",
    ...
  }
}
```

The `useAuth` composable stores this in `user.value.role`. The router and UI components read from there. **The role is never stored in a cookie or localStorage** — it is re-fetched from the backend via `GET /api/auth/me/` on every page load.

---

## How Role is Checked in Router Guards

In `router/index.js`:

```js
const allowedRoles = to.meta.roles  // e.g., ["ADMIN"]

if (requiresAuth && allowedRoles && (!user.value || !allowedRoles.includes(user.value.role))) {
  return getDashboardRedirect(user.value?.role)
}
```

If `to.meta.roles` is not defined, any authenticated user can access the route (e.g., `/profil`).

---

## Role Details

### ADMIN

**Purpose:** System administrator. Manages users, views audit logs, monitors ETL pipeline.

**Accessible pages:** All `/admin/*` routes, `/profil`, generic `/dashboard` (redirected to `/admin`).

**Backend enforcement:** `IsAdmin` permission class guards all `/api/auth/admin/*` and `/api/audit/*` endpoints.

**Cannot:** Access `/manager/*` or `/commercial/*` routes (redirected to `/admin`).

**Special rules:**
- Cannot be deleted via the API (`destroy()` returns `403`)
- Cannot be deactivated via `toggle-active/` (returns `403`)
- Not listed in `GET /api/auth/admin/users/` (excluded from queryset)

---

### CEO (Manager)

**Purpose:** Executive/manager. Accesses market analysis, segmentation, team and report dashboards.

**Accessible pages:** `/manager`, `/manager/team`, `/manager/sync`, `/manager/reports`, `/manager/segmentation`, `/profil`.

**Backend enforcement:** None beyond `IsAuthenticated` on most endpoints. The manager role is currently enforced only at the frontend routing level.

**Cannot:** Access `/admin/*` or `/commercial/*`.

---

### COMMERCIAL

**Purpose:** Sales representative. Manages leads, opportunities, and qualification.

**Accessible pages:** `/commercial`, `/commercial/leads`, `/commercial/leads/:id`, `/commercial/opportunities`, `/commercial/prospects`, `/commercial/qualify`, `/commercial/sync`, `/commercial/analyse-results`, `/profil`.

**Backend enforcement:** None beyond `IsAuthenticated`. Commercial role is enforced at the frontend level only.

**Default role:** All self-registered users receive this role automatically.

---

## How to Add a New Role Safely

1. **Backend — `models.py`:** Add the new value to `User.Role`:
   ```python
   class Role(models.TextChoices):
       ANALYST = 'ANALYST', 'Analyste'
   ```

2. **Backend — Create a migration:**
   ```bash
   python manage.py makemigrations users
   python manage.py migrate
   ```

3. **Backend — Permissions (if needed):** Create a new permission class in `permissions.py`:
   ```python
   class IsAnalyst(permissions.BasePermission):
       def has_permission(self, request, view):
           return bool(request.user and request.user.is_authenticated and request.user.role == 'ANALYST')
   ```

4. **Backend — Apply to views:** Add `permission_classes = [IsAnalyst]` to relevant views.

5. **Frontend — Router:** Add routes with `meta: { requiresAuth: true, roles: ["ANALYST"] }`.

6. **Frontend — `getDashboardRedirect()`:** Add a case for the new role:
   ```js
   case "ANALYST": return { name: "AnalystDashboard" }
   ```

7. **Frontend — UI:** Add sidebar items and dashboard components for the new role.

8. **Admin UI:** Ensure the admin user creation form includes the new role as an option.
