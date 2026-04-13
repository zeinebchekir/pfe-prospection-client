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
            @click="createOpen = true"
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

          <!-- "Search on DataGouv" banner — zero local results -->
          <Transition name="fade-banner">
            <div
              v-if="showSearchBanner"
              class="rounded-xl border border-tacir-blue/25 bg-gradient-to-r from-blue-50/80 to-indigo-50/60 px-5 py-4 flex items-center justify-between gap-4 shadow-sm"
            >
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-full bg-tacir-blue/10 flex items-center justify-center flex-shrink-0">
                  <SearchX class="w-4 h-4 text-tacir-blue" />
                </div>
                <div>
                  <p class="text-sm font-semibold text-tacir-darkblue">
                    Aucun résultat local pour <span class="text-tacir-blue">"{{ filters.search }}"</span>
                  </p>
                  <p class="text-xs text-muted-foreground mt-0.5">
                    Chercher cette entreprise sur DataGouv et choisir laquelle ajouter ?
                  </p>
                </div>
              </div>
              <button
                @click="startSearch"
                :disabled="isSearching"
                class="inline-flex items-center gap-2 h-9 px-4 text-sm font-medium rounded-md bg-tacir-blue text-white hover:opacity-90 transition-opacity disabled:opacity-60 flex-shrink-0"
              >
                <Loader2 v-if="isSearching" class="w-4 h-4 animate-spin" />
                <Search v-else class="w-4 h-4" />
                {{ isSearching ? 'Recherche…' : 'Rechercher sur DataGouv' }}
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

  <!-- ══════════════════════════════════════════════════════════ -->
  <!--  DataGouv Search Preview Modal                            -->
  <!-- ══════════════════════════════════════════════════════════ -->
  <Dialog :open="showPreviewModal" @update:open="closePreviewModal">
    <DialogContent class="max-w-2xl max-h-[88vh] p-0 flex flex-col overflow-hidden">

      <!-- Header -->
      <DialogHeader class="px-6 pt-6 pb-3 flex-shrink-0 border-b border-border">
        <DialogTitle class="text-base font-semibold flex items-center gap-2">
          <Globe class="w-4 h-4 text-tacir-blue" />
          Résultats DataGouv — <span class="text-tacir-blue">"{{ lastQuery }}"</span>
        </DialogTitle>
        <p class="text-xs text-muted-foreground mt-1">
          <span class="font-semibold text-foreground">{{ searchResults.length }}</span>
          entreprise{{ searchResults.length > 1 ? 's' : '' }} trouvée{{ searchResults.length > 1 ? 's' : '' }}.
          Inspectez la fiche avant d'ajouter à votre base.
        </p>
      </DialogHeader>

      <!-- Results list -->
      <div class="flex-1 overflow-y-auto px-4 py-3 space-y-2">
        <!-- Empty state -->
        <div v-if="searchResults.length === 0" class="text-center py-12 text-sm text-muted-foreground italic">
          Aucun résultat trouvé sur DataGouv.
        </div>

        <!-- Result cards -->
        <div
          v-for="(company, idx) in searchResults"
          :key="company.siren || idx"
          class="rounded-xl border transition-all duration-200"
          :class="isAlreadyKnown(company)
            ? 'border-border bg-muted/30'
            : expandedIdx === idx
              ? 'border-tacir-blue/40 bg-blue-50/20'
              : 'border-border hover:border-tacir-blue/25 hover:bg-blue-50/10'"
        >
          <!-- ── Compact header row ── -->
          <div class="flex items-center gap-3 px-4 py-3">
            <!-- Avatar -->
            <div
              :class="['w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0',
                       AVATAR_COLORS[idx % AVATAR_COLORS.length],
                       isAlreadyKnown(company) ? 'opacity-60' : '']"
            >
              {{ (company.nom || '?').slice(0, 2).toUpperCase() }}
            </div>

            <!-- Core info -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 flex-wrap">
                <p class="text-sm font-semibold text-foreground truncate">{{ company.nom }}</p>
                <!-- Already-in-DB badge -->
                <span
                  v-if="existingSirens.has(company.siren)"
                  class="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wide px-1.5 py-0.5 rounded-md bg-purple-100 text-purple-700 border border-purple-200 flex-shrink-0"
                >
                  <Database class="w-2.5 h-2.5" /> Déjà dans votre base
                </span>
                <!-- Added-this-session badge -->
                <span
                  v-else-if="addedSirens.has(company.siren)"
                  class="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wide px-1.5 py-0.5 rounded-md bg-emerald-100 text-emerald-700 border border-emerald-200 flex-shrink-0"
                >
                  <CheckCircle2 class="w-2.5 h-2.5" /> Ajouté
                </span>
              </div>
              <div class="flex flex-wrap items-center gap-x-3 gap-y-0 mt-0.5">
                <span v-if="company.ville" class="text-[11px] text-muted-foreground flex items-center gap-1">
                  <MapPin class="w-2.5 h-2.5" />{{ company.ville }}<span v-if="company.code_postal" class="ml-0.5 text-muted-foreground/70">({{ company.code_postal }})</span>
                </span>
                <span v-if="company.siren" class="text-[11px] text-muted-foreground font-mono">SIREN {{ company.siren }}</span>
                <span v-if="company.forme_juridique" class="text-[11px] text-muted-foreground">{{ company.forme_juridique }}</span>
              </div>
            </div>

            <!-- Action buttons -->
            <div class="flex items-center gap-1.5 flex-shrink-0">
              <!-- Voir fiche toggle -->
              <button
                @click="expandedIdx = expandedIdx === idx ? -1 : idx"
                class="inline-flex items-center gap-1 h-7 px-2.5 text-[11px] font-medium rounded-lg border border-border hover:border-tacir-blue/30 hover:bg-tacir-blue/5 text-tacir-darkgray hover:text-tacir-blue transition-all"
                :class="expandedIdx === idx ? 'border-tacir-blue/30 bg-tacir-blue/5 text-tacir-blue' : ''"
              >
                <Eye v-if="expandedIdx !== idx" class="w-3 h-3" />
                <EyeOff v-else class="w-3 h-3" />
                Fiche
              </button>

              <!-- Add / state button -->
              <button
                @click="!isAlreadyKnown(company) && confirmLead(company)"
                :disabled="addingIndex === idx || isAlreadyKnown(company)"
                class="inline-flex items-center gap-1 h-7 px-2.5 text-[11px] font-medium rounded-lg transition-all"
                :class="companyState(company, idx).cls"
              >
                <Loader2    v-if="addingIndex === idx"                       class="w-3 h-3 animate-spin" />
                <Database   v-else-if="existingSirens.has(company.siren)"    class="w-3 h-3" />
                <CheckCircle2 v-else-if="addedSirens.has(company.siren)"    class="w-3 h-3" />
                <Plus       v-else                                           class="w-3 h-3" />
                {{ companyState(company, idx).label }}
              </button>
            </div>
          </div>

          <!-- ── Expanded fiche entreprise panel ── -->
          <Transition name="slide-down">
            <div v-if="expandedIdx === idx" class="border-t border-border/60 bg-white/80 rounded-b-xl">

              <!-- Section: Identité & finances -->
              <div class="px-4 py-3 grid grid-cols-2 gap-x-6 gap-y-2">
                <div class="col-span-2 flex items-center gap-2 mb-1">
                  <Landmark class="w-3.5 h-3.5 text-tacir-blue" />
                  <span class="text-[10px] font-bold uppercase tracking-widest text-tacir-blue">Identité</span>
                </div>

                <div class="space-y-1.5">
                  <div class="flex justify-between items-center py-1 border-b border-border/40">
                    <span class="text-[11px] text-muted-foreground">SIREN</span>
                    <span class="text-[11px] font-mono font-semibold text-foreground">{{ company.siren || '—' }}</span>
                  </div>
                  <div class="flex justify-between items-center py-1 border-b border-border/40">
                    <span class="text-[11px] text-muted-foreground">SIRET</span>
                    <span class="text-[11px] font-mono font-semibold text-foreground">{{ company.siret || '—' }}</span>
                  </div>
                  <div class="flex justify-between items-center py-1 border-b border-border/40">
                    <span class="text-[11px] text-muted-foreground">Forme juridique</span>
                    <span class="text-[11px] font-semibold text-foreground">{{ company.forme_juridique || '—' }}</span>
                  </div>
                  <div class="flex justify-between items-center py-1 border-b border-border/40">
                    <span class="text-[11px] text-muted-foreground">Catégorie</span>
                    <span class="text-[11px] font-semibold text-foreground">{{ company.categorie_entreprise || '—' }}</span>
                  </div>
                  <div class="flex justify-between items-center py-1">
                    <span class="text-[11px] text-muted-foreground">Taille</span>
                    <span class="text-[11px] font-semibold text-foreground">{{ company.taille_entrep || '—' }}</span>
                  </div>
                </div>

                <div class="space-y-1.5">
                  <div class="flex justify-between items-center py-1 border-b border-border/40">
                    <span class="text-[11px] text-muted-foreground">Secteur</span>
                    <span class="text-[11px] font-semibold text-foreground text-right max-w-[140px] truncate">{{ company.secteur_activite || '—' }}</span>
                  </div>
                  <div class="flex justify-between items-center py-1 border-b border-border/40">
                    <span class="text-[11px] text-muted-foreground">Chiffre d'affaires</span>
                    <span class="text-[11px] font-semibold text-tacir-blue">{{ company.ca ? formatCA(company.ca) : '—' }}</span>
                  </div>
                  <div class="flex justify-between items-center py-1 border-b border-border/40">
                    <span class="text-[11px] text-muted-foreground">Nb locaux</span>
                    <span class="text-[11px] font-semibold text-foreground">{{ company.nb_locaux ?? '—' }}</span>
                  </div>
                  <div class="flex justify-between items-center py-1 border-b border-border/40">
                    <span class="text-[11px] text-muted-foreground">Date création</span>
                    <span class="text-[11px] font-semibold text-foreground">{{ company.date_creation_entreprise ? formatDateFR(company.date_creation_entreprise) : '—' }}</span>
                  </div>
                  <div class="flex justify-between items-center py-1">
                    <span class="text-[11px] text-muted-foreground">Pays</span>
                    <span class="text-[11px] font-semibold text-foreground">{{ company.pays || '—' }}</span>
                  </div>
                </div>
              </div>

              <!-- Section: Contact -->
              <div class="px-4 pb-3 pt-1 border-t border-border/40">
                <div class="flex items-center gap-2 mb-2">
                  <Phone class="w-3.5 h-3.5 text-emerald-600" />
                  <span class="text-[10px] font-bold uppercase tracking-widest text-emerald-600">Contact</span>
                </div>
                <div class="flex flex-wrap gap-x-6 gap-y-1">
                  <div class="flex items-center gap-1.5">
                    <MapPin class="w-3 h-3 text-muted-foreground flex-shrink-0" />
                    <span class="text-[11px] text-foreground">{{ [company.ville, company.code_postal].filter(Boolean).join(', ') || '—' }}</span>
                  </div>
                  <div v-if="company.telephone" class="flex items-center gap-1.5">
                    <Phone class="w-3 h-3 text-muted-foreground flex-shrink-0" />
                    <span class="text-[11px] font-mono text-foreground">{{ company.telephone }}</span>
                  </div>
                  <div v-if="company.adresse_email" class="flex items-center gap-1.5">
                    <Mail class="w-3 h-3 text-muted-foreground flex-shrink-0" />
                    <span class="text-[11px] text-foreground">{{ company.adresse_email }}</span>
                  </div>
                </div>
              </div>

              <!-- Section: Dirigeants -->
              <div v-if="company.dirigeants?.length" class="px-4 pb-4 pt-1 border-t border-border/40">
                <div class="flex items-center gap-2 mb-2">
                  <Users class="w-3.5 h-3.5 text-purple-600" />
                  <span class="text-[10px] font-bold uppercase tracking-widest text-purple-600">
                    Dirigeants ({{ company.dirigeants.length }})
                  </span>
                </div>
                <div class="space-y-1.5">
                  <div
                    v-for="(d, di) in company.dirigeants"
                    :key="di"
                    class="flex items-center gap-2.5 py-1.5 px-2 rounded-lg bg-purple-50/60 border border-purple-100/60"
                  >
                    <div class="w-6 h-6 rounded-full bg-purple-200 flex items-center justify-center text-[9px] font-bold text-purple-800 flex-shrink-0">
                      {{ ((d.prenoms || d.nom || '?')[0]).toUpperCase() }}
                    </div>
                    <div class="flex-1 min-w-0">
                      <p class="text-[11px] font-semibold text-foreground truncate">
                        {{ [d.prenoms, d.nom].filter(Boolean).join(' ') || '—' }}
                      </p>
                      <p class="text-[10px] text-muted-foreground">{{ d.qualite || '—' }}</p>
                    </div>
                    <span v-if="d.nationalite" class="text-[10px] text-muted-foreground flex-shrink-0">{{ d.nationalite }}</span>
                  </div>
                </div>
              </div>
            </div>
          </Transition>
        </div>
      </div>

      <!-- Footer -->
      <div class="flex-shrink-0 border-t border-border px-6 py-3 flex items-center justify-between bg-muted/20">
        <p class="text-[11px] text-muted-foreground">
          <span class="font-semibold text-foreground">{{ addedSirens.size }}</span> ajouté(s) cette session
          <span v-if="existingSirens.size > 0"> · <span class="text-purple-600 font-semibold">{{ searchResults.filter(c => existingSirens.has(c.siren)).length }}</span> déjà dans votre base</span>
        </p>
        <button
          @click="closePreviewModal"
          class="h-8 px-4 text-sm rounded-md border border-input hover:bg-accent transition-colors"
        >
          Fermer
        </button>
      </div>
    </DialogContent>
  </Dialog>

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

  <!-- Create modal -->
  <CreateLeadModal
    :open="createOpen"
    @close="createOpen = false"
    @created="handleLeadCreated"
  />

  <!-- Delete Confirm modal -->
  <LeadDeleteModal
    :open="deleteLeadTarget !== null"
    :lead="deleteLeadTarget"
    @close="deleteLeadTarget = null"
    @deleted="handleLeadDeleted"
  />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import {
  Building2, Plus, Loader2, SearchX, Search, Globe, MapPin, Users,
  CheckCircle2, Eye, EyeOff, ChevronDown, ChevronUp, Database,
  Phone, Mail, Landmark, CalendarDays, BadgeCheck,
} from 'lucide-vue-next'
import { toast } from 'vue-sonner'

