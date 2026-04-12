import { ref, computed, onMounted, onUnmounted } from 'vue'

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export const TASK_LABELS = {
  scrape_boamp:       'Scraping incrémental des marchés publics BOAMP via API',
  extract_boamp:      'Extraction et parsing JSON des champs normalisés',
  enrich_boamp:       'Enrichissement SIRET via API INSEE / Annuaire entreprises',
  load_raw_boamp:     'Chargement dans le schéma raw.boamp (PostgreSQL)',
  clean_boamp:        'Déduplication, normalisation et validation des données',
  load_clean_boamp:   'Chargement final dans le schéma clean.boamp',
  scrape_sirene:      'Téléchargement du fichier SIRENE (data.gouv.fr) en incrémental',
  extract_datagouv:   'Parsing CSV et mapping vers le modèle de données interne',
  load_raw_datagouv:  'Insertion dans le schéma raw.sirene (upsert par SIRET)',
  clean_datagouv:     'Nettoyage, normalisation des codes NAF et validation LUHN SIREN',
  load_clean_sirene:  'Chargement final dans clean.sirene — inserts + updates',
  rapport_final:      'Génération du rapport de synthèse et notifications',
  cleanup:            'Nettoyage des fichiers temporaires',
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

async function apiFetch(url) {
  const r = await fetch(BASE_URL + url)
  if (!r.ok) throw new Error(`HTTP ${r.status} — ${url}`)
  return r.json()
}

// ─────────────────────────────────────────────
// usePipeline — gère UNIQUEMENT logs + stream
// Les ressources sont gérées par le composant parent
// ─────────────────────────────────────────────

export function usePipeline(dagId, externalTaskResources) {

  const state           = ref({ run: null, tasks: [], progress: 0, metrics: {} })
  const history         = ref([])
  const logs            = ref({})
  const systemResources = ref({ cpu: 0, ram: 0, disk: 0, source: 'psutil' })
  const loading         = ref(true)
  const error           = ref(null)
  const connected       = ref(false)

  let pollTimer     = null
  let resourceTimer = null
  let streamCtrl    = null
  let watchedTask   = null

  // ── Computed ─────────────────────────────────────────────

  const runStatus = computed(() => mapState(state.value.run?.state ?? 'idle'))

  const isRunning = computed(() =>
    state.value.tasks.some(t => t.state === 'running')
  )

  const activeTask = computed(() =>
    state.value.tasks.find(t => t.state === 'running') ?? null
  )

  // phases lit les ressources depuis externalTaskResources[dagId][taskId]
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
        inp:        t.inp  ?? '—',
        out:        t.out  ?? '—',
        err:        t.err  ?? null,
        logs:       logs.value[t.task_id] ?? [],
        cpu:        res.cpu,
        ram:        res.ram,
        disk:       res.disk,
      }
    })
  )

  // ── Polling état — toutes les 2s ──────────────────────────

  async function fetchState() {
    try {
      const data      = await apiFetch(`/api/monitoring/state/${dagId}`)
      state.value     = data
      connected.value = true
      error.value     = null

      const running = data.tasks?.find(t => t.state === 'running')

      // Task vient de passer running → stream logs
      if (running && running.task_id !== watchedTask) {
        startLogStream(running.task_id)
      }

      // Plus rien ne tourne → arrêter stream + snapshot final
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
    } finally {
      loading.value = false
    }
  }

  // ── Ressources système ────────────────────────────────────

  async function fetchSystemResources() {
    try {
      systemResources.value = await apiFetch('/api/monitoring/resources/system')
    } catch {}
  }

  // ── Logs ─────────────────────────────────────────────────

  async function fetchLogsSnapshot(taskId) {
    if (!state.value.run?.run_id) return
    try {
      const data = await apiFetch(
        `/api/monitoring/logs/${dagId}/${state.value.run.run_id}/${taskId}`
      )
      logs.value = { ...logs.value, [taskId]: data.lines ?? [] }
    } catch {}
  }

  async function loadLogs(taskId) {
    if (logs.value[taskId]?.length) return
    await fetchLogsSnapshot(taskId)
  }

  function startLogStream(taskId) {
    if (!state.value.run?.run_id) return
    stopLogStream()

    watchedTask = taskId
    logs.value  = { ...logs.value, [taskId]: [] }

    const controller = new AbortController()
    streamCtrl = controller

    const url = `${BASE_URL}/api/monitoring/logs/${dagId}/${state.value.run.run_id}/${taskId}/stream`

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
              const parsed = JSON.parse(line)
              logs.value = {
                ...logs.value,
                [taskId]: [...(logs.value[taskId] ?? []), parsed]
              }
            } catch {}
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

  // ── Trigger ───────────────────────────────────────────────

  async function triggerDag(conf = {}) {
    try {
      await fetch(`${BASE_URL}/api/monitoring/trigger/${dagId}`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(conf),
      })
      setTimeout(fetchState, 1500)
      setTimeout(fetchState, 4000)
    } catch (e) {
      console.error(`[TRIGGER ${dagId}]`, e.message)
    }
  }

  // ── Lifecycle ─────────────────────────────────────────────

  onMounted(async () => {
    await fetchState()
    fetchHistory()
    pollTimer     = setInterval(fetchState,           2000)
    resourceTimer = setInterval(fetchSystemResources, 3000)
    fetchSystemResources()
  })

  onUnmounted(() => {
    if (pollTimer)     clearInterval(pollTimer)
    if (resourceTimer) clearInterval(resourceTimer)
    stopLogStream()
  })

  async function fetchHistory() {
    try { history.value = await apiFetch(`/api/monitoring/history/${dagId}`) }
    catch {}
  }

  return {
    state, history, phases, logs,
    systemResources,
    runStatus, isRunning, activeTask,
    loading, error, connected,
    loadLogs, triggerDag, fetchHistory,
    fetchState,
  }
}