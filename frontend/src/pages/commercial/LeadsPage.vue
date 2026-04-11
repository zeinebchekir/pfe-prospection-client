<template>
  <div>
    <div class="flex min-h-screen bg-tacir-lightgray/30">

    <!-- Sidebar -->
    <TheSidebar />

    <!-- Main content -->
    <div class="flex-1 flex flex-col min-w-0">

      <!-- Page header -->
      <header class="h-16 border-b border-border bg-white sticky top-0 z-40 px-6 flex items-center justify-between shadow-sm">
        <div class="flex items-center gap-3">
          <div class="md:hidden w-10" />
          <div class="flex items-center gap-2">
            <Building2 class="w-5 h-5 text-tacir-blue" />
            <div>
              <h1 class="text-sm font-semibold text-tacir-darkblue">Mes leads</h1>
              <p class="text-[11px] text-tacir-darkgray hidden sm:block">
                Gérez et qualifiez votre portefeuille de prospects B2B
              </p>
            </div>
          </div>
        </div>

        <div class="flex items-center gap-3">
          <span class="hidden sm:inline-flex items-center gap-1.5 bg-tacir-blue/8 text-tacir-blue border border-tacir-blue/15 text-[10px] font-semibold uppercase tracking-widest px-3 py-1 rounded-full">
            <span class="w-1.5 h-1.5 rounded-full bg-tacir-lightblue animate-pulse" />
            COMMERCIAL
          </span>
          <button
            id="leads-new-btn"
            class="inline-flex items-center gap-2 h-9 px-4 text-sm font-medium rounded-md bg-tacir-blue text-white hover:opacity-90 transition-opacity"
          >
            <Plus class="w-4 h-4" /> Nouveau lead
          </button>
        </div>
      </header>

      <!-- Page body -->
      <main class="flex-1 p-6 md:p-8 overflow-y-auto">
        <div class="max-w-[1400px] mx-auto space-y-6">

          <!-- KPI cards -->
          <LeadKPICards :kpis="kpis" />

          <!-- Filters -->
          <LeadFiltersBar
            :filters="filters"
            :active-count="activeFilterCount"
            :unique-villes="uniqueVilles"
            :unique-segments="uniqueSegments"
            :unique-statuses="uniqueStatuses"
            @update:filter="handleFilterUpdate"
            @toggle-array="handleToggleArray"
            @reset="resetFilters"
          />

          <!-- "Add from API" banner — shown when search yields no local results -->
          <Transition name="fade-banner">
            <div
              v-if="showAddBanner"
              class="rounded-xl border border-tacir-blue/30 bg-blue-50/60 px-5 py-4 flex items-center justify-between gap-4 shadow-sm"
            >
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-full bg-tacir-blue/10 flex items-center justify-center flex-shrink-0">
                  <SearchX class="w-4 h-4 text-tacir-blue" />
                </div>
                <div>
                  <p class="text-sm font-semibold text-tacir-darkblue">
                    Aucun résultat local pour "{{ filters.search }}"
                  </p>
                  <p class="text-xs text-muted-foreground mt-0.5">
                    Rechercher cette entreprise sur DataGouv et l'ajouter à votre base ?
                  </p>
                </div>
              </div>
              <button
                @click="addFromQuery"
                :disabled="isAddingFromApi"
                class="inline-flex items-center gap-2 h-9 px-4 text-sm font-medium rounded-md bg-tacir-blue text-white hover:opacity-90 transition-opacity disabled:opacity-60 flex-shrink-0"
              >
                <Loader2 v-if="isAddingFromApi" class="w-4 h-4 animate-spin" />
                <Plus v-else class="w-4 h-4" />
                {{ isAddingFromApi ? 'Recherche...' : 'Rechercher & Ajouter' }}
              </button>
            </div>
          </Transition>

          <!-- Table card -->
          <div class="bg-white rounded-xl border border-border shadow-card overflow-hidden relative">
            <div v-if="isLoading" class="absolute inset-0 z-10 bg-white/70 backdrop-blur-sm flex items-center justify-center">
              <div class="flex flex-col items-center gap-2">
                <Loader2 class="h-8 w-8 animate-spin text-tacir-blue" />
                <span class="text-sm font-medium text-tacir-darkgray">Chargement des données...</span>
              </div>
            </div>
            <LeadTable
              :leads="paginatedLeads"
              :sort-field="sortField"
              :sort-dir="sortDir"
              @sort="toggleSort"
              @preview="previewLead = $event"
              @edit="editLead = $event"
              @delete="handleDelete"
              @navigate="handleNavigate"
            />

            <!-- Pagination -->
            <div class="px-4 pb-4">
              <LeadPagination
                :page="page"
                :total-pages="totalPages"
                :total-items="filteredLeads.length"
                :page-size="pageSize"
                @page-change="setPage"
                @size-change="setPageSize"
              />
            </div>
          </div>

        </div>
      </main>
    </div>
  </div>

  <!-- Preview drawer -->
  <LeadPreviewDrawer
    :lead="previewLead"
    :open="previewLead !== null"
    @close="previewLead = null"
    @navigate="handleNavigate"
    @edit="(l) => { previewLead = null; editLead = l }"
    @delete="handleDelete"
  />

  <!-- Edit modal -->
  <LeadEditModal
    :lead="editLead"
    :open="editLead !== null"
    @close="editLead = null"
    @save="handleSave"
  />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { Building2, Plus, Loader2, SearchX } from 'lucide-vue-next'