import TheSidebar        from '@/components/AppSidebar.vue'
import LeadKPICards      from '@/components/leads/LeadKPICards.vue'
import LeadFiltersBar    from '@/components/leads/LeadFiltersBar.vue'
import LeadTable         from '@/components/leads/LeadTable.vue'
import LeadPagination    from '@/components/leads/LeadPagination.vue'
import LeadPreviewDrawer from '@/components/leads/LeadPreviewDrawer.vue'
import LeadEditModal     from '@/components/leads/LeadEditModal.vue'
import CreateLeadModal   from '@/components/leads/CreateLeadModal.vue'
import LeadDeleteModal   from '@/components/leads/LeadDeleteModal.vue'

import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
} from '@/components/ui/dialog'

import { useLeads }  from '@/composables/useLeads'
import { adaptLead, formatCA, formatDateFR } from '@/lib/leadAdapter'

const router = useRouter()
const BASE_URL = import.meta.env.VITE_FASTAPI_URL || 'http://localhost:8001'

const AVATAR_COLORS = [
  'bg-blue-100 text-blue-700',
  'bg-purple-100 text-purple-700',
  'bg-emerald-100 text-emerald-700',
  'bg-orange-100 text-orange-700',
  'bg-rose-100 text-rose-700',
  'bg-teal-100 text-teal-700',
]

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

