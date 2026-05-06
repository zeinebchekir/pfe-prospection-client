/**
 * monitoringApi.js
 *
 * Service wrapper for the ETL monitoring REST API.
 *
 * ALL routes live in the FastAPI ETL service on port 8001,
 * under the prefix /api/monitoring  (see monitoring.py line 16).
 *
 * monitoringAxios.defaults.baseURL = http://10.0.2.2:8001/api/monitoring
 * Paths passed to monitoringAxios DO NOT include /api/monitoring.
 *
 * Example:
 *   monitoringAxios.get('/state/sync_boamp')
 *   → GET http://10.0.2.2:8001/api/monitoring/state/sync_boamp  ✓
 */
import monitoringAxios from '@/api/monitoringAxios'

const MONITORING_BASE = monitoringAxios.defaults.baseURL

// ── Safe stream URL builder ───────────────────────────────────────────────────
// For log streaming we need the full URL (raw fetch, not Axios).
function streamUrl(path) {
  return MONITORING_BASE + path
}

export const monitoringApi = {

  async getState(dagId) {
    const { data } = await monitoringAxios.get(`/state/${dagId}`)
    return data
  },

  async getHistory(dagId, limit = 8) {
    const { data } = await monitoringAxios.get(`/history/${dagId}`, { params: { limit } })
    return data
  },

  async getLogs(dagId, runId, taskId) {
    const { data } = await monitoringAxios.get(`/logs/${dagId}/${runId}/${taskId}`)
    return data.lines ?? []
  },

  async getMetrics() {
    const { data } = await monitoringAxios.get('/metrics')
    return data
  },

  async triggerDag(dagId, conf = {}) {
    const { data } = await monitoringAxios.post(`/trigger/${dagId}`, conf)
    return data
  },

  // Log stream — must use raw fetch because Axios doesn't support ReadableStream
  streamLogs(dagId, runId, taskId, onLine, onDone) {
    const controller = new AbortController()
    const url = streamUrl(`/logs/${dagId}/${runId}/${taskId}/stream`)

    fetch(url, { signal: controller.signal, credentials: 'omit' })
      .then(async (response) => {
        if (!response.ok) {
          const body = await response.text().catch(() => '')
          console.error(`[STREAM] HTTP ${response.status} — ${url}\n  Body: ${body.slice(0, 200)}`)
          onDone()
          return
        }
        const reader  = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() ?? ''

          for (const line of lines) {
            if (!line.trim()) continue
            try {
              onLine(JSON.parse(line))
            } catch {
              onLine({ text: line, lvl: 'info' })
            }
          }
        }
        onDone()
      })
      .catch((err) => {
        if (err.name !== 'AbortError') console.error('[STREAM]', err)
      })

    return controller
  }
}