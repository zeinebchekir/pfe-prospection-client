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

// Module-level reactive state — shared across all component usages
const user = ref(null)
const isLoading = ref(false)
const error = ref(null)
let fetchPromise = null

export function useAuth() {
  const isAuthenticated = computed(() => user.value !== null)

  /**
   * Fetch the current user from /api/auth/me/.
   * Called on app load to restore session from existing cookies.
   * Silently fails if no valid session exists (sets user to null).
   */
  async function fetchUser() {
    if (fetchPromise) return fetchPromise

    fetchPromise = (async () => {
      isLoading.value = true
      error.value = null
      try {
        const { data } = await api.get('/auth/me/')
        user.value = data.user
        return data.user
      } catch (err) {
        user.value = null
        return null
      } finally {
        isLoading.value = false
        fetchPromise = null
      }
    })()

    return fetchPromise
  }

  /**
   * Login with email + password.
   * Backend sets HTTP-only JWT cookies on success.
   */
  async function login(credentials) {
    isLoading.value = true
    error.value = null
    try {
      const { data } = await api.post('/auth/login/', credentials)
      user.value = data.user
      return { success: true }
    } catch (err) {
      const message =
        err.response?.data?.errors?.message ||
        err.response?.data?.message ||
        'Login failed. Please check your credentials.'
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
   * Logout — blacklists refresh token on backend, clears cookies,
   * and resets local user state.
   */
  async function logout() {
    isLoading.value = true
    error.value = null
    try {
      await api.post('/auth/logout/')
    } catch {
      // Even if the server request fails, clear local state
    } finally {
      user.value = null
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