// ── UI state ──────────────────────────────────────────────────
const previewLead      = ref(null)
const editLead         = ref(null)
const createOpen       = ref(false)
const deleteLeadTarget = ref(null)

// Search-preview modal state
const isSearching      = ref(false)
const showPreviewModal = ref(false)
const searchResults    = ref([])
const lastQuery        = ref('')
const addingIndex      = ref(-1)          // index of the row currently being saved
const addedSirens      = ref(new Set())   // SIRENs added to DB this session
const expandedIdx      = ref(-1)          // which company card is expanded (-1 = none)

// Cross-ref against the already-loaded lead list — survives modal reopen
const existingSirens = computed(() =>
  new Set(allLeads.value.map((l) => l.siren).filter(Boolean))
)

// True if company is already in local DB OR was added this session
function isAlreadyKnown(company) {
  return existingSirens.value.has(company.siren) ||
         addedSirens.value.has(company.siren)
}

// Returns a display label + style for a company's add-state
function companyState(company, idx) {
  if (existingSirens.value.has(company.siren)) {
    return { label: 'Déjà dans votre base', icon: 'db', cls: 'bg-purple-50 text-purple-700 border border-purple-200 cursor-default' }
  }
  if (addedSirens.value.has(company.siren)) {
    return { label: 'Ajouté', icon: 'check', cls: 'bg-emerald-50 text-emerald-700 border border-emerald-200 cursor-default' }
  }
  if (addingIndex.value === idx) {
    return { label: '…', icon: 'loading', cls: 'bg-tacir-blue text-white opacity-60 cursor-wait' }
  }
  return { label: 'Ajouter', icon: 'plus', cls: 'bg-tacir-blue text-white hover:opacity-90 shadow-sm' }
}

