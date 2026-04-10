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
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Building2, Plus, Loader2 } from 'lucide-vue-next'

import TheSidebar     from '@/components/AppSidebar.vue'
import LeadKPICards   from '@/components/leads/LeadKPICards.vue'
import LeadFiltersBar from '@/components/leads/LeadFiltersBar.vue'
import LeadTable      from '@/components/leads/LeadTable.vue'
import LeadPagination from '@/components/leads/LeadPagination.vue'
import LeadPreviewDrawer from '@/components/leads/LeadPreviewDrawer.vue'
import LeadEditModal  from '@/components/leads/LeadEditModal.vue'

import { useLeads } from '@/composables/useLeads'

const router = useRouter()

const {
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
const previewLead = ref(null)
const editLead    = ref(null)

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
  // Simulation — hook up to API later
  console.info(`[Leads] Delete requested for ${lead.nom} (${lead.id})`)
}

function handleSave(id, updates) {
  updateLead(id, updates)
}
</script>

<style scoped>
.shadow-card {
  box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(48,62,140,0.06);
}
</style>
