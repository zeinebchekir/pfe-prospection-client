<template>
  <div>
  <div class="flex min-h-screen bg-tacir-lightgray/30">
    <TheSidebar />

    <div class="flex min-w-0 flex-1 flex-col">
      <header class="sticky top-0 z-40 flex h-16 items-center justify-between border-b border-border bg-white px-6 shadow-sm">
        <div class="flex items-center gap-3">
          <Activity class="h-5 w-5 text-tacir-blue" />
          <div>
            <h1 class="text-sm font-semibold text-tacir-darkblue">Analyse Comportementale</h1>
            <p class="hidden text-[11px] text-tacir-darkgray sm:block">
              Scoring comportemental base sur les sessions visiteur.
            </p>
          </div>
        </div>

        <div class="flex items-center gap-3">
          <Badge variant="outline" class="hidden border-tacir-blue/20 bg-tacir-blue/5 text-tacir-blue sm:inline-flex">
            {{ kpis.total_leads }} leads
          </Badge>
          <button
            class="inline-flex h-9 items-center justify-center rounded-md bg-tacir-blue px-4 text-sm font-semibold text-white transition-opacity hover:opacity-90"
            @click="showCreateDialog = true"
          >
            Ajouter un lead
          </button>
        </div>
      </header>

      <main class="flex-1 overflow-y-auto p-6 md:p-8">
        <div class="mx-auto max-w-[1500px] space-y-6">
          <section class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <MetricCard label="Total Leads" :value="kpis.total_leads" />
            <MetricCard label="HOT Leads" :value="kpis.total_hot" tone="hot" />
            <MetricCard label="WARM Leads" :value="kpis.total_warm" tone="warm" />
            <MetricCard label="COLD Leads" :value="kpis.total_cold" tone="cold" />
            <MetricCard label="Score Moyen" :value="formatScore(kpis.average_score)" />
            <MetricCard label="Bounce Rate Moyen" :value="formatPercent(kpis.average_bounce_rate)" />
            <MetricCard label="Leads actifs" :value="kpis.active_leads_last_date" />
            <MetricCard label="Nouvelles visites" :value="kpis.new_visits" />
          </section>

          <section class="grid gap-4 xl:grid-cols-5">
            <Card class="border-border/80 xl:col-span-2">
              <CardContent class="p-5">
                <ChartTitle title="Repartition HOT/WARM/COLD" />
                <div class="mt-5 space-y-3">
                  <SegmentBar
                    v-for="row in segmentDistribution"
                    :key="row.segment"
                    :label="row.segment"
                    :value="row.count"
                    :percent="segmentPercent(row.count)"
                    :max="segmentMax"
                  />
                </div>
              </CardContent>
            </Card>

            <Card class="border-border/80">
              <CardContent class="space-y-4 p-5">
                <div>
                  <p class="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">Nombre de leads</p>
                  <p class="mt-1 text-xs text-muted-foreground">Repartition des leads chauds, tiedes et froids.</p>
                </div>

                <div class="grid grid-cols-3 gap-3">
                  <div class="rounded-xl border border-emerald-200 bg-emerald-50/80 px-3 py-3">
                    <p class="text-[11px] font-semibold uppercase tracking-wide text-emerald-700">Chaud</p>
                    <p class="mt-2 text-2xl font-bold text-emerald-900">{{ leadCounts.hot }}</p>
                  </div>
                  <div class="rounded-xl border border-amber-200 bg-amber-50/80 px-3 py-3">
                    <p class="text-[11px] font-semibold uppercase tracking-wide text-amber-700">Tiede</p>
                    <p class="mt-2 text-2xl font-bold text-amber-900">{{ leadCounts.warm }}</p>
                  </div>
                  <div class="rounded-xl border border-rose-200 bg-rose-50/80 px-3 py-3">
                    <p class="text-[11px] font-semibold uppercase tracking-wide text-rose-700">Froid</p>
                    <p class="mt-2 text-2xl font-bold text-rose-900">{{ leadCounts.cold }}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card class="border-border/80 xl:col-span-3">
              <CardContent class="p-5">
                <ChartTitle title="Distribution scores" />
                <div class="mt-5 flex h-56 items-end gap-2 overflow-x-auto pb-2">
                  <div
                    v-for="row in scoreDistribution"
                    :key="row.bucket"
                    class="flex h-full min-w-14 flex-1 flex-col justify-end gap-2"
                    :title="`${row.bucket}-${Number(row.bucket) + 9}: ${row.count}`"
                  >
                    <span class="text-center text-[11px] font-semibold text-tacir-darkblue">
                      {{ compactNumber(row.count) }}
                    </span>
                    <div
                      class="mx-auto w-full rounded-t bg-emerald-500/75"
                      :style="{ height: `${barHeight(row.count, scoreMax)}%` }"
                    />
                    <span class="truncate text-center text-[11px] text-muted-foreground">
                      {{ Number(row.bucket) }}-{{ Number(row.bucket) + 9 }}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card class="border-border/80">
            <CardContent class="space-y-4 p-4 md:p-5">
              <div class="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
                <div class="relative w-full xl:max-w-xl">
                  <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    v-model="search"
                    class="pl-9"
                    placeholder="Rechercher par entreprise, contact, email, poste, pays, secteur ou source"
                    @input="handleSearchInput"
                  />
                </div>

                <div class="flex flex-wrap items-center justify-between gap-3">
                  <p class="text-xs text-muted-foreground">
                    <span class="font-semibold text-foreground">Filtres actifs :</span>
                    {{ activeFiltersLabel }}
                  </p>
                  <button
                    v-if="hasActiveFilters"
                    class="inline-flex h-9 items-center gap-2 rounded-md border border-input px-4 text-sm font-medium transition-colors hover:bg-accent"
                    @click="resetFilters"
                  >
                    <RotateCcw class="h-4 w-4" />
                    Reinitialiser
                  </button>
                </div>
              </div>

              <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-6">
                <div class="space-y-1.5">
                  <p class="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">Type</p>
                  <Select v-model="filters.temperature" @update:modelValue="handleFilterChange">
                    <SelectTrigger class="h-10 rounded-md bg-white text-sm">
                      <SelectValue placeholder="Tous les types" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ALL">Tous les types</SelectItem>
                      <SelectItem value="HOT">Chaud</SelectItem>
                      <SelectItem value="WARM">Tiede</SelectItem>
                      <SelectItem value="COLD">Froid</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div class="space-y-1.5">
                  <p class="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">Score</p>
                  <Select v-model="filters.scoreOrder" @update:modelValue="handleFilterChange">
                    <SelectTrigger class="h-10 rounded-md bg-white text-sm">
                      <SelectValue placeholder="Tri du score" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="default">Tri par defaut</SelectItem>
                      <SelectItem value="desc">Score decroissant</SelectItem>
                      <SelectItem value="asc">Score croissant</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div class="space-y-1.5">
                  <p class="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">Pays</p>
                  <Select v-model="filters.country" @update:modelValue="handleFilterChange">
                    <SelectTrigger class="h-10 rounded-md bg-white text-sm">
                      <SelectValue placeholder="Tous les pays" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ALL">Tous les pays</SelectItem>
                      <SelectItem
                        v-for="country in formOptions.countries"
                        :key="country"
                        :value="country"
                      >
                        {{ country }}
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div class="space-y-1.5">
                  <p class="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">Job Title</p>
                  <Select v-model="filters.jobTitle" @update:modelValue="handleFilterChange">
                    <SelectTrigger class="h-10 rounded-md bg-white text-sm">
                      <SelectValue placeholder="Tous les postes" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ALL">Tous les postes</SelectItem>
                      <SelectItem
                        v-for="jobTitle in formOptions.job_titles"
                        :key="jobTitle"
                        :value="jobTitle"
                      >
                        {{ jobTitle }}
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div class="space-y-1.5">
                  <p class="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">Taille entreprise</p>
                  <Select v-model="filters.companySize" @update:modelValue="handleFilterChange">
                    <SelectTrigger class="h-10 rounded-md bg-white text-sm">
                      <SelectValue placeholder="Toutes les tailles" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ALL">Toutes les tailles</SelectItem>
                      <SelectItem
                        v-for="companySize in formOptions.company_sizes"
                        :key="companySize"
                        :value="companySize"
                      >
                        {{ companySize }}
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div class="space-y-1.5">
                  <p class="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">Industry</p>
                  <Select v-model="filters.industry" @update:modelValue="handleFilterChange">
                    <SelectTrigger class="h-10 rounded-md bg-white text-sm">
                      <SelectValue placeholder="Tous les secteurs" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ALL">Tous les secteurs</SelectItem>
                      <SelectItem
                        v-for="industry in formOptions.industries"
                        :key="industry"
                        :value="industry"
                      >
                        {{ industry }}
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>

          <div class="relative overflow-hidden rounded-xl border border-border bg-white shadow-card">
            <div
              v-if="isLoading"
              class="absolute inset-0 z-10 flex items-center justify-center bg-white/70 backdrop-blur-sm"
            >
              <div class="flex flex-col items-center gap-2">
                <Loader2 class="h-8 w-8 animate-spin text-tacir-blue" />
                <span class="text-sm font-medium text-tacir-darkgray">Chargement des opportunites...</span>
              </div>
            </div>

            <OpportunityLeadTable
              :leads="opportunityLeads"
              :loading="isLoading"
              @edit="openEditDialog"
              @delete="openDeleteDialog"
            />

            <div class="px-4 pb-4">
              <LeadPagination
                :page="page"
                :total-pages="totalPages"
                :total-items="totalItems"
                :page-size="pageSize"
                @page-change="handlePageChange"
                @size-change="handlePageSizeChange"
              />
            </div>
          </div>

          <OpportunityPerformancePanel
            :performance="performance"
            :loading="isPerformanceLoading"
            :training="isTraining"
            @train="handleTrainModel"
          />
        </div>
      </main>
    </div>
  </div>

  <OpportunityLeadFormDialog
    v-model:open="showCreateDialog"
    :saving="isSavingLead"
    mode="create"
    list-id-prefix="opportunity-create"
    :options-loading="isFormOptionsLoading"
    :job-title-options="formOptions.job_titles"
    :industry-options="formOptions.industries"
    :lead-source-options="formOptions.lead_sources"
    :last-activity-options="formOptions.last_activities"
    :last-notable-activity-options="formOptions.last_notable_activities"
    @submit="handleCreateLead"
  />

  <OpportunityLeadFormDialog
    v-model:open="showEditDialog"
    :saving="isUpdatingLead"
    mode="edit"
    list-id-prefix="opportunity-edit"
    :lead="editingLead"
    :options-loading="isFormOptionsLoading"
    :job-title-options="formOptions.job_titles"
    :industry-options="formOptions.industries"
    :lead-source-options="formOptions.lead_sources"
    :last-activity-options="formOptions.last_activities"
    :last-notable-activity-options="formOptions.last_notable_activities"
    @submit="handleUpdateLead"
  />

  <OpportunityLeadDeleteDialog
    v-model:open="showDeleteDialog"
    :deleting="isDeletingLead"
    :lead="deletingLead"
    @confirm="handleDeleteLead"
  />
  </div>