// Show banner only when: search present + not loading + 0 local results
const showSearchBanner = computed(() =>
  !!filters.value.search.trim() &&
  !isLoading.value &&
  filteredLeads.value.length === 0
)

// ── Event handlers ─────────────────────────────────────────────
function handleFilterUpdate(key, value) { setFilter(key, value) }
function handleToggleArray(key, value)  { toggleArrayFilter(key, value) }
function handleNavigate(lead)           { router.push(`/commercial/leads/${lead.id}`) }
function handleDelete(lead)             { deleteLeadTarget.value = lead }
function handleSave(id, updates)        { updateLead(id, updates) }

// Called when LeadDeleteModal succeeds
function handleLeadDeleted(id) {
  allLeads.value = allLeads.value.filter(l => l.id !== id)
  previewLead.value = null // Close drawer if it was open
}

// Called when CreateLeadModal succeeds — prepend new lead to list
function handleLeadCreated(adaptedLead) {
  allLeads.value.unshift(adaptedLead)
}

function closePreviewModal() {
  showPreviewModal.value = false
  // Clear only if user closed without adding anything
}

// ── Step 1 — Preview (no DB write) ────────────────────────────
async function startSearch() {
  const query = filters.value.search.trim()
  if (!query) return

  isSearching.value = true
  try {
    const res = await axios.post(`${BASE_URL}/entreprises/search_from_query/${encodeURIComponent(query)}`)

    if (res.data?.status === 'preview' && Array.isArray(res.data.results)) {
      searchResults.value    = res.data.results
      lastQuery.value        = query
      addedSirens.value      = new Set()
      addingIndex.value      = -1
      expandedIdx.value      = -1
      showPreviewModal.value = true
    } else {
      toast.warning('Aucun résultat DataGouv', {
        description: `Aucune entreprise trouvée pour "${query}".`,
      })
    }
  } catch (err) {
    console.error('[Leads] search_from_query error:', err)
    toast.error('Erreur de recherche', {
      description: err?.response?.data?.detail || 'Impossible de contacter DataGouv.',
    })
  } finally {
    isSearching.value = false
  }
}