import { toast } from 'vue-sonner'

import TheSidebar     from '@/components/AppSidebar.vue'
import LeadKPICards   from '@/components/leads/LeadKPICards.vue'
import LeadFiltersBar from '@/components/leads/LeadFiltersBar.vue'
import LeadTable      from '@/components/leads/LeadTable.vue'
import LeadPagination from '@/components/leads/LeadPagination.vue'
import LeadPreviewDrawer from '@/components/leads/LeadPreviewDrawer.vue'
import LeadEditModal  from '@/components/leads/LeadEditModal.vue'

import { useLeads } from '@/composables/useLeads'
import { adaptLead } from '@/lib/leadAdapter'

const router = useRouter()

const {
  allLeads,
  filteredLeads,
  paginatedLeads,
  filters,
  setFilter,
  toggleArrayFilter,
  resetFilters,
  sortField,
  sortDir,
  toggleSort,
  page,
  setPage,
  pageSize,
  setPageSize,
  totalPages,
  kpis,
  uniqueVilles,
  uniqueSegments,
  uniqueStatuses,
  activeFilterCount,
  updateLead,
  isLoading,
} = useLeads()

// Local UI state
const previewLead     = ref(null)
const editLead        = ref(null)
const isAddingFromApi = ref(false)

// Show banner only when: search query present, not loading, and zero local results
const showAddBanner = computed(() =>
  !!filters.value.search.trim() &&
  !isLoading.value &&
  filteredLeads.value.length === 0
)

// ---- Event handlers ----

function handleFilterUpdate(key, value) {
  setFilter(key, value)
}

function handleToggleArray(key, value) {
  toggleArrayFilter(key, value)
}

function handleNavigate(lead) {
  router.push(`/commercial/leads/${lead.id}`)
}

function handleDelete(lead) {
  console.info(`[Leads] Delete requested for ${lead.nom} (${lead.id})`)
}

function handleSave(id, updates) {
  updateLead(id, updates)
}

// ---- Add from DataGouv via API ----
async function addFromQuery() {
  const query = filters.value.search.trim()
  if (!query) return

  isAddingFromApi.value = true
  try {
    const baseUrl = import.meta.env.VITE_FASTAPI_URL || 'http://localhost:8001'
    const res = await axios.post(`${baseUrl}/entreprises/add_from_query/${encodeURIComponent(query)}`)

    if (res.data?.status === 'success' && res.data?.lead) {
      const raw = res.data.lead
      // Adapt and push to local store
      const adapted = adaptLead({
        identifiant:            raw.identifiant,
        siren:                  raw.siren,
        nom:                    raw.nom,
        ville:                  raw.ville,
        code_postal:            raw.code_postal,
        pays:                   raw.pays,
        secteur_activite:       raw.secteur_activite,
        forme_juridique:        raw.forme_juridique,
        taille_entrep:          raw.taille_entrep,
        ca:                     raw.ca ?? null,
        dirigeants:             raw.dirigeants || [],
      }, allLeads.value.length)

      allLeads.value.unshift(adapted)

      toast.success(`Entreprise ajoutée : ${raw.nom}`, {
        description: `${raw.ville || ''} · ${raw.secteur_activite || ''}`.replace(/^ · | · $/g, '')
      })
      // Clear search so the new lead is visible
      setFilter('search', '')
    } else {
      toast.warning('Aucune entreprise trouvée', {
        description: `Aucun résultat pour "${query}" sur DataGouv.`,
      })
    }
  } catch (err) {
    console.error('[Leads] add_from_query error:', err)
    toast.error('Erreur de recherche', {
      description: err?.response?.data?.detail || 'Impossible de contacter DataGouv.',
    })
  } finally {
    isAddingFromApi.value = false
  }
}
</script>

<style scoped>
.shadow-card {
  box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(48,62,140,0.06);
}
.fade-banner-enter-active,
.fade-banner-leave-active { transition: all 0.25s ease; }
.fade-banner-enter-from,
.fade-banner-leave-to     { opacity: 0; transform: translateY(-6px); }
</style>