</template>

<script setup>
import { computed, defineComponent, h, onMounted, ref } from 'vue'
import axios from 'axios'
import { Activity, Bell, RefreshCcw, Search, X } from 'lucide-vue-next'
import { toast } from 'vue-sonner'

import TheSidebar from '@/components/AppSidebar.vue'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'

const behavioralApi = axios.create({
  baseURL: import.meta.env.VITE_IA_ML_URL || 'http://localhost:8002',
})

const emptyKpis = {
  total_leads: 0,
  total_hot: 0,
  total_warm: 0,
  total_cold: 0,
  average_score: null,
  average_bounce_rate: null,
  active_leads_last_date: 0,
  new_visits: 0,
  segment_distribution: [],
  visits_evolution: [],
  device_distribution: [],
  score_distribution: [],
  traffic_sources: [],
}

const kpis = ref({ ...emptyKpis })
const topLeads = ref([])
const notifications = ref([])
const leads = ref({ page: 1, page_size: 20, total: 0, total_pages: 1, results: [] })
const selectedLead = ref(null)
const selectedNotification = ref(null)
const showNotifications = ref(false)
const topLimit = ref(10)
const page = ref(1)
const visitPeriod = ref('month')
const segmentFilter = ref('')
const deviceFilter = ref('')
const search = ref('')
const activeSearch = ref('')
const isRecalculating = ref(false)
let searchTimer = null

