import { ref, computed, watch, onMounted } from 'vue'
import etlApi from '@/api/etlAxios'
import { adaptLeadResponse } from '@/lib/leadAdapter'

export const INITIAL_FILTERS = {
  search: '',
  segments: [],
  statuses: [],
  villes: [],
  hasBoamp: null,
  hasEmail: null,
  hasTelephone: null,
  hasLinkedin: null,
  hasDirigeants: null,
  caMin: null,
  caMax: null,
  scoreMin: null,
  scoreMax: null,
}

export const UNIQUE_SEGMENTS = ['PME', 'ETI', 'GE', 'Micro', 'Inconnu']
export const UNIQUE_STATUSES = ['Nouveau', 'Qualifié', 'Opportunité']

console.log('[useLeads] ETL base URL:', etlApi.defaults.baseURL)

function countActiveFilters(f) {
  let c = 0
  if (f.search) c++
  if (f.segments.length) c++
  if (f.statuses.length) c++
  if (f.villes.length) c++
  if (f.hasBoamp !== null) c++
  if (f.hasEmail !== null) c++
  if (f.hasTelephone !== null) c++
  if (f.hasLinkedin !== null) c++
  if (f.hasDirigeants !== null) c++
  if (f.caMin !== null || f.caMax !== null) c++
  if (f.scoreMin !== null || f.scoreMax !== null) c++
  return c
}

function safeText(value) {
  return String(value || '').toLowerCase()
}

