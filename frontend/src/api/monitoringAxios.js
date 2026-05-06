/**
 * monitoringAxios.js
 *
 * Shared Axios instance for the ETL Monitoring API.
 *
 * All monitoring routes (/api/monitoring/...) are served by the
 * FastAPI ETL service on port 8001 — NOT the Django backend.
 *
 * Router prefix in monitoring.py: prefix="/api/monitoring"
 * So endpoint paths do NOT include /api/monitoring in the path here;
 * the baseURL already ends with /api/monitoring.
 *
 * Usage:
 *   monitoringApi.get('/state/sync_boamp')
 *   → GET http://10.0.2.2:8001/api/monitoring/state/sync_boamp
 */
import axios from 'axios'
import { getEtlBaseUrl } from '@/lib/apiBase'

const ETL_BASE = getEtlBaseUrl()  // e.g. 'http://10.0.2.2:8001' or 'http://localhost:8001'
const MONITORING_BASE = `${ETL_BASE}/api/monitoring`

console.log('[monitoringAxios] Monitoring base URL:', MONITORING_BASE)

const monitoringAxios = axios.create({
  baseURL: MONITORING_BASE,
  headers: {
    Accept: 'application/json',
    'Content-Type': 'application/json',
  },
  // Monitoring service is unauthenticated — no cookies needed
  withCredentials: false,
  timeout: 8000,
})

// Safe response interceptor — log non-JSON responses instead of crashing
monitoringAxios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const config = error.config
    const status = error.response?.status
    const contentType = error.response?.headers?.['content-type'] ?? '(unknown)'
    const url = config?.baseURL && config?.url
      ? config.baseURL + config.url
      : config?.url ?? '(unknown URL)'

    if (error.response) {
      // Try to get first 300 chars of body for debugging HTML 404s etc.
      let bodyPreview = ''
      try {
        const text = typeof error.response.data === 'string'
          ? error.response.data
          : JSON.stringify(error.response.data)
        bodyPreview = text.slice(0, 300)
      } catch { }

      console.error(
        `[monitoringAxios] HTTP ${status} — ${url}\n` +
        `  Content-Type: ${contentType}\n` +
        `  Body preview: ${bodyPreview}`
      )
    } else {
      console.error(`[monitoringAxios] Network error — ${url}: ${error.message}`)
    }

    return Promise.reject(error)
  }
)

export default monitoringAxios