const leadCounts = computed(() => summary.value?.lead_counts || createEmptySummary().lead_counts)
const averageScoreLabel = computed(() => {
  const value = summary.value?.average_score
  if (value === null || value === undefined) return '-'
  return `${Number(value).toFixed(1)}/100`
})
const hasActiveFilters = computed(() => {
  return Boolean(
    activeSearch.value
      || filters.value.temperature !== 'ALL'
      || filters.value.scoreOrder !== 'default'
      || filters.value.country !== 'ALL'
      || filters.value.jobTitle !== 'ALL'
      || filters.value.companySize !== 'ALL'
      || filters.value.industry !== 'ALL',
  )
})
const activeFiltersLabel = computed(() => {
  const labels = []

  if (activeSearch.value) labels.push(`Recherche: ${activeSearch.value}`)
  if (filters.value.temperature !== 'ALL') labels.push(`Type: ${temperatureLabel(filters.value.temperature)}`)
  if (filters.value.scoreOrder === 'desc') labels.push('Score: decroissant')
  if (filters.value.scoreOrder === 'asc') labels.push('Score: croissant')
  if (filters.value.country !== 'ALL') labels.push(`Pays: ${filters.value.country}`)
  if (filters.value.jobTitle !== 'ALL') labels.push(`Job Title: ${filters.value.jobTitle}`)
  if (filters.value.companySize !== 'ALL') labels.push(`Taille: ${filters.value.companySize}`)
  if (filters.value.industry !== 'ALL') labels.push(`Industry: ${filters.value.industry}`)

  return labels.length ? labels.join(' | ') : 'Aucun, toutes les opportunites sont affichees'
})

