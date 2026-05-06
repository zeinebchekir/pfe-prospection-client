import { ref, computed } from 'vue'
import api from '@/api/axios'

const user = ref(null)
const isLoading = ref(false)
const error = ref(null)
let fetchPromise = null

function logAxiosError(label, err) {
  console.error(label, JSON.stringify({
    message: err.message,
    status: err.response?.status,
    data: err.response?.data,
    url: err.config?.url,
    baseURL: err.config?.baseURL,
    fullURL: `${err.config?.baseURL || ''}${err.config?.url || ''}`,
  }, null, 2))
}

if (typeof window !== 'undefined') {
  window.addEventListener('auth:session-expired', () => {
    user.value = null
    isLoading.value = false
    fetchPromise = null
  })
}

export function useAuth() {
  const isAuthenticated = computed(() => user.value !== null)

  async function fetchUser() {
    if (fetchPromise) return fetchPromise

    fetchPromise = (async () => {
      isLoading.value = true
      error.value = null

      try {
        const { data } = await api.get('/auth/me/', { authProbe: true })
        user.value = data.user
        return data.user
      } catch (err) {
        logAxiosError('🚨 FETCH USER FAILED FULL:', err)
        user.value = null
        return null
      } finally {
        isLoading.value = false
        fetchPromise = null
      }
    })()

    return fetchPromise
  }

  async function login(credentials) {
    isLoading.value = true
    error.value = null

    try {
      const { data } = await api.post('/auth/login/', credentials)
      console.log('✅ LOGIN RESPONSE:', JSON.stringify(data, null, 2))

      user.value = data.user

      return { success: true }
    } catch (err) {
      logAxiosError('🚨 LOGIN FAILED FULL:', err)

      const responseData = err.response?.data

      if (responseData?.code === 'ACCOUNT_INACTIVE') {
        error.value = responseData.message
        return { success: false, message: responseData.message }
      }

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

  async function register(formData) {
    isLoading.value = true
    error.value = null

    try {
      const { data } = await api.post('/auth/register/', formData)

      console.log('✅ REGISTER RESPONSE:', JSON.stringify(data, null, 2))

      user.value = data.user
      return {
        success: true,
        needsLogin: false,
        user: data.user,
        message: 'Compte créé avec succès. Connectez-vous maintenant.',
      }
    } catch (err) {
      logAxiosError('🚨 REGISTER FAILED FULL:', err)

      const responseData = err.response?.data
      const errors = responseData?.errors || {}

      const message =
        responseData?.message ||
        Object.entries(errors)
          .filter(([k]) => k !== 'code' && k !== 'status')
          .map(([field, msgs]) =>
            Array.isArray(msgs)
              ? `${field}: ${msgs.join(' ')}`
              : `${field}: ${msgs}`
          )
          .join('\n') ||
        'Registration failed.'

      error.value = message
      return { success: false, message }
    } finally {
      isLoading.value = false
    }
  }

  async function logout() {
    isLoading.value = true
    error.value = null

    try {
      await api.post('/auth/logout/')
    } catch (err) {
      logAxiosError('🚨 LOGOUT FAILED FULL:', err)
    } finally {
      user.value = null
      isLoading.value = false
    }
  }

  async function updateProfile(data) {
    isLoading.value = true
    error.value = null

    try {
      const { data: responseData } = await api.patch('/auth/me/', data)
      user.value = responseData.user
      return { success: true }
    } catch (err) {
      logAxiosError('🚨 UPDATE PROFILE FAILED FULL:', err)

      const message = err.response?.data?.message || 'Failed to update profile.'
      error.value = message
      return { success: false, message }
    } finally {
      isLoading.value = false
    }
  }

  async function changePassword(pwData) {
    isLoading.value = true
    error.value = null

    try {
      await api.post('/auth/change-password/', {
        old_password: pwData.currentPw,
        new_password: pwData.newPw,
        confirm_password: pwData.confirmPw,
      })

      return { success: true }
    } catch (err) {
      logAxiosError('🚨 CHANGE PASSWORD FAILED FULL:', err)

      const message =
        err.response?.data?.error ||
        err.response?.data?.message ||
        'Failed to change password.'

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
