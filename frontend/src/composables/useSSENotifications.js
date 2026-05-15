import { ref, onMounted, onUnmounted } from 'vue'

// const API = import.meta.env.VITE_ETL_API_URL || 'http://localhost:8001'

export function useSSENotifications() {
  const alerts    = ref([])
  const unread    = ref(0)
  const connected = ref(false)

  let eventSource = null

  // ── 1. Historique depuis la BDD ─────────────────────────────────
  async function fetchHistory() {
    try {
      const res = await fetch(`/notifications/`, {
        credentials: 'include'
      })
      if (!res.ok) return

      const data = await res.json()

      alerts.value = data.map(n => ({
        id:        n.id,
        dag_id:    n.dag_id,
        task_id:   n.task_id,
        message:   n.message,
        log_file:  n.log_file || '',
        timestamp: n.timestamp,
        read:      n.read,          // ← vient de is_read en BDD
      }))

      // Compter uniquement les non lues
      unread.value = alerts.value.filter(a => !a.read).length

    } catch (e) {
      console.error('Erreur chargement historique:', e)
    }
  }

  // ── 2. SSE temps réel ────────────────────────────────────────────
  function connect() {
    eventSource = new EventSource(`/notifications/stream`, {
      withCredentials: true
    })

    eventSource.onopen = () => {
      connected.value = true
    }

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'ping' || data.type === 'connected') return

      // Éviter doublon si déjà chargée depuis la BDD
      const exists = alerts.value.some(a => a.id === data.id)
      if (exists) return

      // Nouvelle alerte toujours non lue
      alerts.value.unshift({
        id:        data.id,
        dag_id:    data.dag_id,
        task_id:   data.task_id,
        message:   data.message,
        log_file:  data.log_file || '',
        timestamp: data.timestamp,
        read:      false,
      })

      unread.value++
    }

    eventSource.onerror = () => {
      connected.value = false
      eventSource.close()
      setTimeout(connect, 5000)
    }
  }

  // ── 3. Marquer une notification lue ─────────────────────────────
  async function markAsRead(id) {
    const alert = alerts.value.find(a => a.id === id)
    if (!alert || alert.read) return

    try {
      await fetch(`/notifications/${id}/read`, {
        method: 'PATCH',
        credentials: 'include'
      })
      alert.read   = true
      unread.value = Math.max(0, unread.value - 1)
    } catch (e) {
      console.error('Erreur markAsRead:', e)
    }
  }

  // ── 4. Tout marquer lu ───────────────────────────────────────────
  async function markAllAsRead() {
    try {
      await fetch(`/notifications/read-all`, {
        method: 'PATCH',
        credentials: 'include'
      })
      alerts.value.forEach(a => { a.read = true })
      unread.value = 0
    } catch (e) {
      console.error('Erreur markAllAsRead:', e)
    }
  }

  // ── 5. Effacer localement (pas de suppression BDD) ───────────────
  function clearAll() {
    alerts.value = []
    unread.value = 0
  }

  // ── Cycle de vie ─────────────────────────────────────────────────
  onMounted(async () => {
    await fetchHistory()   // BDD d'abord
    connect()              // puis SSE
  })

  onUnmounted(() => {
    if (eventSource) eventSource.close()
  })

  return { alerts, unread, connected, markAsRead, markAllAsRead, clearAll }
}