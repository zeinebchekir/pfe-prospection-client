/**
 * useLeads composable — Vue 3 port of the React use-leads hook.
 *
 * Provides:
 *  - allLeads: all UI-adapted leads (from mock or API)
 *  - filters / setFilter / resetFilters: cumulative filter state
 *  - sortField / sortDir / toggleSort: sorting
 *  - page / setPage / pageSize / totalPages: pagination
 *  - filteredLeads / sortedLeads / paginatedLeads: derived arrays
 *  - kpis: KPI computed from filteredLeads
 *  - uniqueVilles, uniqueSegments, uniqueStatuses: dropdown data
 *  - activeFilterCount: badge counter
 *  - updateLead / updateLeadStatus: optimistic local mutations
 *
 * Filter bug fixes vs Lovable original:
 *  - Page is reset to 1 on every filter change (prevents ghost pages)
 *  - All bool filters use strict null comparison (avoids false=="" bug)
 *  - Filter count correctly includes scoreMin/Max, caMin/Max as single entry
 *  - Score/CA range filters correctly skip leads with null values
 */

import { ref, computed, watch, onMounted } from 'vue'
import axios from 'axios'
import { adaptLeadResponse } from '@/lib/leadAdapter'

// ---- Constants ----

export const INITIAL_FILTERS = {
  search: '',
  segments: [],    // LeadSegment[]
  statuses: [],    // LeadStatus[]
  villes: [],      // string[]
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



// ---- Filter count ----

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

// ---- Composable ----

export function useLeads() {
  // Source data
  const allLeads = ref([])
  const isLoading = ref(false)

  // Fetch leads from FastAPI
  async function fetchLeads() {
    isLoading.value = true
    try {
      const baseUrl = import.meta.env.VITE_FASTAPI_URL || 'http://localhost:8001'
      // Fetch a generous chunk to allow rich client-side filtering/sorting
      const res = await axios.get(`${baseUrl}/entreprises/`, {
        params: { skip: 0, limit: 1000 }
      })
      const rawData = Array.isArray(res.data) ? res.data : (res.data.data || [])
      allLeads.value = adaptLeadResponse(rawData)
    } catch (err) {
      console.error('[Leads] Fetch error:', err)
    } finally {
      isLoading.value = false
    }
  }

  onMounted(() => {
    fetchLeads()
  })

  // Filter state
  const filters = ref({ ...INITIAL_FILTERS, segments: [], statuses: [], villes: [] })
  const sortField = ref('score')
  const sortDir = ref('desc')
  const page = ref(1)
  const pageSize = ref(20)

  // Reset page whenever filters change
  watch(filters, () => { page.value = 1 }, { deep: true })
  // Reset page whenever pageSize changes
  watch(pageSize, () => { page.value = 1 })

  // ---- Derived: filteredLeads ----
  const filteredLeads = computed(() => {
    let result = [...allLeads.value]
    const f = filters.value

    // Global text search
    if (f.search) {
      const q = f.search.toLowerCase()
      result = result.filter((l) =>
        l.nom.toLowerCase().includes(q) ||
        l.siren.toLowerCase().includes(q) ||
        l.siret.toLowerCase().includes(q) ||
        l.identifiant.toLowerCase().includes(q) ||
        l.ville.toLowerCase().includes(q) ||
        l.codePostal.toLowerCase().includes(q) ||
        l.secteurActivite.toLowerCase().includes(q) ||
        l.formeJuridique.toLowerCase().includes(q) ||
        l.tailleEntreprise.toLowerCase().includes(q) ||
        l.dirigeants.some((d) => d.fullName.toLowerCase().includes(q))
      )
    }

    // Array filters (multi-select)
    if (f.segments.length) {
      result = result.filter((l) => f.segments.includes(l.segment))
    }
    if (f.statuses.length) {
      result = result.filter((l) => f.statuses.includes(l.status))
    }
    if (f.villes.length) {
      result = result.filter((l) => f.villes.includes(l.ville))
    }

    // Boolean presence filters — strict null check
    if (f.hasBoamp === true)  result = result.filter((l) => l.hasBoamp)
    if (f.hasBoamp === false) result = result.filter((l) => !l.hasBoamp)

    if (f.hasEmail === true)  result = result.filter((l) => l.hasEmail)
    if (f.hasEmail === false) result = result.filter((l) => !l.hasEmail)

    if (f.hasTelephone === true)  result = result.filter((l) => l.hasTelephone)
    if (f.hasTelephone === false) result = result.filter((l) => !l.hasTelephone)

    if (f.hasLinkedin === true)  result = result.filter((l) => l.hasLinkedinDirigeant)
    if (f.hasLinkedin === false) result = result.filter((l) => !l.hasLinkedinDirigeant)

    if (f.hasDirigeants === true)  result = result.filter((l) => l.nbDirigeants > 0)
    if (f.hasDirigeants === false) result = result.filter((l) => l.nbDirigeants === 0)

    // Numeric range filters — skip when lead value is null
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

  // ---- Derived: sortedLeads ----
  const sortedLeads = computed(() => {
    const sorted = [...filteredLeads.value]
    sorted.sort((a, b) => {
      let valA, valB
      switch (sortField.value) {
        case 'nom':            valA = a.nom;            valB = b.nom;            break
        case 'segment':        valA = a.segment;        valB = b.segment;        break
        case 'ca':             valA = a.ca ?? 0;        valB = b.ca ?? 0;        break
        case 'score':          valA = a.score;          valB = b.score;          break
        case 'completude':     valA = a.completude;     valB = b.completude;     break
        case 'probaConversion':valA = a.probaConversion;valB = b.probaConversion;break
        case 'nbLocaux':       valA = a.nbLocaux ?? 0;  valB = b.nbLocaux ?? 0;  break
        case 'ville':          valA = a.ville;          valB = b.ville;          break
        case 'nbDirigeants':   valA = a.nbDirigeants;   valB = b.nbDirigeants;   break
        default:               valA = a.score;          valB = b.score
      }
      if (typeof valA === 'string') {
        const cmp = valA.localeCompare(valB)
        return sortDir.value === 'asc' ? cmp : -cmp
      }
      return sortDir.value === 'asc' ? valA - valB : valB - valA
    })
    return sorted
  })

  // ---- Derived: pagination ----
  const totalPages = computed(() => Math.ceil(sortedLeads.value.length / pageSize.value))

  const paginatedLeads = computed(() => {
    const start = (page.value - 1) * pageSize.value
    return sortedLeads.value.slice(start, start + pageSize.value)
  })

  // ---- Derived: KPIs (based on filteredLeads, not paginated) ----
  const kpis = computed(() => {
    const leads = filteredLeads.value
    const total = leads.length
    if (total === 0) {
      return { total: 0, avgScore: 0, avgProba: 0, avgCompletude: 0, totalCA: 0, qualified: 0, opportunities: 0 }
    }
    const avgScore = Math.round(leads.reduce((s, l) => s + l.score, 0) / total)
    const avgProba = Math.round(leads.reduce((s, l) => s + l.probaConversion, 0) / total)
    const avgCompletude = Math.round(leads.reduce((s, l) => s + l.completude, 0) / total)
    const totalCA = leads.reduce((s, l) => s + (l.ca ?? 0), 0)
    const qualified = leads.filter((l) => l.status === 'Qualifié').length
    const opportunities = leads.filter((l) => l.status === 'Opportunité').length
    return { total, avgScore, avgProba, avgCompletude, totalCA, qualified, opportunities }
  })

  // ---- Unique values for filter dropdowns (from allLeads, not filtered) ----
  const uniqueVilles = computed(() =>
    [...new Set(allLeads.value.map((l) => l.ville).filter((v) => v !== '—'))].sort()
  )

  // ---- Active filter count ----
  const activeFilterCount = computed(() => countActiveFilters(filters.value))

  // ---- Actions ----

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
  }
}
