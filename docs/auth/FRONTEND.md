# Frontend Authentication — Vue/Vite Implementation

## File Map

```
frontend/src/
  api/
    axios.js                    # Axios instance, CSRF injection, 401 auto-refresh
  composables/
    useAuth.js                  # Reactive auth state & all auth actions
  router/
    index.js                    # Vue Router with navigation guards
  pages/
    LoginPage.vue               # Login form
    RegisterPage.vue            # Registration form
    ResetPasswordPage.vue       # Password reset orchestrator
    ProfilePage.vue             # Authenticated user profile
  components/
    resetPassword/
      RequestResetForm.vue      # Step 1: enter email
      NewPasswordForm.vue       # Step 2: enter new password with token
      SuccessMessage.vue        # Confirmation step
```

---

## Axios Instance (`api/axios.js`)

A single shared Axios instance is used for all API calls. Key configuration:

```js
const api = axios.create({
  baseURL: '/api',              // Proxied to Django by Vite in dev
  withCredentials: true,        // Sends HTTP-only cookies cross-origin
})
```

### Request Interceptor
Reads the `csrftoken` cookie (not HttpOnly) and attaches it as `X-CSRFToken` to every request. This satisfies Django's CSRF protection without storing anything in application state.

### Response Interceptor (401 Auto-Refresh)
When any request returns `401 Unauthorized`:
1. Checks if this is an auth endpoint (login/register/logout/refresh) — if so, rejects immediately to avoid loops.
2. If a refresh is already in progress, queues the request in `pendingRequests[]`.
3. Otherwise, sends `POST /api/auth/refresh/` (browser automatically includes the `refresh_token` cookie).
4. On refresh success: sets `isRefreshing = false`, resolves the queue, retries the original request.
5. On refresh failure: calls `forceLogout()` which dispatches `auth:session-expired` event and hard-redirects to `/login?redirect=<path>&reason=session_expired`.

The queue mechanism prevents duplicate refresh calls when multiple requests fail simultaneously.

---

## Auth Composable (`composables/useAuth.js`)

The composable uses **module-level `ref`s** (not component-level), so auth state is shared globally across all component instances — effectively a singleton store without Vuex/Pinia.

```js
// Module-level — shared across all components
const user = ref(null)       // null = not authenticated
const isLoading = ref(false)
const error = ref(null)
```

### How the App Knows the User is Logged In

`isAuthenticated` is a computed property: `user.value !== null`. There is no boolean flag — if `user` is populated, the user is authenticated.

### Session Expiry Handler

```js
window.addEventListener('auth:session-expired', () => {
  user.value = null
  isLoading.value = false
  fetchPromise = null
})
```

This event is dispatched by `axios.js` when the refresh token fails. It resets auth state before the hard redirect so components don't render stale data.

### Key Functions

| Function | Endpoint | Effect |
|----------|---------|--------|
| `fetchUser()` | `GET /api/auth/me/` | Restores session from cookie on page load |
| `login(credentials)` | `POST /api/auth/login/` | Sets `user.value`, returns `{success, message}` |
| `register(formData)` | `POST /api/auth/register/` | Sets `user.value`, returns `{success, message}` |
| `logout()` | `POST /api/auth/logout/` | Clears `user.value` (even if request fails) |
| `updateProfile(data)` | `PATCH /api/auth/me/` | Updates `user.value` with response |
| `changePassword(pwData)` | `POST /api/auth/change-password/` | No state change on success |

### `fetchUser()` — Deduplication

```js
if (fetchPromise) return fetchPromise
```

If `fetchUser()` is called concurrently (e.g., from both the router guard and a component), only one HTTP request is made. Subsequent callers await the same promise.

### Error Handling in `login()`

```js
if (responseData?.code === 'ACCOUNT_INACTIVE') {
  error.value = responseData.message   // Show specific message for blocked accounts
}
```

The `ACCOUNT_INACTIVE` error code from the backend triggers a distinct UI message rather than a generic "invalid credentials" message.

---

## Vue Router (`router/index.js`)

### Route Meta Flags

| Meta field | Type | Meaning |
|-----------|------|---------|
| `requiresAuth: true` | boolean | Must be authenticated to access |
| `requiresAuth: false` | boolean | Public route (no check) |
| `guestOnly: true` | boolean | Redirect to dashboard if already authenticated |
| `roles: ["ADMIN"]` | string[] | Only users with these roles can access |