// ── Step 2 — Confirm (DB write for chosen row) ─────────────────
async function confirmLead(company) {
  const idx = searchResults.value.indexOf(company)
  if (isAlreadyKnown(company)) return

  addingIndex.value = idx
  try {
    const res = await axios.post(`${BASE_URL}/entreprises/confirm_lead`, {
      entreprise: company,
    })

    if (res.data?.status === 'success' && res.data?.lead) {
      const raw     = res.data.lead
      const adapted = adaptLead(raw, allLeads.value.length)

      allLeads.value.unshift(adapted)
      addedSirens.value = new Set([...addedSirens.value, company.siren])

      toast.success(`Lead ajouté : ${raw.nom || company.nom}`, {
        description: [raw.ville || company.ville, raw.secteur_activite].filter(Boolean).join(' · '),
      })
    } else {
      toast.warning('Sauvegarde partielle', {
        description: res.data?.message || 'Le lead a peut-être déjà été enregistré.',
      })
    }
  } catch (err) {
    console.error('[Leads] confirm_lead error:', err)
    toast.error('Erreur lors de l\'ajout', {
      description: err?.response?.data?.detail || 'Impossible d\'enregistrer le lead.',
    })
  } finally {
    addingIndex.value = -1
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
/* Expandable fiche panel */
.slide-down-enter-active,
.slide-down-leave-active  { transition: all 0.22s ease; overflow: hidden; }
.slide-down-enter-from,
.slide-down-leave-to      { opacity: 0; max-height: 0; }
.slide-down-enter-to,
.slide-down-leave-from    { opacity: 1; max-height: 600px; }
</style>