function normalizePerformance(payload) {
  if (!payload) return null
  if (payload.performance) return normalizePerformance(payload.performance)

  const normalized = { ...payload }
  delete normalized.status
  delete normalized.rescored_rows

  return Object.keys(normalized).length ? normalized : null
}

function normalizeSummary(payload) {
  const base = createEmptySummary()
  if (!payload || typeof payload !== 'object') return base

  return {
    lead_counts: {
      total: Number(payload?.lead_counts?.total || 0),
      hot: Number(payload?.lead_counts?.hot || 0),
      warm: Number(payload?.lead_counts?.warm || 0),
      cold: Number(payload?.lead_counts?.cold || 0),
    },
    average_score: payload.average_score === null || payload.average_score === undefined
      ? null
      : Number(payload.average_score),
    top_hot_limit: Number(payload.top_hot_limit || 5),
    top_hot_leads: Array.isArray(payload.top_hot_leads) ? payload.top_hot_leads : [],
  }
}

async function fetchOpportunityLeads() {
  isLoading.value = true

  try {
    const params = {
      page: page.value,
      page_size: pageSize.value,
    }

    if (activeSearch.value) params.search = activeSearch.value
    if (filters.value.temperature !== 'ALL') params.temperature = filters.value.temperature
    if (filters.value.scoreOrder !== 'default') params.score_order = filters.value.scoreOrder
    if (filters.value.country !== 'ALL') params.country = filters.value.country
    if (filters.value.jobTitle !== 'ALL') params.job_title = filters.value.jobTitle
    if (filters.value.companySize !== 'ALL') params.company_size = filters.value.companySize
    if (filters.value.industry !== 'ALL') params.industry = filters.value.industry

    const { data } = await api.get('/leads/opportunities/', { params })
    opportunityLeads.value = data.results || []
    totalItems.value = data.count || 0
    totalPages.value = data.total_pages || 1
    page.value = data.page || 1
    summary.value = normalizeSummary(data.summary)
  } catch (error) {
    console.error('[OpportunityLeads] fetch error:', error)
    opportunityLeads.value = []
    totalItems.value = 0
    totalPages.value = 1
    summary.value = createEmptySummary()
    toast.error("Impossible de charger les leads d'opportunite.")
  } finally {
    isLoading.value = false
  }
}

