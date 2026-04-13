<template>
  <div class="flex min-h-screen bg-tacir-lightgray/30">

    <!-- Sidebar -->
    <TheSidebar />

    <!-- Main content -->
    <div class="flex-1 flex flex-col min-w-0">

      <!-- Sticky header -->
      <header class="h-16 border-b border-border bg-white sticky top-0 z-40 px-6 flex items-center justify-between shadow-sm">
        <div class="flex items-center gap-3">
          <div class="flex items-center gap-2">
            <BarChart3 class="w-5 h-5 text-tacir-blue" />
            <div>
              <h1 class="text-sm font-semibold text-tacir-darkblue">Tableau de bord</h1>
              <p class="text-[11px] text-tacir-darkgray hidden sm:block">
                Analyse de marché — Segmentation prospects · Pipeline commercial
              </p>
            </div>
          </div>
        </div>

        <div class="flex items-center gap-3">
          <!-- Live badge -->
          <span class="hidden sm:inline-flex items-center gap-1.5 bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px] font-semibold uppercase tracking-widest px-3 py-1 rounded-full">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            LIVE
          </span>

          <!-- Date -->
          <span class="text-xs text-muted-foreground">
            {{ todayLabel }}
          </span>

          <!-- Refresh button -->
          <button
            @click="reload"
            :disabled="isLoading"
            class="h-8 w-8 flex items-center justify-center rounded-md border border-input hover:bg-accent transition-colors disabled:opacity-50"
            title="Actualiser les données"
          >
            <RefreshCw class="w-3.5 h-3.5" :class="{ 'animate-spin': isLoading }" />
          </button>
        </div>
      </header>

      <!-- Page body -->
      <main class="flex-1 p-6 md:p-8 overflow-y-auto">
        <div class="max-w-[1400px] mx-auto space-y-6">

          <!-- ── Filters bar ─────────────────────────────────────── -->
          <div class="flex flex-wrap items-center gap-3">
            <!-- Segment filter -->
            <div class="flex items-center gap-2">
              <span class="text-xs font-semibold text-foreground">Segment</span>
              <select
                v-model="segmentFilter"
                class="h-9 px-3 text-sm rounded-md border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="all">Tous les segments</option>
                <option value="Micro">Microentreprise</option>
                <option value="PME">PME</option>
                <option value="ETI">ETI</option>
                <option value="GE">Grande Entreprise</option>
              </select>
            </div>

            <!-- Source filter -->
            <div class="flex items-center gap-2">
              <span class="text-xs font-semibold text-foreground">Source</span>
              <select
                v-model="sourceFilter"
                class="h-9 px-3 text-sm rounded-md border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="all">Toutes sources</option>
                <option value="DataGouv">DataGouv</option>
                <option value="BOAMP">BOAMP</option>
              </select>
            </div>

            <!-- Status filter -->
            <div class="flex items-center gap-2">
              <span class="text-xs font-semibold text-foreground">Statut</span>
              <select
                v-model="statusFilter"
                class="h-9 px-3 text-sm rounded-md border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="all">Tous statuts</option>
                <option value="Nouveau">Nouveau</option>
                <option value="Qualifié">Qualifié</option>
                <option value="Opportunité">Opportunité</option>
              </select>
            </div>

            <!-- Active filter chips -->
            <div v-if="hasActiveFilters" class="flex items-center gap-1.5">
              <span
                v-if="segmentFilter !== 'all'"
                class="inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full bg-tacir-blue/10 text-tacir-blue cursor-pointer hover:bg-tacir-blue/20"
                @click="segmentFilter = 'all'"
              >
                {{ segmentFilter }} <X class="w-2.5 h-2.5" />
              </span>
              <span
                v-if="sourceFilter !== 'all'"
                class="inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full bg-tacir-blue/10 text-tacir-blue cursor-pointer hover:bg-tacir-blue/20"
                @click="sourceFilter = 'all'"
              >
                {{ sourceFilter }} <X class="w-2.5 h-2.5" />
              </span>
              <span
                v-if="statusFilter !== 'all'"
                class="inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full bg-tacir-blue/10 text-tacir-blue cursor-pointer hover:bg-tacir-blue/20"
                @click="statusFilter = 'all'"
              >
                {{ statusFilter }} <X class="w-2.5 h-2.5" />
              </span>
              <button
                @click="resetFilters"
                class="text-[10px] text-muted-foreground underline hover:text-foreground transition-colors"
              >
                Réinitialiser
              </button>
            </div>

            <!-- Result count -->
            <span class="ml-auto text-xs text-muted-foreground">
              <strong class="text-foreground">{{ filteredLeads.length }}</strong> / {{ allLeads.length }} prospects
            </span>
          </div>

          <!-- ── KPI Cards ───────────────────────────────────────── -->
          <DashboardKpiCards :kpis="dashboardData.kpis" :loading="isLoading" />

          <!-- ── Segment summary cards ───────────────────────────── -->
          <DashboardSegmentCards
            :segments="dashboardData.segmentSummaries.filter(s => s.count > 0)"
            :loading="isLoading"
          />

          <!-- ── Charts row 1: Donut + CA Bar ───────────────────── -->
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <DashboardSegmentPieChart
              :distribution="dashboardData.distribution"
              :total-leads="dashboardData.kpis.totalLeads"
              :loading="isLoading"
            />
            <DashboardCaBarChart
              :segments="dashboardData.segmentSummaries"
              :loading="isLoading"
            />
          </div>

          <!-- ── Charts row 2: Complétude + Pipeline ────────────── -->
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <DashboardCompletudeBars
              :segments="dashboardData.segmentSummaries"
              :loading="isLoading"
            />
            <DashboardPipeline
              :segments="dashboardData.segmentSummaries"
              :funnel="dashboardData.funnel"
              :loading="isLoading"
            />
          </div>

          <!-- ── Empty state ─────────────────────────────────────── -->
          <Transition name="fade">
            <div
              v-if="!isLoading && allLeads.length === 0"
              class="rounded-xl border border-border bg-card p-12 flex flex-col items-center text-center"
            >
              <div class="w-14 h-14 rounded-2xl bg-muted flex items-center justify-center mb-4">
                <BarChart3 class="w-7 h-7 text-muted-foreground" />
              </div>
              <p class="text-sm font-medium text-foreground mb-1">Aucune donnée disponible</p>
              <p class="text-xs text-muted-foreground mb-4">Vérifiez que l'API est accessible et que des leads ont été importés.</p>
              <button
                @click="reload"
                class="h-9 px-4 text-sm font-medium rounded-md bg-tacir-blue text-white hover:opacity-90 transition-opacity"
              >
                Réessayer
              </button>
            </div>
          </Transition>

        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { BarChart3, RefreshCw, X } from 'lucide-vue-next'

