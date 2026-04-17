<template>
  <div class="min-h-screen bg-tacir-lightgray/40">
    <!-- Sticky header -->
    <header class="sticky top-0 z-30 bg-white/90 backdrop-blur-md border-b border-border shadow-sm">
      <div class="max-w-[1400px] mx-auto px-6 py-4 flex items-center justify-between gap-4 flex-wrap">
        <div class="flex items-center gap-4">
          <RouterLink to="/manager">
            <button class="h-8 w-8 flex items-center justify-center rounded-lg text-tacir-darkgray hover:bg-tacir-lightgray transition-colors">
              <ArrowLeft class="w-4 h-4" />
            </button>
          </RouterLink>
          <div>
            <h1 class="text-xl font-bold text-tacir-darkblue tracking-tight">
              Analyse de marché &amp; segmentation
            </h1>
            <p class="text-xs text-tacir-darkgray">Vue exécutive — clustering KMeans K=5 sur les leads</p>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <div class="flex items-center gap-1.5 text-xs text-tacir-darkgray">
            <Calendar class="w-3.5 h-3.5" />
            <span>{{ today }}</span>
          </div>
          <span
            v-if="summary"
            class="inline-flex items-center gap-1.5 text-[11px] font-medium px-2.5 py-1 rounded-full bg-green-50 text-green-700 border border-green-200"
          >
            <CheckCircle2 class="w-3 h-3" /> Données à jour
          </span>
          <button
            @click="handleRun"
            :disabled="running"
            class="inline-flex items-center gap-2 text-xs px-3 py-1.5 bg-tacir-blue text-white rounded-lg hover:bg-tacir-darkblue transition-colors disabled:opacity-60"
          >
            <RefreshCw class="w-3.5 h-3.5" :class="running ? 'animate-spin' : ''" />
            {{ running ? "Analyse en cours…" : "Relancer l'analyse" }}
          </button>
        </div>
      </div>
    </header>

    <!-- Error banner -->
    <div v-if="error" class="max-w-[1400px] mx-auto px-6 pt-4">
      <div class="flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg px-4 py-3">
        <AlertTriangle class="w-4 h-4 shrink-0" />
        {{ error }}
        <button @click="loadData" class="ml-auto underline font-medium">Réessayer</button>
      </div>
    </div>

    <main class="max-w-[1400px] mx-auto px-6 py-6 space-y-6">

      <!-- Loading skeleton -->
      <div v-if="loading" class="space-y-4">
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          <div v-for="i in 6" :key="i" class="h-20 bg-gray-200 rounded-xl animate-pulse" />
        </div>
        <div class="h-64 bg-gray-200 rounded-xl animate-pulse" />
      </div>

      <template v-else-if="summary">
        <!-- KPI Cards -->
        <section>
          <MarketKPICards :segments="summary.segments" :total-leads="summary.total_leads" />
        </section>

        <!-- Bubble chart -->
        <section>
          <div class="bg-white border border-border rounded-xl p-5 shadow-sm">
            <div class="mb-4 flex items-start justify-between flex-wrap gap-2">
              <div>
                <h2 class="font-semibold text-tacir-darkblue text-sm">Vue synthétique des segments</h2>
                <p class="text-xs text-tacir-darkgray">Taille des bulles = volume de leads · couleur = segment</p>
              </div>
              <div class="flex flex-wrap gap-2">
                <div v-for="s in summary.segments" :key="s.cluster" class="flex items-center gap-1.5 text-[11px]">
                  <span class="w-2.5 h-2.5 rounded-full" :style="{ backgroundColor: s.color }" />
                  <span class="text-tacir-darkgray">{{ s.label.split(" ").slice(0,2).join(" ") }}</span>
                </div>
              </div>
            </div>
            <SegmentBubbleChart :segments="summary.segments" :total-leads="summary.total_leads" />
          </div>
        </section>

        <!-- Segment cards -->
        <section>
          <div class="mb-3">
            <h2 class="font-semibold text-tacir-darkblue text-sm">Profils des segments</h2>
            <p class="text-xs text-tacir-darkgray">Caractéristiques métier et recommandations</p>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <SegmentCard
              v-for="s in summary.segments"
              :key="s.cluster"
              :segment="s"
              :total-leads="summary.total_leads"
            />
          </div>
        </section>

        <!-- Comparison charts -->
        <section>
          <SegmentComparisonCharts :segments="summary.segments" />
        </section>

        <!-- Radar + Matrix -->
        <section class="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <SegmentRadarChart :segments="summary.segments" />
          <OpportunityMatrix :segments="summary.segments" />
        </section>

        <!-- Insights -->
        <section>
          <InsightsPanel />
        </section>

        <!-- Leads Explorer -->
        <section>
          <LeadsExplorerTable :segments="summary.segments" />
        </section>
      </template>

      <!-- Empty state — never run -->
      <div v-else class="flex flex-col items-center justify-center py-24 text-center gap-4">
        <BarChart3 class="w-12 h-12 text-tacir-darkgray/40" />
        <p class="text-tacir-darkblue font-semibold">Aucune analyse disponible</p>
        <p class="text-xs text-tacir-darkgray max-w-xs">Cliquez sur "Relancer l'analyse" pour exécuter le clustering sur les données actuelles.</p>
      </div>

    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { RouterLink } from "vue-router";
import {
  ArrowLeft, Calendar, CheckCircle2, RefreshCw, AlertTriangle, BarChart3,
} from "lucide-vue-next";

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

const today = new Date().toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" });

async function loadData() {
  loading.value = true;
  error.value   = null;
  try {
    const res    = await getSummary();
    summary.value = res.data;
  } catch (e) {
    if (e.response?.status === 404) {
      summary.value = null; // Not yet run — show empty state
    } else {
      error.value = "Impossible de charger les données de segmentation. Vérifiez que le service ETL est actif.";
    }
  } finally {
    loading.value = false;
  }
}

async function handleRun() {
  running.value = true;
  error.value   = null;
  try {
    const res     = await runClustering();
    summary.value = { total_leads: res.data.total_rows, segments: res.data.segments, run_at: res.data.run_at };
  } catch (e) {
    error.value = e.response?.data?.detail || "Erreur lors de l'analyse. Vérifiez les logs FastAPI.";
  } finally {
    running.value = false;
  }
}

onMounted(loadData);
</script>
