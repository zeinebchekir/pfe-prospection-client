/**
 * usePipeline.js
 *
 * Composables for the ETL monitoring dashboard.
 *
 * ALL monitoring routes live in the FastAPI ETL service (port 8001),
 * NOT in Django (port 8000).
 *
 * ETL FastAPI monitoring router: prefix="/api/monitoring"  (monitoring.py line 16)
 * → monitoringAxios baseURL = http://10.0.2.2:8001/api/monitoring
 *
 * Path rules:
 *   monitoringAxios.get('/state/sync_boamp')
 *   → GET http://10.0.2.2:8001/api/monitoring/state/sync_boamp  ✓
 *
 *   DO NOT add /api/monitoring in the path — baseURL already includes it.
 */
import { ref, computed, onMounted, onUnmounted } from 'vue'
import monitoringAxios from '@/api/monitoringAxios'

// ETL base (no /api/monitoring) for raw fetch() stream calls
// monitoringAxios.defaults.baseURL is already http://10.0.2.2:8001/api/monitoring
const MONITORING_BASE = monitoringAxios.defaults.baseURL
console.log('[usePipeline] Monitoring base URL:', MONITORING_BASE)

// ─── Safe fetch helper ────────────────────────────────────────────────────────
// Returns parsed JSON or throws with a clear message if the response is HTML/404.
async function safeGet(path) {
  const url = MONITORING_BASE + path
  let response
  try {
    response = await fetch(url, { credentials: 'omit' })
  } catch (networkErr) {
    throw new Error(`[monitoring] Network error — ${url}: ${networkErr.message}`)
  }

  if (!response.ok) {
    const contentType = response.headers.get('content-type') ?? ''
    let bodyPreview = ''
    try { bodyPreview = (await response.text()).slice(0, 300) } catch { }
    throw new Error(
      `[monitoring] HTTP ${response.status} — ${url}\n` +
      `  Content-Type: ${contentType}\n` +
      `  Body: ${bodyPreview}`
    )
  }

  const contentType = response.headers.get('content-type') ?? ''
  if (!contentType.includes('application/json')) {
    let bodyPreview = ''
    try { bodyPreview = (await response.text()).slice(0, 300) } catch { }
    throw new Error(
      `[monitoring] Non-JSON response — ${url}\n` +
      `  Content-Type: ${contentType}\n` +
      `  Body: ${bodyPreview}`
    )
  }

  return response.json()
}

// ─── Shared utils ─────────────────────────────────────────────────────────────

export const TASK_LABELS = {
  scrape_boamp:     'Scraping incrémental des marchés publics BOAMP via API',
  extract_boamp:    'Extraction et parsing JSON des champs normalisés',
  enrich_boamp:     'Enrichissement SIRET via API INSEE / Annuaire entreprises',
  load_raw_boamp:   'Chargement dans le schéma raw.boamp (PostgreSQL)',
  clean_boamp:      'Déduplication, normalisation et validation des données',
  load_clean_boamp: 'Chargement final dans le schéma clean.boamp',
  scrape_sirene:    'Téléchargement du fichier SIRENE (data.gouv.fr) en incrémental',
  extract_datagouv: 'Parsing CSV et mapping vers le modèle de données interne',
  load_raw_datagouv:'Insertion dans le schéma raw.sirene (upsert par SIRET)',
  clean_datagouv:   'Nettoyage, normalisation des codes NAF et validation LUHN SIREN',
  load_clean_sirene:'Chargement final dans clean.sirene — inserts + updates',
  rapport_final:    'Génération du rapport de synthèse et notifications',
  cleanup:          'Nettoyage des fichiers temporaires',
}

export function mapState(s) {
  const MAP = {
    success:         'ok',
    failed:          'err',
    upstream_failed: 'err',
    running:         'run',
    queued:          'idle',
    scheduled:       'idle',
    skipped:         'idle',
    none:            'idle',
  }
  return MAP[s] ?? 'idle'
}

export function formatDuration(sec) {
  if (!sec || sec <= 0) return '—'
  const m = Math.floor(sec / 60)
  const s = Math.round(sec % 60)
  return `${m}m ${s}s`
}