import TheSidebar from '@/components/AppSidebar.vue'
import DashboardKpiCards       from '@/components/dashboard/DashboardKpiCards.vue'
import DashboardSegmentCards   from '@/components/dashboard/DashboardSegmentCards.vue'
import DashboardSegmentPieChart from '@/components/dashboard/DashboardSegmentPieChart.vue'
import DashboardCaBarChart     from '@/components/dashboard/DashboardCaBarChart.vue'
import DashboardCompletudeBars from '@/components/dashboard/DashboardCompletudeBars.vue'
import DashboardPipeline       from '@/components/dashboard/DashboardPipeline.vue'

import { adaptLeadResponse } from '@/lib/leadAdapter'
import { computeDashboardData } from '@/lib/dashboardData'

// ── Constants ────────────────────────────────────────────────────
const BASE_URL = import.meta.env.VITE_FASTAPI_URL || 'http://localhost:8001'

const todayLabel = new Date().toLocaleDateString('fr-FR', {
  day: 'numeric', month: 'long', year: 'numeric',
})

// ── Data state ───────────────────────────────────────────────────
const allLeads = ref([])
const isLoading = ref(false)

async function fetchLeads() {
  isLoading.value = true
  try {
    const res = await axios.get(`${BASE_URL}/entreprises/`, {
      params: { skip: 0, limit: 2000 },
    })
    const raw = Array.isArray(res.data) ? res.data : (res.data?.data ?? [])
    allLeads.value = adaptLeadResponse(raw)
  } catch (err) {
    console.error('[Dashboard] Fetch error:', err)
  } finally {
    isLoading.value = false
  }
}

function reload() { fetchLeads() }

onMounted(fetchLeads)

// ── Filter state ─────────────────────────────────────────────────
const segmentFilter = ref('all')
const sourceFilter  = ref('all')
const statusFilter  = ref('all')

const hasActiveFilters = computed(() =>
  segmentFilter.value !== 'all' ||
  sourceFilter.value  !== 'all' ||
  statusFilter.value  !== 'all'
)

function resetFilters() {
  segmentFilter.value = 'all'
  sourceFilter.value  = 'all'
  statusFilter.value  = 'all'
}

// ── Derived: filteredLeads ───────────────────────────────────────
const filteredLeads = computed(() => {
  let result = allLeads.value

  if (segmentFilter.value !== 'all') {
    result = result.filter((l) => l.segment === segmentFilter.value)
  }

  if (sourceFilter.value === 'BOAMP') {
    result = result.filter((l) => l.hasBoamp)
  } else if (sourceFilter.value === 'DataGouv') {
    result = result.filter((l) => !l.hasBoamp)
  }

  if (statusFilter.value !== 'all') {
    result = result.filter((l) => l.status === statusFilter.value)
  }

  return result
})

// ── Dashboard analytics ──────────────────────────────────────────
// Computed lazily from filteredLeads — auto-updates on filter change
const dashboardData = computed(() => {
  // Return safe empty structure during initial load
  if (isLoading.value && !filteredLeads.value.length) {
    return {
      kpis:            { totalLeads: 0, averageRevenue: '—', averageCompleteness: 0, averageAge: 0 },
      segmentSummaries:[],
      distribution:   [],
      funnel:          [],
    }
  }
  return computeDashboardData(filteredLeads.value)
})
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.25s ease; }
.fade-enter-from, .fade-leave-to       { opacity: 0; }
</style>
