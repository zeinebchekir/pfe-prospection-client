<template>
  <div class="flex min-h-screen bg-tacir-lightgray/30">
    <TheSidebar />

    <div class="flex min-w-0 flex-1 flex-col">
      <header class="sticky top-0 z-40 flex h-16 items-center justify-between border-b border-border bg-white px-6 shadow-sm">
        <div class="flex items-center gap-3">
          <div class="w-10 md:hidden" />
          <div class="flex items-center gap-2">
            <Sparkles class="h-5 w-5 text-tacir-blue" />
            <div>
              <h1 class="text-sm font-semibold text-tacir-darkblue">Leads d'opportunite</h1>
              <p class="hidden text-[11px] text-tacir-darkgray sm:block">
                Liste commerciale alimentee depuis la table PostgreSQL `lead_opportunity`
              </p>
            </div>
          </div>
        </div>

        <div class="flex items-center gap-3">
          <Badge
            variant="outline"
            class="hidden border-tacir-blue/20 bg-tacir-blue/5 text-tacir-blue sm:inline-flex"
          >
            {{ totalItems }} leads affiches
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
        <div class="mx-auto max-w-[1400px] space-y-6">
          <div class="grid gap-4 lg:grid-cols-3">
            <Card class="border-border/80">
              <CardContent class="p-5">
                <p class="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">Total affiche</p>
                <p class="mt-2 text-3xl font-bold text-tacir-darkblue">{{ totalItems }}</p>
                <p class="mt-2 text-xs text-muted-foreground">
                  Nombre de leads correspondant a la recherche et aux filtres actifs.
                </p>
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

            <Card class="border-border/80">
              <CardContent class="p-5">
                <p class="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">Moyenne de score</p>
                <p class="mt-2 text-3xl font-bold text-tacir-darkblue">{{ averageScoreLabel }}</p>
                <p class="mt-2 text-xs text-muted-foreground">
                  Moyenne du score predictif sur les leads actuellement filtres.
                </p>
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

          <Card class="border-border/80">
            <CardContent class="p-5">
              <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div>
                  <p class="text-sm font-semibold text-tacir-darkblue">Top leads chauds</p>
                  <p class="text-xs text-muted-foreground">
                    Leads HOT les mieux notes, avec resume de l'historique de message et des activites recentes.
                  </p>
                </div>

                <div class="w-full md:w-[140px]">
                  <Select v-model="hotLeadLimit" @update:modelValue="handleHotLeadLimitChange">
                    <SelectTrigger class="h-10 rounded-md bg-white text-sm">
                      <SelectValue placeholder="Top 5" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="5">Top 5</SelectItem>
                      <SelectItem value="10">Top 10</SelectItem>
                      <SelectItem value="20">Top 20</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div v-if="topHotLeads.length" class="mt-4 grid gap-4 xl:grid-cols-2">
                <article
                  v-for="(lead, index) in topHotLeads"
                  :key="lead.lead_id"
                  class="rounded-2xl border border-border bg-white p-4 shadow-card"
                >
                  <div class="flex items-start justify-between gap-3">
                    <div class="min-w-0">
                      <div class="flex items-center gap-2">
                        <div class="flex h-7 w-7 items-center justify-center rounded-full bg-tacir-blue/10 text-xs font-semibold text-tacir-blue">
                          {{ index + 1 }}
                        </div>
                        <p class="truncate text-base font-semibold text-foreground">{{ lead.company_name }}</p>
                      </div>
                      <p class="mt-2 truncate text-xs text-muted-foreground">
                        {{ topLeadMeta(lead) }}
                      </p>
                    </div>

                    <div class="flex shrink-0 items-center gap-2">
                      <Badge class="border-emerald-200 bg-emerald-50 text-emerald-700">Chaud</Badge>
                      <Badge variant="outline" class="border-tacir-blue/20 bg-tacir-blue/5 text-tacir-blue">
                        {{ formatLeadScore(lead.lead_score_predicted) }}
                      </Badge>
                    </div>
                  </div>

                  <div class="mt-4 space-y-3">
                    <div>
                      <button
                        type="button"
                        class="text-left text-[11px] font-semibold uppercase tracking-wide text-muted-foreground transition-colors hover:text-tacir-blue"
                        @click="toggleHistorySummary(lead.lead_id)"
                      >
                        Resume de l'historique
                      </button>
                      <p class="mt-1 text-sm leading-6 text-foreground">
                        {{ isHistoryExpanded(lead.lead_id) ? (lead.history_summary_full || lead.history_summary) : (lead.history_summary_preview || lead.history_summary) }}
                      </p>
                      <button
                        v-if="lead.history_summary_full && lead.history_summary_preview && lead.history_summary_full !== lead.history_summary_preview"
                        type="button"
                        class="mt-2 text-xs font-medium text-tacir-blue transition-colors hover:underline"
                        @click="toggleHistorySummary(lead.lead_id)"
                      >
                        {{ isHistoryExpanded(lead.lead_id) ? 'Voir moins' : 'Voir tout' }}
                      </button>
                    </div>

                    <div>
                      <p class="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                        Activites
                      </p>
                      <p class="mt-1 text-sm leading-6 text-muted-foreground">{{ lead.activity_summary }}</p>
                    </div>
                  </div>
                </article>
              </div>

              <div
                v-else
                class="mt-4 rounded-xl border border-dashed border-border bg-muted/20 px-5 py-8 text-center"
              >
                <p class="text-sm font-medium text-foreground">Aucun lead chaud ne correspond aux filtres actuels.</p>
                <p class="mt-1 text-xs text-muted-foreground">
                  Essaie de retirer certains filtres ou de relancer l'entrainement pour mettre a jour les scores.
                </p>
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
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Loader2, RotateCcw, Search, Sparkles } from 'lucide-vue-next'
import { toast } from 'vue-sonner'