export function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleTimeString('fr-FR', {
    hour:   '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

// ─── usePipeline — real-time pipeline state + logs + stream ──────────────────

export function usePipeline(dagId, externalTaskResources) {

  const state           = ref({ run: null, tasks: [], progress: 0, metrics: {} })
  const history         = ref([])
  const logs            = ref({})
  const systemResources = ref({ cpu: 0, ram: 0, disk: 0, source: 'psutil' })
  const loading         = ref(true)
  const error           = ref(null)
  const connected       = ref(false)

  let pollTimer      = null
  let resourceTimer  = null
  let streamCtrl     = null
  let watchedTask    = null

  // ── Computed ───────────────────────────────────────────────────────────────

  const runStatus = computed(() => mapState(state.value.run?.state ?? 'idle'))

  const isRunning = computed(() =>
    state.value.tasks.some(t => t.state === 'running')
  )

  const activeTask = computed(() =>
    state.value.tasks.find(t => t.state === 'running') ?? null
  )

  const phases = computed(() =>
    state.value.tasks.map((t, i) => {
      const res = externalTaskResources.value?.[dagId]?.[t.task_id]
        ?? { cpu: 0, ram: 0, disk: 0 }
      return {
        num:        i + 1,
        name:       t.task_id,
        sub:        TASK_LABELS[t.task_id] ?? t.task_id,
        st:         mapState(t.state),
        dur:        formatDuration(t.duration),
        start:      formatDate(t.start_date),
        end:        formatDate(t.end_date),
        try_number: t.try_number ?? 1,
        inp:        t.inp ?? '—',
        out:        t.out ?? '—',
        err:        t.err ?? null,
        logs:       logs.value[t.task_id] ?? [],
        cpu:        res.cpu,
        ram:        res.ram,
        disk:       res.disk,
      }
    })
  )

  // ── Polling état — toutes les 2s ───────────────────────────────────────────
  // Path: /state/{dag_id}
  // Full URL: http://10.0.2.2:8001/api/monitoring/state/{dag_id}

  async function fetchState() {
    try {
      const data = await safeGet(`/state/${dagId}`)
      state.value   = data
      connected.value = true
      error.value   = null

      const running = data.tasks?.find(t => t.state === 'running')

      if (running && running.task_id !== watchedTask) {
        startLogStream(running.task_id)
      }

      if (!running && watchedTask) {
        const finished = watchedTask
        stopLogStream()
        if (data.run?.run_id) {
          await fetchLogsSnapshot(finished)
        }
        watchedTask = null
      }

    } catch (e) {
      error.value     = e.message
      connected.value = false
      console.error(`[POLL ${dagId}]`, e.message)
    } finally {
      loading.value = false
    }
  }

  // ── Ressources système ─────────────────────────────────────────────────────
  // Path: /resources/system
  // Full URL: http://10.0.2.2:8001/api/monitoring/resources/system

  async function fetchSystemResources() {
    try {
      const data = await safeGet('/resources/system')
      systemResources.value = data
    } catch (e) {
      // Silently fail — not critical
      console.warn('[monitoring] System resources unavailable:', e.message.split('\n')[0])
    }
  }

  // ── Logs ───────────────────────────────────────────────────────────────────
  // Path: /logs/{dag_id}/{run_id}/{task_id}
  // Full URL: http://10.0.2.2:8001/api/monitoring/logs/...

  async function fetchLogsSnapshot(taskId) {
    if (!state.value.run?.run_id) return
    try {
      const data = await safeGet(
        `/logs/${dagId}/${state.value.run.run_id}/${taskId}`
      )
      logs.value = { ...logs.value, [taskId]: data.lines ?? [] }
    } catch (e) {
      console.warn('[monitoring] Log snapshot failed:', e.message.split('\n')[0])
    }
  }

  async function loadLogs(taskId) {
    if (logs.value[taskId]?.length) return
    await fetchLogsSnapshot(taskId)
  }

  // ── Log stream (tail -f) ───────────────────────────────────────────────────
  // Path: /logs/{dag_id}/{run_id}/{task_id}/stream
  // Full URL: http://10.0.2.2:8001/api/monitoring/logs/...

  function startLogStream(taskId) {
    if (!state.value.run?.run_id) return
    stopLogStream()

    watchedTask = taskId
    logs.value  = { ...logs.value, [taskId]: [] }

    const controller = new AbortController()
    streamCtrl = controller

    const url = `${MONITORING_BASE}/logs/${dagId}/${state.value.run.run_id}/${taskId}/stream`

    fetch(url, { signal: controller.signal, credentials: 'omit' })
      .then(async (response) => {
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
              const parsed = JSON.parse(line)
              logs.value = {
                ...logs.value,
                [taskId]: [...(logs.value[taskId] ?? []), parsed]
              }
            } catch { }
          }
        }
        watchedTask = null
      })
      .catch(err => {
        if (err.name !== 'AbortError')
          console.error(`[STREAM ${dagId}:${taskId}]`, err.message)
      })
  }

  function stopLogStream() {
    streamCtrl?.abort()
    streamCtrl = null
  }

  // ── Trigger DAG ────────────────────────────────────────────────────────────
  // Path: /trigger/{dag_id}
  // Full URL: http://10.0.2.2:8001/api/monitoring/trigger/{dag_id}

  async function triggerDag(conf = {}) {
    try {
      await monitoringAxios.post(`/trigger/${dagId}`, conf)
      setTimeout(fetchState, 1500)
      setTimeout(fetchState, 4000)
    } catch (e) {
      console.error(`[TRIGGER ${dagId}]`, e.message)
    }
  }

  // ── History ────────────────────────────────────────────────────────────────
  // Path: /history/{dag_id}
  // Full URL: http://10.0.2.2:8001/api/monitoring/history/{dag_id}

  async function fetchHistory() {
    try {
      history.value = await safeGet(`/history/${dagId}`)
    } catch (e) {
      console.warn('[monitoring] History unavailable:', e.message.split('\n')[0])
    }
  }

  // ── Lifecycle ──────────────────────────────────────────────────────────────

  onMounted(async () => {
    await fetchState()
    fetchHistory()
    pollTimer      = setInterval(fetchState,          2000)
    resourceTimer  = setInterval(fetchSystemResources, 3000)
    fetchSystemResources()
  })

  onUnmounted(() => {
    if (pollTimer)     clearInterval(pollTimer)
    if (resourceTimer) clearInterval(resourceTimer)
    stopLogStream()
  })

  return {
    state, history, phases, logs,
    systemResources,
    runStatus, isRunning, activeTask,
    loading, error, connected,
    loadLogs, triggerDag, fetchHistory,
    fetchState,
  }
}


