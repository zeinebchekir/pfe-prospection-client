<template>
  <div class="flex min-h-screen bg-tacir-lightgray/30">

    <!-- Sidebar -->
    <TheSidebar />

    <!-- Right content column -->
    <div class="flex-1 flex flex-col min-w-0">

      <!-- ── Sticky top bar ── -->
      <header class="border-b border-border bg-white sticky top-0 z-40 px-4 sm:px-6 shadow-sm">
        <div class="flex items-center justify-between h-16 gap-3 flex-wrap sm:flex-nowrap">
          <div class="min-w-0">
            <h2 class="text-sm font-semibold text-tacir-darkblue truncate">
              Segmentation &amp; Analyse de marché
            </h2>
            <p class="text-[11px] text-tacir-darkgray hidden sm:block">{{ today }}</p>
          </div>
          <div class="flex items-center gap-2 flex-shrink-0">
            <!-- Silhouette score badge -->
            <span
              v-if="summary?.validation?.silhouette"
              class="hidden md:inline-flex items-center gap-1.5 text-[11px] font-medium px-2.5 py-1 rounded-full border"
              :class="silhouetteBadgeClass"
              :title="summary.validation.silhouette_interpretation"
            >
              <span class="font-mono font-bold">S={{ summary.validation.silhouette }}</span>
              <span class="opacity-70">silhouette</span>
            </span>
            <span
              v-if="summary"
              class="hidden sm:inline-flex items-center gap-1.5 text-[11px] font-medium px-2.5 py-1 rounded-full bg-green-50 text-green-700 border border-green-200"
            >
              <CheckCircle2 class="w-3 h-3" /> Données à jour
            </span>
            <button
              id="btn-run-clustering"
              @click="handleRun"
              :disabled="running"
              class="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 bg-tacir-blue text-white rounded-lg hover:bg-tacir-darkblue transition-colors disabled:opacity-60 whitespace-nowrap"
            >
              <RefreshCw class="w-3.5 h-3.5" :class="running ? 'animate-spin' : ''" />
              <span class="hidden sm:inline">{{ running ? "Analyse en cours…" : "Relancer l'analyse" }}</span>
              <span class="sm:hidden">{{ running ? "…" : "Lancer" }}</span>
            </button>
          </div>
        </div>
      </header>

      <!-- ── Scrollable body ── -->
      <main class="flex-1 p-4 sm:p-6 overflow-y-auto">

        <!-- Error banner -->
        <div
          v-if="error"
          class="mb-4 flex items-start gap-2 bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg px-4 py-3"
        >
          <AlertTriangle class="w-4 h-4 shrink-0 mt-0.5" />
          <span class="flex-1">{{ error }}</span>
          <button @click="loadData" class="underline font-medium whitespace-nowrap">Réessayer</button>
        </div>

        <!-- ── Loading skeleton ── -->
        <div v-if="loading" class="space-y-4">
          <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div v-for="i in 6" :key="i" class="h-20 bg-gray-200 rounded-xl animate-pulse" />
          </div>
          <div class="h-48 bg-gray-200 rounded-xl animate-pulse" />
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <div v-for="i in 3" :key="i" class="h-40 bg-gray-200 rounded-xl animate-pulse" />
          </div>
        </div>

        <!-- ── Main content ── -->
        <template v-else-if="summary">
          <div class="space-y-5 sm:space-y-6">

            <!-- KPI Cards -->
            <MarketKPICards :segments="summary.segments" :total-leads="summary.total_leads" />

            <!-- Bubble chart — legend + chart -->
            <div class="bg-white border border-border rounded-xl p-4 sm:p-5 shadow-sm">
              <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 mb-4">
                <div>
                  <h2 class="font-semibold text-tacir-darkblue text-sm">Vue synthétique des segments</h2>
                  <p class="text-xs text-tacir-darkgray">Taille des bulles = volume de leads</p>
                </div>
                <div class="flex flex-wrap gap-x-3 gap-y-1.5">
                  <div v-for="s in summary.segments" :key="s.cluster" class="flex items-center gap-1.5 text-[11px]">
                    <span class="w-2 h-2 rounded-full flex-shrink-0" :style="{ backgroundColor: s.color }" />
                    <span class="text-tacir-darkgray font-medium">{{ s.label_short || s.label }}</span>
                    <span v-if="s.label_sub" class="text-tacir-darkgray/60 text-[10px]">· {{ s.label_sub }}</span>
                  </div>
                </div>
              </div>
              <SegmentBubbleChart :segments="summary.segments" :total-leads="summary.total_leads" />
            </div>

            <!-- Segment profile cards — 1 col mobile, 2 tablet, 3 desktop -->
            <div>
              <div class="mb-3">
                <h2 class="font-semibold text-tacir-darkblue text-sm">Profils des segments</h2>
                <p class="text-xs text-tacir-darkgray">Caractéristiques métier et recommandations stratégiques</p>
              </div>
              <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
                <SegmentCard
                  v-for="s in summary.segments"
                  :key="s.cluster"
                  :segment="s"
                  :total-leads="summary.total_leads"
                />
              </div>
            </div>

            <!-- Comparison bar charts — stack on mobile, side by side desktop -->
            <SegmentComparisonCharts :segments="summary.segments" />

            <!-- Radar + Opportunity matrix — stack on mobile, side by side desktop -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-5">
              <SegmentRadarChart :segments="summary.segments" />
              <OpportunityMatrix :segments="summary.segments" />
            </div>

            <!-- Strategic insights (dynamic, from Gemini or fallback) -->
            <InsightsPanel
              :insights="summary.insights || []"
              :source="summary.insights_source || ''"
            />

            <!-- Leads explorer with full pagination -->
            <LeadsExplorerTable :segments="summary.segments" />

          </div>
        </template>

        <!-- ── Empty state ── -->
        <div v-else class="flex flex-col items-center justify-center py-16 sm:py-24 text-center gap-4">
          <div class="w-16 h-16 rounded-2xl bg-tacir-lightgray flex items-center justify-center">
            <BarChart3 class="w-8 h-8 text-tacir-darkgray/50" />
          </div>
          <div>
            <p class="text-tacir-darkblue font-semibold mb-1">Aucune analyse disponible</p>
            <p class="text-xs text-tacir-darkgray max-w-xs">
              Cliquez sur "Relancer l'analyse" pour exécuter le clustering K-Means sur les données actuelles.
            </p>
          </div>
          <button
            @click="handleRun"
            :disabled="running"
            class="inline-flex items-center gap-2 text-sm px-4 py-2 bg-tacir-blue text-white rounded-lg hover:bg-tacir-darkblue transition-colors disabled:opacity-60"
          >
            <RefreshCw class="w-4 h-4" :class="running ? 'animate-spin' : ''" />
            {{ running ? "Analyse en cours…" : "Lancer l'analyse" }}
          </button>
        </div>

      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import { CheckCircle2, RefreshCw, AlertTriangle, BarChart3 } from "lucide-vue-next";