async function fetchPerformance() {
  isPerformanceLoading.value = true

  try {
    const { data } = await api.get('/leads/opportunities/performance/latest/')
    performance.value = normalizePerformance(data.performance)
  } catch (error) {
    if (error?.response?.status === 404) {
      performance.value = null
      return
    }
    console.error('[OpportunityLeads] performance error:', error)
    performance.value = null
  } finally {
    isPerformanceLoading.value = false
  }
}

async function fetchFormOptions(force = false) {
  if (isFormOptionsLoading.value) return
  if (!force && (formOptions.value.job_titles.length || formOptions.value.countries.length)) return

  isFormOptionsLoading.value = true

  try {
    const { data } = await api.get('/leads/opportunities/form-options/')
    formOptions.value = {
      countries: data?.options?.countries || [],
      industries: data?.options?.industries || [],
      company_sizes: data?.options?.company_sizes || [],
      job_titles: data?.options?.job_titles || [],
      lead_sources: data?.options?.lead_sources || [],
      last_activities: data?.options?.last_activities || [],
      last_notable_activities: data?.options?.last_notable_activities || [],
    }
  } catch (error) {
    console.error('[OpportunityLeads] form options error:', error)
    formOptions.value = {
      countries: [],
      industries: [],
      company_sizes: [],
      job_titles: [],
      lead_sources: [],
      last_activities: [],
      last_notable_activities: [],
    }
  } finally {
    isFormOptionsLoading.value = false
  }
}

async function handleCreateLead(payload) {
  isSavingLead.value = true

  try {
    const { data } = await api.post('/leads/opportunities/', payload)
    toast.success('Opportunite creee et scoree.', {
      description: data?.lead?.company_name || 'Le lead est maintenant disponible dans la liste.',
    })
    showCreateDialog.value = false
    await Promise.all([fetchOpportunityLeads(), fetchPerformance(), fetchFormOptions(true)])
  } catch (error) {
    console.error('[OpportunityLeads] create error:', error)
    toast.error("Impossible de creer l'opportunite.", {
      description: error?.response?.data?.detail || error?.response?.data?.message || 'Verifie que le service ia-ml est demarre.',
    })
  } finally {
    isSavingLead.value = false
  }
}

async function handleUpdateLead(payload) {
  if (!editingLead.value?.lead_id) return

  isUpdatingLead.value = true

  try {
    const { data } = await api.patch(`/leads/opportunities/${editingLead.value.lead_id}/`, payload)
    toast.success('Opportunite mise a jour et rescoree.', {
      description: data?.lead?.company_name || 'Le lead a ete mis a jour.',
    })
    showEditDialog.value = false
    editingLead.value = null
    await Promise.all([fetchOpportunityLeads(), fetchPerformance(), fetchFormOptions(true)])
  } catch (error) {
    console.error('[OpportunityLeads] update error:', error)
    toast.error("Impossible de modifier l'opportunite.", {
      description: error?.response?.data?.detail || error?.response?.data?.message || 'Le rescoring automatique a echoue.',
    })
  } finally {
    isUpdatingLead.value = false
  }
}

