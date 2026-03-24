/**
 * Axios instance configured for cookie-based JWT authentication.
 *
 * Key security decisions:
 * - withCredentials: true → sends HTTP-only cookies cross-origin
 * - X-CSRFToken header is read from the csrftoken cookie (not HttpOnly)
 *   and attached to every mutating request (Django CSRF protection)
 * - On 401 response → attempt silent token refresh then retry original request
 * - On refresh failure → redirect to login (clears expired session)
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
// Django sets a csrftoken cookie (NOT HttpOnly) that we can read here.
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
      return Promise.reject(error)
    }

    if (isRefreshing) {
      // Queue while a refresh is already in progress
      return new Promise((resolve, reject) => {
        pendingRequests.push({ resolve, reject })
      })
        .then(() => api(originalRequest))
        .catch((err) => Promise.reject(err))
    }

    originalRequest._retry = true
    isRefreshing = true

    try {
      await api.post('/auth/refresh/')
      isRefreshing = false
      processQueue(null)
      return api(originalRequest)
    } catch (refreshError) {
      isRefreshing = false
      processQueue(refreshError)
      
      // Refresh failed — session is dead. 
      // We don't redirect here to avoid circular dependency with router.
      // The calling code (like router guards or useAuth) should handle the failure.
      
      return Promise.reject(refreshError)
    }
  },
)

export default api