import api from '@/api/axios'
import TheSidebar from '@/components/AppSidebar.vue'
import LeadPagination from '@/components/leads/LeadPagination.vue'
import OpportunityLeadDeleteDialog from '@/components/opportunities/OpportunityLeadDeleteDialog.vue'
import OpportunityLeadFormDialog from '@/components/opportunities/OpportunityLeadFormDialog.vue'
import OpportunityLeadTable from '@/components/opportunities/OpportunityLeadTable.vue'
import OpportunityPerformancePanel from '@/components/opportunities/OpportunityPerformancePanel.vue'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

function createEmptySummary() {
  return {
    lead_counts: {
      total: 0,
      hot: 0,
      warm: 0,
      cold: 0,
    },
    average_score: null,
    top_hot_limit: 5,
    top_hot_leads: [],
  }
}

const opportunityLeads = ref([])
const summary = ref(createEmptySummary())
const isLoading = ref(false)
const isSavingLead = ref(false)
const isUpdatingLead = ref(false)
const isDeletingLead = ref(false)
const isPerformanceLoading = ref(false)
const isTraining = ref(false)
const performance = ref(null)
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const showDeleteDialog = ref(false)
const editingLead = ref(null)
const deletingLead = ref(null)
const isFormOptionsLoading = ref(false)
const formOptions = ref({
  countries: [],
  industries: [],
  company_sizes: [],
  job_titles: [],
  lead_sources: [],
  last_activities: [],
  last_notable_activities: [],
})
const filters = ref({
  temperature: 'ALL',
  scoreOrder: 'default',
  country: 'ALL',
  jobTitle: 'ALL',
  companySize: 'ALL',
  industry: 'ALL',
})
const hotLeadLimit = ref('5')
const search = ref('')
const activeSearch = ref('')
const page = ref(1)
const pageSize = ref(20)
const totalItems = ref(0)
const totalPages = ref(1)
const expandedHistoryLeadIds = ref([])

let searchTimer = null

const leadCounts = computed(() => summary.value?.lead_counts || createEmptySummary().lead_counts)
const topHotLeads = computed(() => summary.value?.top_hot_leads || [])
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
      hot_limit: hotLeadLimit.value,
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
    expandedHistoryLeadIds.value = []
    hotLeadLimit.value = String(summary.value.top_hot_limit || hotLeadLimit.value)
  } catch (error) {
    console.error('[OpportunityLeads] fetch error:', error)
    opportunityLeads.value = []
    totalItems.value = 0
    totalPages.value = 1
    summary.value = createEmptySummary()
    expandedHistoryLeadIds.value = []
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

function handleHotLeadLimitChange(nextValue) {
  hotLeadLimit.value = String(nextValue || hotLeadLimit.value)
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

function isHistoryExpanded(leadId) {
  return expandedHistoryLeadIds.value.includes(leadId)
}

function toggleHistorySummary(leadId) {
  if (isHistoryExpanded(leadId)) {
    expandedHistoryLeadIds.value = expandedHistoryLeadIds.value.filter((value) => value !== leadId)
    return
  }

  expandedHistoryLeadIds.value = [...expandedHistoryLeadIds.value, leadId]
}

function temperatureLabel(value) {
  if (value === 'HOT') return 'Chaud'
  if (value === 'WARM') return 'Tiede'
  if (value === 'COLD') return 'Froid'
  return 'Tous'
}

function formatLeadScore(value) {
  if (value === null || value === undefined) return '-'
  return `${Number(value)}/100`
}

function topLeadMeta(lead) {
  const parts = [lead.contact_name, lead.job_title, lead.country, lead.industry, lead.company_size]
  return parts.filter(Boolean).join(' | ') || 'Informations de profil non renseignees.'
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