export function useLeads() {
  const allLeads = ref([])
  const isLoading = ref(false)

  async function fetchLeads() {
    isLoading.value = true

    console.log('[useLeads] Fetching:', etlApi.defaults.baseURL + '/entreprises/')

    try {
      const res = await etlApi.get('/entreprises/', {
        params: { skip: 0, limit: 10000 },
      })

      console.log('[useLeads] Fetch response:', JSON.stringify(res.data, null, 2))

      const rawData = Array.isArray(res.data)
        ? res.data
        : (res.data?.data || [])

      allLeads.value = adaptLeadResponse(rawData)

      console.log('[useLeads] Adapted leads count:', allLeads.value.length)
    } catch (err) {
      console.error('[useLeads] Fetch error:', JSON.stringify({
        message: err.message,
        status: err.response?.status,
        data: err.response?.data,
        url: err.config?.url,
        baseURL: err.config?.baseURL,
      }, null, 2))
    } finally {
      isLoading.value = false
    }
  }

  onMounted(fetchLeads)

  const filters = ref({ ...INITIAL_FILTERS, segments: [], statuses: [], villes: [] })
  const sortField = ref('score')
  const sortDir = ref('desc')
  const page = ref(1)
  const pageSize = ref(20)

  watch(filters, () => {
    page.value = 1
  }, { deep: true })

  watch(pageSize, () => {
    page.value = 1
  })

  const filteredLeads = computed(() => {
    let result = [...allLeads.value]
    const f = filters.value

    if (f.search) {
      const q = f.search.toLowerCase()

      result = result.filter((l) =>
        safeText(l.nom).includes(q) ||
        safeText(l.siren).includes(q) ||
        safeText(l.siret).includes(q) ||
        safeText(l.identifiant).includes(q) ||
        safeText(l.ville).includes(q) ||
        safeText(l.codePostal).includes(q) ||
        safeText(l.secteurActivite).includes(q) ||
        safeText(l.formeJuridique).includes(q) ||
        safeText(l.tailleEntreprise).includes(q) ||
        (Array.isArray(l.dirigeants) &&
          l.dirigeants.some((d) => safeText(d.fullName).includes(q)))
      )
    }

    if (f.segments.length) {
      result = result.filter((l) => f.segments.includes(l.segment))
    }

    if (f.statuses.length) {
      result = result.filter((l) => f.statuses.includes(l.status))
    }

    if (f.villes.length) {
      result = result.filter((l) => f.villes.includes(l.ville))
    }

    if (f.hasBoamp === true) result = result.filter((l) => l.hasBoamp)
    if (f.hasBoamp === false) result = result.filter((l) => !l.hasBoamp)

    if (f.hasEmail === true) result = result.filter((l) => l.hasEmail)
    if (f.hasEmail === false) result = result.filter((l) => !l.hasEmail)

    if (f.hasTelephone === true) result = result.filter((l) => l.hasTelephone)
    if (f.hasTelephone === false) result = result.filter((l) => !l.hasTelephone)

    if (f.hasLinkedin === true) result = result.filter((l) => l.hasLinkedinDirigeant)
    if (f.hasLinkedin === false) result = result.filter((l) => !l.hasLinkedinDirigeant)

    if (f.hasDirigeants === true) result = result.filter((l) => l.nbDirigeants > 0)
    if (f.hasDirigeants === false) result = result.filter((l) => l.nbDirigeants === 0)

    if (f.caMin !== null) {
      result = result.filter((l) => l.ca !== null && l.ca >= f.caMin)
    }

    if (f.caMax !== null) {
      result = result.filter((l) => l.ca !== null && l.ca <= f.caMax)
    }

    if (f.scoreMin !== null) {
      result = result.filter((l) => l.score >= f.scoreMin)
    }

    if (f.scoreMax !== null) {
      result = result.filter((l) => l.score <= f.scoreMax)
    }

    return result
  })

  const sortedLeads = computed(() => {
    const sorted = [...filteredLeads.value]

    sorted.sort((a, b) => {
      let valA
      let valB

      switch (sortField.value) {
        case 'nom':
          valA = a.nom
          valB = b.nom
          break
        case 'segment':
          valA = a.segment
          valB = b.segment
          break
        case 'ca':
          valA = a.ca ?? 0
          valB = b.ca ?? 0
          break
        case 'score':
          valA = a.score
          valB = b.score
          break
        case 'completude':
          valA = a.completude
          valB = b.completude
          break
        case 'probaConversion':
          valA = a.probaConversion
          valB = b.probaConversion
          break
        case 'nbLocaux':
          valA = a.nbLocaux ?? 0
          valB = b.nbLocaux ?? 0
          break
        case 'ville':
          valA = a.ville
          valB = b.ville
          break
        case 'nbDirigeants':
          valA = a.nbDirigeants
          valB = b.nbDirigeants
          break
        default:
          valA = a.score
          valB = b.score
      }

      if (typeof valA === 'string') {
        const cmp = valA.localeCompare(String(valB || ''))
        return sortDir.value === 'asc' ? cmp : -cmp
      }

      return sortDir.value === 'asc' ? valA - valB : valB - valA
    })

    return sorted
  })

  const totalPages = computed(() =>
    Math.max(1, Math.ceil(sortedLeads.value.length / pageSize.value))
  )

  const paginatedLeads = computed(() => {
    const start = (page.value - 1) * pageSize.value
    return sortedLeads.value.slice(start, start + pageSize.value)
  })

  const kpis = computed(() => {
    const leads = filteredLeads.value
    const total = leads.length

    if (total === 0) {
      return {
        total: 0,
        avgScore: 0,
        avgProba: 0,
        avgCompletude: 0,
        totalCA: 0,
        qualified: 0,
        opportunities: 0,
      }
    }

    const avgScore = Math.round(leads.reduce((s, l) => s + (l.score || 0), 0) / total)
    const avgProba = Math.round(leads.reduce((s, l) => s + (l.probaConversion || 0), 0) / total)
    const avgCompletude = Math.round(leads.reduce((s, l) => s + (l.completude || 0), 0) / total)
    const totalCA = leads.reduce((s, l) => s + (l.ca ?? 0), 0)
    const qualified = leads.filter((l) => l.status === 'Qualifié').length
    const opportunities = leads.filter((l) => l.status === 'Opportunité').length

    return {
      total,
      avgScore,
      avgProba,
      avgCompletude,
      totalCA,
      qualified,
      opportunities,
    }
  })

  const uniqueVilles = computed(() =>
    [...new Set(allLeads.value.map((l) => l.ville).filter((v) => v && v !== '—'))].sort()
  )

  const activeFilterCount = computed(() => countActiveFilters(filters.value))

  function setFilter(key, value) {
    filters.value = { ...filters.value, [key]: value }
  }

  function toggleArrayFilter(key, value) {
    const arr = filters.value[key]

    if (arr.includes(value)) {
      filters.value = { ...filters.value, [key]: arr.filter((v) => v !== value) }
    } else {
      filters.value = { ...filters.value, [key]: [...arr, value] }
    }
  }

  function resetFilters() {
    filters.value = { ...INITIAL_FILTERS, segments: [], statuses: [], villes: [] }
    page.value = 1
  }

  function toggleSort(field) {
    if (sortField.value === field) {
      sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
    } else {
      sortField.value = field
      sortDir.value = 'desc'
    }
  }

  function updateLeadStatus(id, newStatus) {
    const lead = allLeads.value.find((l) => l.id === id)
    if (lead) lead.status = newStatus
  }

  function updateLead(id, updates) {
    const idx = allLeads.value.findIndex((l) => l.id === id)
    if (idx !== -1) {
      allLeads.value[idx] = { ...allLeads.value[idx], ...updates }
    }
  }

  return {
    allLeads,
    isLoading,
    filteredLeads,
    sortedLeads,
    paginatedLeads,
    filters,
    setFilter,
    toggleArrayFilter,
    resetFilters,
    sortField,
    sortDir,
    toggleSort,
    page,
    setPage: (p) => { page.value = p },
    pageSize,
    setPageSize: (size) => { pageSize.value = size },
    totalPages,
    kpis,
    uniqueVilles,
    uniqueSegments: UNIQUE_SEGMENTS,
    uniqueStatuses: UNIQUE_STATUSES,
    activeFilterCount,
    updateLeadStatus,
    updateLead,
    totalFromData: computed(() => allLeads.value.length),
    reloadLeads: fetchLeads,
  }
}