import TheSidebar              from "@/components/AppSidebar.vue";
import { getSummary, runClustering } from "@/services/segmentation.js";
import MarketKPICards           from "@/components/market/MarketKPICards.vue";
import SegmentBubbleChart       from "@/components/market/SegmentBubbleChart.vue";
import SegmentCard              from "@/components/market/SegmentCard.vue";
import SegmentComparisonCharts  from "@/components/market/SegmentComparisonCharts.vue";
import SegmentRadarChart        from "@/components/market/SegmentRadarChart.vue";
import OpportunityMatrix        from "@/components/market/OpportunityMatrix.vue";
import InsightsPanel            from "@/components/market/InsightsPanel.vue";
import LeadsExplorerTable       from "@/components/market/LeadsExplorerTable.vue";

const summary = ref(null);
const loading = ref(false);
const running = ref(false);
const error   = ref(null);

const today = new Date().toLocaleDateString("fr-FR", {
  weekday: "long", day: "numeric", month: "long",
});

async function loadData() {
  loading.value = true;
  error.value   = null;
  try {
    const res     = await getSummary();
    summary.value = res.data;
  } catch (e) {
    if (e.response?.status === 404) {
      summary.value = null;
    } else {
      error.value = "Impossible de charger les données. Vérifiez que le service ETL est actif (port 8001).";
    }
  } finally {
    loading.value = false;
  }
}

// Silhouette badge colour
const silhouetteBadgeClass = computed(() => {
  const s = summary.value?.validation?.silhouette ?? 0;
  if (s >= 0.5) return 'bg-green-50 text-green-700 border-green-200';
  if (s >= 0.3) return 'bg-amber-50 text-amber-700 border-amber-200';
  return 'bg-red-50 text-red-600 border-red-200';
});

async function handleRun() {
  running.value = true;
  error.value   = null;
  try {
    const res     = await runClustering();
    // Full summary is now returned by /run endpoint
    summary.value = res.data;
  } catch (e) {
    error.value = e.response?.data?.detail || "Erreur lors de l'analyse. Vérifiez les logs FastAPI.";
  } finally {
    running.value = false;
  }
}

onMounted(loadData);
</script>