// ─── useMonitoringETL — analytics charts ─────────────────────────────────────
//
// Endpoints (all on ETL FastAPI :8001, prefix /api/monitoring):
//   GET /kpi-summary          → http://10.0.2.2:8001/api/monitoring/kpi-summary
//   GET /dag-success-rate     → http://10.0.2.2:8001/api/monitoring/dag-success-rate
//   GET /task-duration        → http://10.0.2.2:8001/api/monitoring/task-duration
//   GET /volume-over-time     → http://10.0.2.2:8001/api/monitoring/volume-over-time
//   GET /data-quality         → http://10.0.2.2:8001/api/monitoring/data-quality
//   GET /data-quality-boamp   → http://10.0.2.2:8001/api/monitoring/data-quality-boamp

export function useMonitoringETL() {
  const kpi              = ref(null)
  const dagSuccess       = ref([])
  const taskDuration     = ref([])
  const volumeOverTime   = ref([])
  const dataQuality      = ref([])
  const dataQualityBoamp = ref([])
  const loading          = ref(true)
  const error            = ref(null)

  let intervalId = null

  async function fetchAll() {
    try {
      // monitoringAxios.baseURL = http://10.0.2.2:8001/api/monitoring
      // Paths below do NOT include /api/monitoring — that's in the baseURL
      const [r1, r2, r3, r4, r5, r6] = await Promise.all([
        monitoringAxios.get('/kpi-summary'),
        monitoringAxios.get('/dag-success-rate', { params: { days: 30 } }),
        monitoringAxios.get('/task-duration', { params: { dag_id: 'sync_boamp', days: 7 } }),
        monitoringAxios.get('/volume-over-time', { params: { days: 7 } }),
        monitoringAxios.get('/data-quality'),
        monitoringAxios.get('/data-quality-boamp'),
      ])

      kpi.value              = r1.data
      dagSuccess.value       = r2.data
      taskDuration.value     = r3.data
      volumeOverTime.value   = r4.data
      dataQuality.value      = r5.data
      dataQualityBoamp.value = r6.data
      error.value            = null
    } catch (e) {
      error.value = e.message
      console.error('[METRICS] fetchAll failed:', e.message.split('\n')[0])
    } finally {
      loading.value = false
    }
  }

  onMounted(() => {
    fetchAll()
    intervalId = setInterval(fetchAll, 60_000)
  })

  onUnmounted(() => {
    clearInterval(intervalId)
  })

  return {
    kpi, dagSuccess, taskDuration, volumeOverTime,
    dataQuality, dataQualityBoamp,
    loading, error, fetchAll,
  }
}