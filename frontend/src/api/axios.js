/**
 * Axios instance configured for cookie-based JWT authentication.
 *
 * Key security decisions:
 * - withCredentials: true → sends HTTP-only cookies cross-origin
 * - X-CSRFToken header is read from the csrftoken cookie (not HttpOnly)
 *   and attached to every mutating request (Django CSRF protection)
 * - On 401 response → attempt silent token refresh then retry original request
 * - On refresh failure → force logout + redirect to /login
 *
 * Tokens are NEVER stored in localStorage or sessionStorage.
 */
import axios from 'axios'

/** Read a cookie by name from document.cookie */
function getCookie(name) {
  const value = `; ${document.cookie}`
  const parts = value.split(`; ${name}=`)
  if (parts.length === 2) return parts.pop().split(';').shift()
  return null
}

const api = axios.create({
  baseURL: '/api',
  withCredentials: true, // Required to send HTTP-only cookies cross-origin
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
})

// ── Request interceptor ────────────────────────────────────────────────────
// Attach the CSRF token to every mutating request.
api.interceptors.request.use((config) => {
  const csrfToken = getCookie('csrftoken')
  if (csrfToken) {
    config.headers['X-CSRFToken'] = csrfToken
  }
  return config
})

// ── Response interceptor ───────────────────────────────────────────────────
let isRefreshing = false
let pendingRequests = [] // Queue requests while refreshing

/**
 * Resolve or reject all requests that were queued during a token refresh.
 * On success: each pending request is retried.
 * On failure: each pending request is rejected with the refresh error.
 */
function processQueue(error) {
  pendingRequests.forEach((prom) => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve()
    }
  })
  pendingRequests = []
}

/**
 * Force a clean logout:
 * - Reset user state in useAuth (avoid circular import → use custom event)
 * - Redirect to /login preserving the intended destination
 */
function forceLogout() {
  // Dispatch a global event that main.js / App.vue listens to
  window.dispatchEvent(new CustomEvent('auth:session-expired'))
  // Hard redirect to break any Vue state
  const currentPath = window.location.pathname
  if (currentPath !== '/login') {
    window.location.href = `/login?redirect=${encodeURIComponent(currentPath)}&reason=session_expired`
  }
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // Only handle 401 Unauthorized — and avoid infinite loops
    if (error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error)
    }

    // Don't try to refresh on auth endpoints themselves
    const authEndpoints = ['/auth/login/', '/auth/register/', '/auth/refresh/', '/auth/logout/']
    if (authEndpoints.some((ep) => originalRequest.url?.includes(ep))) {
      // A 401 on /auth/me/ or /auth/login/ means credentials are wrong — not a token issue
      return Promise.reject(error)
    }

    if (isRefreshing) {
      // Queue while a refresh is already in progress — retry once resolved
      return new Promise((resolve, reject) => {
        pendingRequests.push({ resolve, reject })
      })
        .then(() => api(originalRequest))
        .catch((err) => Promise.reject(err))
    }

    originalRequest._retry = true
    isRefreshing = true

    try {
      // Ask backend to rotate tokens using the HTTP-only refresh cookie
      await api.post('/auth/refresh/')
      isRefreshing = false
      processQueue(null)
      // Retry the original failed request with the new access token
      return api(originalRequest)
    } catch (refreshError) {
      isRefreshing = false
      processQueue(refreshError)

      // ── Refresh failed: both tokens are expired / invalid ──
      // Clear the user state and redirect to login.
      forceLogout()

      return Promise.reject(refreshError)
    }
  },
)

export default api
