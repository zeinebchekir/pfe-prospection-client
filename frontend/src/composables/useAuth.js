/**
 * useAuth composable — centralised auth state management.
 *
 * - user: reactive User object or null
 * - isAuthenticated: computed boolean
 * - isLoading: true while fetching session on app load
 * - error: last error message or null
 *
 * Tokens are never touched by this composable — they live exclusively
 * in HTTP-only cookies managed by the browser and backend.
 */
import { ref, computed } from 'vue'
import api from '@/api/axios'

// Module-level reactive state — shared as a singleton across all component usages.
// Using module scope (not inside the function) ensures all components share the same
// user object and react to the same mutations, equivalent to a global Pinia store.
const user = ref(null)       // null means not authenticated
const isLoading = ref(false)  // true only during async auth operations
const error = ref(null)       // last auth error message or null
let fetchPromise = null        // deduplicates concurrent fetchUser() calls

// ── Session expiry handler ────────────────────────────────────────────────
// Fired by axios.js when the refresh token is also expired/invalid.
// Clears user state immediately before the hard redirect to /login.
if (typeof window !== 'undefined') {
  window.addEventListener('auth:session-expired', () => {
    user.value = null
    isLoading.value = false
    fetchPromise = null
  })
}

export function useAuth() {
  const isAuthenticated = computed(() => user.value !== null)

  /**
   * Fetch the current user from /api/auth/me/.
   *
   * Called by the router guard on first load and periodically on protected routes
   * to restore and verify session state from the HTTP-only cookie.
   * Silently sets user to null if the request fails (no valid session).
   *
   * Deduplication: if called concurrently, only one HTTP request is made.
   * All callers await the same promise and receive the same result.
   */
  async function fetchUser() {
    if (fetchPromise) return fetchPromise  // Return in-flight request instead of making a new one

    fetchPromise = (async () => {
      isLoading.value = true
      error.value = null
      try {
        const { data } = await api.get('/auth/me/')
        user.value = data.user
        return data.user
      } catch (err) {
        // Any error (401, network issue) means no valid session
        user.value = null
        return null
      } finally {
        isLoading.value = false
        fetchPromise = null  // Reset so future calls can make a new request
      }
    })()

    return fetchPromise
  }

  /**
   * Login with email + password.
   * Backend sets HTTP-only JWT cookies on success; we only store the user profile object.
   *
   * Returns { success: true } on success or { success: false, message } on failure.
   * The ACCOUNT_INACTIVE code (403) gets a distinct user-visible message.
   */
  async function login(credentials) {
    isLoading.value = true
    error.value = null
    try {
      const { data } = await api.post('/auth/login/', credentials)
      user.value = data.user  // Store user profile (never the token itself)
      return { success: true }
    } catch (err) {
      const responseData = err.response?.data
      // Handle disabled account separately: show admin contact message, not generic error
      if (responseData?.code === 'ACCOUNT_INACTIVE') {
        error.value = responseData.message
        return { success: false, message: responseData.message }
      }
      // Flatten nested error structures from DRF's custom exception handler
      const message =
        responseData?.errors?.message ||
        responseData?.message ||
        'Email ou mot de passe invalide.'
      error.value = message
      return { success: false, message }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Register a new account.
   * Backend sets HTTP-only JWT cookies on success.
   */
  async function register(formData) {
    isLoading.value = true
    error.value = null
    try {
      const { data } = await api.post('/auth/register/', formData)
      user.value = data.user
      return { success: true }
    } catch (err) {
      const errors = err.response?.data?.errors || {}
      const message = Object.entries(errors)
        .filter(([k]) => k !== 'code' && k !== 'status')
        .map(([field, msgs]) =>
          Array.isArray(msgs) ? `${field}: ${msgs.join(' ')}` : `${field}: ${msgs}`
        )
        .join('\n') || 'Registration failed.'
      error.value = message
      return { success: false, message }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Logout — blacklists refresh token on backend, clears both cookies,
   * then resets local user state.
   *
   * Even if the server request fails (e.g., network error), user state is
   * cleared locally. This ensures the UI reflects a logged-out state.
   * The backend cookie deletion won't happen in that case, but the user's
   * next request will fail authentication and trigger the forceLogout path.
   */
  async function logout() {
    isLoading.value = true
    error.value = null
    try {
      await api.post('/auth/logout/')  // Blacklists refresh token on backend
    } catch {
      // Even if the server request fails, clear local state
      // so the UI correctly reflects the logged-out state
    } finally {
      user.value = null  // Clear auth state regardless of server response
      isLoading.value = false
    }
  }

  /**
   * Update current user profile.
   */
  async function updateProfile(data) {
    isLoading.value = true
    error.value = null
    try {
      const { data: responseData } = await api.patch('/auth/me/', data)
      user.value = responseData.user
      return { success: true }
    } catch (err) {
      const message = err.response?.data?.message || 'Failed to update profile.'
      error.value = message
      return { success: false, message }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Change current user password.
   */
  async function changePassword(pwData) {
    isLoading.value = true
    error.value = null
    try {
      await api.post('/auth/change-password/', {
        old_password: pwData.currentPw,
        new_password: pwData.newPw,
        confirm_password: pwData.confirmPw
      })
      return { success: true }
    } catch (err) {
      const message = err.response?.data?.error || err.response?.data?.message || 'Failed to change password.'
      error.value = message
      return { success: false, message }
    } finally {
      isLoading.value = false
    }
  }

  return {
    user,
    isAuthenticated,
    isLoading,
    error,
    fetchUser,
    login,
    register,
    logout,
    updateProfile,
    changePassword,
  }
}