async function handleDeleteLead() {
  if (!deletingLead.value?.lead_id) return

  isDeletingLead.value = true

  try {
    await api.delete(`/leads/opportunities/${deletingLead.value.lead_id}/`)
    toast.success('Opportunite supprimee.', {
      description: deletingLead.value?.company_name || 'Le lead a ete retire de la base.',
    })
    showDeleteDialog.value = false
    deletingLead.value = null
    await Promise.all([fetchOpportunityLeads(), fetchFormOptions(true)])
  } catch (error) {
    console.error('[OpportunityLeads] delete error:', error)
    toast.error("Impossible de supprimer l'opportunite.", {
      description: error?.response?.data?.detail || 'Une erreur inattendue est survenue.',
    })
  } finally {
    isDeletingLead.value = false
  }
}

async function handleTrainModel() {
  isTraining.value = true

  try {
    const { data } = await api.post('/leads/opportunities/train/')
    performance.value = normalizePerformance(data.performance)
    toast.success("Le modele de scoring a ete entraine.", {
      description: data?.performance?.model_version || 'Les opportunites existantes ont ete rescourees.',
    })
    await fetchOpportunityLeads()
  } catch (error) {
    console.error('[OpportunityLeads] train error:', error)
    toast.error("Impossible de lancer l'entrainement.", {
      description: error?.response?.data?.detail || error?.response?.data?.message || 'Verifie le service ia-ml et les dependances ML.',
    })
  } finally {
    isTraining.value = false
  }
}

function handleSearchInput() {
  if (searchTimer) clearTimeout(searchTimer)

  searchTimer = setTimeout(() => {
    activeSearch.value = search.value.trim()
    page.value = 1
    fetchOpportunityLeads()
  }, 250)
}

function handleFilterChange() {
  page.value = 1
  fetchOpportunityLeads()
}

function handlePageChange(nextPage) {
  if (nextPage === page.value) return
  page.value = nextPage
  fetchOpportunityLeads()
}

function handlePageSizeChange(nextSize) {
  if (nextSize === pageSize.value) return
  pageSize.value = nextSize
  page.value = 1
  fetchOpportunityLeads()
}

function resetFilters() {
  if (searchTimer) clearTimeout(searchTimer)

  search.value = ''
  activeSearch.value = ''
  filters.value = {
    temperature: 'ALL',
    scoreOrder: 'default',
    country: 'ALL',
    jobTitle: 'ALL',
    companySize: 'ALL',
    industry: 'ALL',
  }
  page.value = 1
  fetchOpportunityLeads()
}

function openEditDialog(lead) {
  editingLead.value = lead
  showEditDialog.value = true
  fetchFormOptions()
}

function openDeleteDialog(lead) {
  deletingLead.value = lead
  showDeleteDialog.value = true
}

function temperatureLabel(value) {
  if (value === 'HOT') return 'Chaud'
  if (value === 'WARM') return 'Tiede'
  if (value === 'COLD') return 'Froid'
  return 'Tous'
}

onMounted(() => {
  fetchOpportunityLeads()
  fetchPerformance()
  fetchFormOptions()
})

onBeforeUnmount(() => {
  if (searchTimer) clearTimeout(searchTimer)
})

watch(showCreateDialog, (isOpen) => {
  if (isOpen) {
    fetchFormOptions()
  }
})

watch(showEditDialog, (isOpen) => {
  if (isOpen) {
    fetchFormOptions()
  } else {
    editingLead.value = null
  }
})

watch(showDeleteDialog, (isOpen) => {
  if (!isOpen) {
    deletingLead.value = null
  }
})
</script>

<style scoped>
.shadow-card {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 4px 16px rgba(48, 62, 140, 0.06);
}
</style>
