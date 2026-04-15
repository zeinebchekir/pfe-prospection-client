// src/services/monitoringApi.js

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export const monitoringApi = {

  async getState(dagId) {
    const r = await fetch(`${BASE}/api/monitoring/state/${dagId}`)
    return r.json()
  },

  async getHistory(dagId, limit = 8) {
    const r = await fetch(`${BASE}/api/monitoring/history/${dagId}?limit=${limit}`)
    return r.json()
  },

  async getLogs(dagId, runId, taskId) {
    const r = await fetch(`${BASE}/api/monitoring/logs/${dagId}/${runId}/${taskId}`)
    const data = await r.json()
    return data.lines ?? []
  },

  async getMetrics() {
    const r = await fetch(`${BASE}/api/monitoring/metrics`)
    return r.json()
  },

  async triggerDag(dagId, conf = {}) {
    const r = await fetch(`${BASE}/api/monitoring/trigger/${dagId}`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(conf),
    })
    return r.json()
  },

  streamLogs(dagId, runId, taskId, onLine, onDone) {
    const controller = new AbortController()
    const url = `${BASE}/api/monitoring/logs/${dagId}/${runId}/${taskId}/stream`

    fetch(url, { signal: controller.signal })
      .then(async (response) => {
        const reader  = response.body.getReader()
        const decoder = new TextDecoder()
        let   buffer  = ''

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