### Navigation Guard Logic

```
beforeEach(to)
  │
  ├─ 1. First load (user === null) → fetchUser() to restore session
  │      - Re-validates with backend every 15 min on protected routes
  │
  ├─ 2. requiresAuth && !isAuthenticated → { name: "Login", query: { redirect: to.fullPath } }
  │
  ├─ 3. guestOnly && isAuthenticated → getDashboardRedirect(user.role)
  │      (Prevents logged-in users accessing /login or /register)
  │
  ├─ 4. allowedRoles defined && user.role not in allowedRoles → getDashboardRedirect(user.role)
  │      (Role mismatch: silently redirect to own dashboard)
  │
  └─ 5. to.name === "Dashboard" && authenticated → getDashboardRedirect(user.role)
         (Generic /dashboard redirects to role-specific URL)
```

### Role-to-Dashboard Mapping

```js
function getDashboardRedirect(role) {
  switch (role) {
    case "ADMIN":      return { name: "AdminDashboard" }     // /admin
    case "CEO":        return { name: "ManagerDashboard" }   // /manager
    case "COMMERCIAL": return { name: "CommercialDashboard" } // /commercial
    default:           return { name: "Login" }
  }
}
```

---

## Login Page (`pages/LoginPage.vue`)

**Flow:**
1. User types email/password → client-side validation runs on submit.
2. `handleLogin()` calls `useAuth().login({ email, password })`.
3. On success: reads `route.query.redirect` (set by the guard on protected route access) and navigates there, or falls back to `/dashboard`.
4. `/dashboard` immediately redirects to the role-specific dashboard via guard rule #5.

**Note on "Remember me" checkbox:** The checkbox exists in the UI but currently has no backend effect — token lifetimes (10 min access, 7 day refresh) are fixed server-side.

**Note on Google SSO button:** The button is rendered but does not have a backend implementation. It is a UI placeholder.

---

## Register Page (`pages/RegisterPage.vue`)

**Flow:**
1. User fills name, email, password fields → client-side validation.
2. `handleRegister()` calls `useAuth().register(form)` (passes full form object).
3. On success: navigates to `/dashboard` → redirects to `CommercialDashboard` (new users always get `COMMERCIAL` role).

**Password strength indicator:** Client-side only scoring (length, uppercase, number, symbol). Backend applies Django's `AUTH_PASSWORD_VALIDATORS` independently.

---

## Password Reset Flow (`pages/ResetPasswordPage.vue`)

A multi-step form orchestrated by a `step` ref:
1. `request` → `RequestResetForm.vue` (enter email)
2. `sent` → `SuccessMessage.vue` (check your inbox)
3. `reset` → `NewPasswordForm.vue` (enter new password, token from URL query `?token=<uuid>`)
4. `success` → `SuccessMessage.vue` (password updated)

On mount, the page checks `route.query.token`. If present, it skips to step `reset` directly (handles the link from the email).

---

## How the Frontend Decides Auth State

| Question | How Answered |
|----------|-------------|
| Is user logged in? | `user.value !== null` (`isAuthenticated` computed) |
| What is the user's role? | `user.value.role` (string: `ADMIN`, `CEO`, `COMMERCIAL`) |
| Can user access a route? | `router/index.js` guard checks `to.meta.requiresAuth` and `to.meta.roles` |
| What happens after login? | Router navigates to `redirect` query param or role dashboard |
| What happens after logout? | `user.value = null`, navigate to `/login` |
| Token expired mid-session? | Axios interceptor silently refreshes; user sees nothing |
| Both tokens expired? | `forceLogout()` redirects to `/login?reason=session_expired` |

---

## Role-Based UI Visibility

Role-gated rendering in templates uses `user.value.role` directly:

```vue
<template>
  <div v-if="user?.role === 'ADMIN'">Admin-only content</div>
  <div v-else-if="user?.role === 'CEO'">CEO content</div>
</template>
```

Sidebar navigation items are conditionally rendered based on role. The actual filtering logic is distributed across role-specific sidebar components and the DashboardPage.

> **Critical reminder:** Frontend visibility is a UX convenience only. The backend API endpoints enforce access independently. A user who knows an API URL and has a valid token for the wrong role will be blocked by Django's `IsAdmin` permission (for admin endpoints). However, leads and other data endpoints rely primarily on frontend-only guards — see [SECURITY_NOTES.md](./SECURITY_NOTES.md).
