import { Capacitor } from '@capacitor/core'

const DEFAULT_ANDROID_EMULATOR_HOST = '10.0.2.2'
const DEFAULT_DJANGO_PORT = '8000'
const DEFAULT_ETL_PORT = '8001'

function trimTrailingSlash(value) {
  return value.replace(/\/+$/, '')
}

function buildNativeApiOrigin(port = DEFAULT_DJANGO_PORT) {
  if (typeof window === 'undefined') {
    return `http://${DEFAULT_ANDROID_EMULATOR_HOST}:${port}`
  }

  const isHttp = window.location.protocol === 'http:'
  const scheme = isHttp ? 'http' : 'https'
  const host =
    window.location.hostname && window.location.hostname !== 'localhost'
      ? window.location.hostname
      : DEFAULT_ANDROID_EMULATOR_HOST

  return `${scheme}://${host}:${port}`
}

/**
 * Base URL for the Django REST API (port 8000).
 * - Explicit VITE_API_URL env var → use it
 * - Capacitor native (Android emulator) → http://10.0.2.2:8000/api
 * - Browser dev → /api  (proxied by Vite to localhost:8000)
 */
export function getDjangoApiBaseUrl() {
  const explicitBaseUrl = import.meta.env.VITE_API_URL
  if (explicitBaseUrl) {
    return `${trimTrailingSlash(explicitBaseUrl)}/api`
  }

  if (Capacitor.isNativePlatform()) {
    return `${buildNativeApiOrigin(DEFAULT_DJANGO_PORT)}/api`
  }

  return '/api'
}

/**
 * Base URL for the FastAPI ETL service (port 8001).
 * - Explicit VITE_FASTAPI_URL / VITE_ETL_API_URL env var → use it
 * - Capacitor native (Android emulator) → http://10.0.2.2:8001
 * - Browser dev → http://localhost:8001  (direct, no Vite proxy for ETL)
 */
export function getEtlBaseUrl() {
  // Accept either VITE_FASTAPI_URL or VITE_ETL_API_URL (both point at :8001)
  const explicitUrl = import.meta.env.VITE_FASTAPI_URL || import.meta.env.VITE_ETL_API_URL
  if (explicitUrl) {
    return trimTrailingSlash(explicitUrl)
  }

  if (Capacitor.isNativePlatform()) {
    return buildNativeApiOrigin(DEFAULT_ETL_PORT)
  }

  // Browser fallback: direct access (dev server must be running on :8001)
  return `http://localhost:${DEFAULT_ETL_PORT}`
}

