/**
 * etlAxios.js
 *
 * Shared Axios instance for the FastAPI ETL / Entreprises service (port 8001).
 *
 * Key points:
 * - Uses getEtlBaseUrl() for env-aware base URL resolution
 * - withCredentials: false — the ETL service does NOT use cookie-based auth;
 *   only the Django API (port 8000) uses cookies.
 * - No token refresh interceptor needed here.
 * - CORS on the ETL service must explicitly allow Origin: http://10.0.2.2
 *   (handled in ETL_service/ETL_pipeline/apis/main.py)
 */
import axios from 'axios'
import { getEtlBaseUrl } from '@/lib/apiBase'

const ETL_BASE = getEtlBaseUrl()

console.log('[etlAxios] ETL service base URL:', ETL_BASE)

const etlApi = axios.create({
  baseURL: ETL_BASE,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
  // ETL service is unauthenticated (no cookies) — keep withCredentials false
  // to avoid preflight complexity on this service.
  withCredentials: false,
})

export default etlApi
