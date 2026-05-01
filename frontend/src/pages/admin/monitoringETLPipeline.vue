<template>
  <div class="flex min-h-screen bg-tacir-lightgray/30">
    <TheSidebar />

    <div class="flex-1 flex flex-col min-w-0">

      <!-- ── STICKY HEADER ── -->
      <header class="h-16 border-b border-border bg-white sticky top-0 z-40 px-6 flex items-center justify-between shadow-sm">
        <div class="flex items-center gap-3">
          <div class="md:hidden w-10" />
          <div>
            <h2 class="text-sm font-semibold text-tacir-darkblue">Monitoring ETL Pipeline</h2>
            <p class="text-[11px] text-tacir-darkgray">Supervision des pipelines de données · Temps réel</p>
          </div>
        </div>

        <div class="flex items-center gap-3">
          <!-- <Button @click="router.push('/admin/reports')" variant="outline" size="sm" class="hidden sm:flex items-center gap-2 border-border/60 text-tacir-darkblue bg-tacir-lightgray/20 hover:bg-tacir-lightgray/50">
            <Database class="w-3.5 h-3.5 text-tacir-darkgray" />
            <span class="text-xs font-semibold">Reports List</span>
          </Button> -->

          <Button @click="router.push('/admin/etllogs')" variant="outline" size="sm" class="hidden sm:flex items-center gap-2 border-border/60 text-tacir-darkblue bg-tacir-lightgray/20 hover:bg-tacir-lightgray/50">
            <FileText class="w-3.5 h-3.5 text-tacir-darkgray" />
            <span class="text-xs font-semibold">Logs ETL</span>
          </Button>

          <div class="hidden sm:flex items-center gap-2 bg-tacir-lightgray/50 border border-border/60 rounded-lg px-3 py-1.5">
            <Clock class="w-3.5 h-3.5 text-tacir-darkgray" />
            <span class="font-mono text-xs font-bold text-tacir-darkblue tabular-nums">{{ liveClock }}</span>
            <span class="w-1.5 h-1.5 rounded-full bg-tacir-lightblue animate-pulse"></span>
          </div>
          <span class="hidden sm:inline-flex items-center gap-1.5 bg-tacir-blue/8 text-tacir-blue border border-tacir-blue/15 text-[10px] font-semibold uppercase tracking-widest px-3 py-1 rounded-full">
            <span class="w-1.5 h-1.5 rounded-full bg-tacir-lightblue animate-pulse" />
            ADMIN
          </span>
        </div>
      </header>

      <!-- ── MAIN CONTENT ── -->
      <main class="p-4 md:p-6 space-y-6 overflow-y-auto">

        <!-- ── GLOBAL KPIs ── -->
        <div class="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 gap-3">

          <!-- Total runs aujourd'hui -->
          <Card class="border-border shadow-sm rounded-2xl bg-white overflow-hidden">
            <CardContent class="p-4">
              <div class="flex items-start justify-between mb-3">
                <div class="w-8 h-8 rounded-xl bg-tacir-blue/10 flex items-center justify-center">
                  <RefreshCw class="w-4 h-4 text-tacir-blue" />
                </div>
                <span class="text-[9px] uppercase tracking-widest font-bold text-tacir-darkgray">Aujourd'hui</span>
              </div>
              <p class="text-2xl font-black text-tacir-darkblue tabular-nums">{{ kpis.totalRuns }}</p>
              <p class="text-[10px] text-tacir-darkgray font-semibold mt-0.5">Runs exécutés</p>
              <div class="mt-2 flex items-center gap-1">
                <span class="text-[9px] font-bold text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded-full">
                  ↑ {{ kpis.runsVsYesterday }}% vs hier
                </span>
              </div>
            </CardContent>
          </Card>

          <!-- Taux de succès -->
          <Card class="border-border shadow-sm rounded-2xl bg-white overflow-hidden">
            <CardContent class="p-4">
              <div class="flex items-start justify-between mb-3">
                <div class="w-8 h-8 rounded-xl bg-emerald-50 flex items-center justify-center">
                  <CheckCircle2 class="w-4 h-4 text-emerald-600" />
                </div>
                <span class="text-[9px] uppercase tracking-widest font-bold text-tacir-darkgray">Global</span>
              </div>
              <p class="text-2xl font-black tabular-nums" :class="kpis.successRate >= 80 ? 'text-emerald-600' : 'text-amber-600'">
                {{ kpis.successRate }}%
              </p>
              <p class="text-[10px] text-tacir-darkgray font-semibold mt-0.5">Taux de succès</p>
              <div class="mt-2 w-full h-1.5 bg-tacir-lightgray rounded-full overflow-hidden">
                <div class="h-full rounded-full bg-emerald-500 transition-all duration-700" :style="{ width: kpis.successRate + '%' }"></div>
              </div>
            </CardContent>
          </Card>

          <!-- Lignes insérées -->
          <Card class="border-border shadow-sm rounded-2xl bg-white overflow-hidden">
            <CardContent class="p-4">
              <div class="flex items-start justify-between mb-3">
                <div class="w-8 h-8 rounded-xl bg-tacir-lightblue/10 flex items-center justify-center">
                  <Database class="w-4 h-4 text-tacir-lightblue" />
                </div>
                <span class="text-[9px] uppercase tracking-widest font-bold text-tacir-darkgray">Aujourd'hui</span>
              </div>
              <p class="text-2xl font-black text-tacir-darkblue tabular-nums">{{ kpis.rowsInserted.toLocaleString('fr-FR') }}</p>
              <p class="text-[10px] text-tacir-darkgray font-semibold mt-0.5">Lignes insérées</p>
              <div class="mt-2 flex items-center gap-1">
                <span class="text-[9px] font-bold text-tacir-lightblue bg-tacir-blue/8 px-1.5 py-0.5 rounded-full">
                  raw + clean
                </span>
              </div>
            </CardContent>
          </Card>

          <!-- Lignes mises à jour -->
          <Card class="border-border shadow-sm rounded-2xl bg-white overflow-hidden">
            <CardContent class="p-4">
              <div class="flex items-start justify-between mb-3">
                <div class="w-8 h-8 rounded-xl bg-amber-50 flex items-center justify-center">
                  <ArrowUpDown class="w-4 h-4 text-amber-600" />
                </div>
                <span class="text-[9px] uppercase tracking-widest font-bold text-tacir-darkgray">Aujourd'hui</span>
              </div>
              <p class="text-2xl font-black text-tacir-darkblue tabular-nums">{{ kpis.rowsUpdated.toLocaleString('fr-FR') }}</p>
              <p class="text-[10px] text-tacir-darkgray font-semibold mt-0.5">Lignes mises à jour</p>
              <div class="mt-2 flex items-center gap-1">
                <span class="text-[9px] font-bold text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded-full">
                  upserts
                </span>
              </div>
            </CardContent>
          </Card>

          <!-- Erreurs aujourd'hui -->
          <Card class="border-border shadow-sm rounded-2xl bg-white overflow-hidden">
            <CardContent class="p-4">
              <div class="flex items-start justify-between mb-3">
                <div class="w-8 h-8 rounded-xl flex items-center justify-center" :class="kpis.errorsToday > 0 ? 'bg-red-50' : 'bg-emerald-50'">
                  <XCircle class="w-4 h-4" :class="kpis.errorsToday > 0 ? 'text-red-500' : 'text-emerald-500'" />
                </div>
                <span class="text-[9px] uppercase tracking-widest font-bold text-tacir-darkgray">Aujourd'hui</span>
              </div>
              <p class="text-2xl font-black tabular-nums" :class="kpis.errorsToday > 0 ? 'text-red-600' : 'text-emerald-600'">
                {{ kpis.errorsToday }}
              </p>
              <p class="text-[10px] text-tacir-darkgray font-semibold mt-0.5">Erreurs pipeline</p>
              <div class="mt-2 flex items-center gap-1">
                <span
                  class="text-[9px] font-bold px-1.5 py-0.5 rounded-full"
                  :class="kpis.errorsToday > 0 ? 'text-red-600 bg-red-50' : 'text-emerald-600 bg-emerald-50'"
                >
                  {{ kpis.errorsToday > 0 ? kpis.errorsToday + ' phase(s) en échec' : 'Aucune erreur' }}
                </span>
              </div>
            </CardContent>
          </Card>

          <!-- Durée moyenne -->
          <Card class="border-border shadow-sm rounded-2xl bg-white overflow-hidden">
            <CardContent class="p-4">
              <div class="flex items-start justify-between mb-3">
                <div class="w-8 h-8 rounded-xl bg-tacir-lightgray flex items-center justify-center">
                  <Timer class="w-4 h-4 text-tacir-darkgray" />
                </div>
                <span class="text-[9px] uppercase tracking-widest font-bold text-tacir-darkgray">Moyenne</span>
              </div>
              <p class="text-2xl font-black text-tacir-darkblue tabular-nums">{{ kpis.avgDuration }}</p>
              <p class="text-[10px] text-tacir-darkgray font-semibold mt-0.5">Durée / pipeline</p>
              <div class="mt-2 flex items-center gap-1">
                <span class="text-[9px] font-bold text-tacir-darkgray bg-tacir-lightgray px-1.5 py-0.5 rounded-full">
                  sur {{ kpis.totalRuns }} runs
                </span>
              </div>
            </CardContent>
          </Card>

        </div>

        <!-- ── ANALYTICS DASHBOARD ── -->
        <div class="space-y-4 pt-4">
          <h3 class="text-xs font-black text-tacir-darkblue uppercase tracking-widest flex items-center gap-2">
            <svg class="w-4 h-4 text-tacir-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>
            Analytique Décisionnelle
          </h3>
           <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 pb-2">
               <ChartStatusByDag class="lg:col-span-1" />
               <ChartBoampQuality class="lg:col-span-1" />
               <ChartQualityCompleteness class="lg:col-span-1" />
           </div>
           <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 pb-2 mt-4">
               <ChartVolumeTrends class="lg:col-span-1" />
               <ChartDurationBottlenecks class="lg:col-span-1" />
           </div>
        </div>
        

        <div class="h-px bg-border/60 w-full my-6"></div>

        <!-- ── SIDE BY SIDE PIPELINES GRID ── -->
        <h3 class="text-xs font-black text-tacir-darkblue uppercase tracking-widest flex items-center gap-2 mb-4">
          <Terminal class="w-4 h-4 text-tacir-blue" />
          Temps Réel & Contrôle
        </h3>
        <div class="grid grid-cols-1 xl:grid-cols-2 gap-6 items-start">

          <div
            v-for="pid in pipelineIds"
            :key="pid"
            class="flex flex-col gap-4"
          >
            <!-- Pipeline header label -->
            <div class="flex items-center justify-between cursor-pointer group" @click="togglePipeline(pid)">
              <div class="flex items-center gap-2">
                <span class="text-base">{{ pid === 'sync_boamp' ? '📄' : '🇫🇷' }}</span>
                <h3 class="text-sm font-black text-tacir-darkblue tracking-tight">{{ pid }}</h3>
                <Badge :class="pipelineStatusBadgeClass(pipelines[pid].status)" class="ml-1">
                  <component :is="pipelineStatusIcon(pipelines[pid].status)" class="w-2.5 h-2.5 mr-1" :class="pipelines[pid].status === 'run' ? 'animate-spin' : ''" />
                  {{ pipelineStatusLabel(pipelines[pid].status) }}
                </Badge>
              </div>
              <Button variant="ghost" size="sm" class="h-8 w-8 p-0 text-tacir-darkgray group-hover:bg-tacir-lightgray/50 rounded-full transition-colors" @click.stop="togglePipeline(pid)">
                <ChevronDown class="w-4 h-4 transition-transform duration-300" :class="{ 'rotate-180': expandedPipelines.has(pid) }" />
              </Button>
            </div>

            <!-- ── RUN CONTROL CARD ── -->
            <Card class="border-border shadow-sm rounded-2xl bg-white overflow-hidden">
              <CardContent class="p-4 space-y-4">

                <!-- Run metadata -->
                <div class="grid grid-cols-2 gap-3">
                  <div>
                    <p class="text-[9px] uppercase tracking-widest text-tacir-darkgray font-semibold mb-0.5">Run ID</p>
                    <span class="font-mono text-[11px] font-bold text-tacir-darkblue truncate block">{{ pipelines[pid].runId }}</span>
                  </div>
                  <div class="grid grid-cols-2 gap-2">
                    <div>
                      <p class="text-[9px] uppercase tracking-widest text-tacir-darkgray font-semibold mb-0.5">Début</p>
                      <span class="font-mono text-[11px] font-bold text-tacir-darkblue">{{ pipelines[pid].start }}</span>
                    </div>
                    <div>
                      <p class="text-[9px] uppercase tracking-widest text-tacir-darkgray font-semibold mb-0.5">Fin</p>
                      <span class="font-mono text-[11px] font-bold text-tacir-darkblue">{{ pipelines[pid].end || '—' }}</span>
                    </div>
                  </div>
                </div>

                <!-- Progress bar -->
                <div>
                  <div class="flex justify-between items-center mb-1">
                    <span class="text-[9px] uppercase tracking-wider font-semibold text-tacir-darkgray">
                      Complétion · {{ pipelines[pid].phases.filter(p => p.st === 'ok').length }}/{{ pipelines[pid].phases.length }} phases
                    </span>
                    <span
                      class="text-xs font-black tabular-nums"
                      :class="pipelines[pid].status === 'err' ? 'text-red-600' : pipelines[pid].status === 'run' ? 'text-tacir-blue' : 'text-tacir-lightblue'"
                    >{{ pipelines[pid].progress }}%</span>
                  </div>
                  <div class="w-full h-2 bg-tacir-lightgray rounded-full overflow-hidden">
                    <div
                      class="h-full rounded-full transition-all duration-700"
                      :class="pipelines[pid].status === 'err' ? 'bg-red-500' : pipelines[pid].status === 'run' ? 'bg-tacir-blue' : 'bg-tacir-lightblue'"
                      :style="{ width: pipelines[pid].progress + '%' }"
                    ></div>
                  </div>
                </div>

                

              </CardContent>
            </Card>

            <!-- ── PHASE CARDS ── -->
            <!-- <Transition
              enter-active-class="transition-all duration-500 ease-in-out origin-top"
              enter-from-class="grid-rows-[0fr] opacity-0"
              enter-to-class="grid-rows-[1fr] opacity-100"
              leave-active-class="transition-all duration-300 ease-in-out origin-top"
              leave-from-class="grid-rows-[1fr] opacity-100"
              leave-to-class="grid-rows-[0fr] opacity-0"
            > -->
              <!-- <div v-show="expandedPipelines.has(pid)" class="grid">
                <div class="space-y-0 min-h-0">
                  <template v-for="(phase, idx) in pipelines[pid].phases" :key="phase.name">

                <Card
                  class="border-border shadow-sm rounded-2xl bg-white overflow-hidden"
                  :class="phaseBorderClass(phase.st)"
                >
                  <CardContent class="p-4">

                    Phase header -->
                    <!-- <div class="flex items-start gap-2.5 mb-3">
                      <div
                        class="w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-black flex-shrink-0 mt-0.5"
                        :class="phaseCircleClass(phase.st)"
                      >{{ phase.num }}</div>
                      <div class="flex-1 min-w-0">
                        <div class="flex flex-wrap items-center gap-1.5">
                          <span class="font-mono font-bold text-tacir-darkblue text-xs">{{ phase.name }}</span>
                          <Badge :class="phaseStatusBadgeClass(phase.st)" class="rounded-lg font-black uppercase text-[9px] tracking-widest px-1.5 py-0">
                            <component :is="phaseStatusIcon(phase.st)" class="w-2 h-2 mr-1" :class="phase.st === 'run' ? 'animate-spin' : ''" />
                            {{ phaseStatusLabel(phase.st) }}
                          </Badge>
                        </div>
                        <p class="text-[10px] text-tacir-darkgray mt-0.5 leading-tight">{{ phase.sub }}</p>
                      </div>
                    </div> -->

                    <!-- Metadata row -->
                    <!-- <div class="grid grid-cols-4 gap-1.5 mb-3">
                      <div class="bg-tacir-lightgray/40 rounded-lg p-2 border border-border/30">
                        <p class="text-[8px] uppercase tracking-wider text-tacir-darkgray font-semibold mb-0.5">Durée</p>
                        <p class="font-mono text-[10px] font-bold text-tacir-darkblue">{{ phase.st === 'idle' ? '—' : phase.dur }}</p>
                      </div>
                      <div class="bg-tacir-lightgray/40 rounded-lg p-2 border border-border/30">
                        <p class="text-[8px] uppercase tracking-wider text-tacir-darkgray font-semibold mb-0.5">Entrées</p>
                        <p class="font-mono text-[10px] font-bold text-tacir-darkblue truncate">{{ phase.st === 'idle' ? '—' : phase.inp }}</p>
                      </div>
                      <div class="col-span-2 bg-tacir-lightgray/40 rounded-lg p-2 border border-border/30">
                        <p class="text-[8px] uppercase tracking-wider text-tacir-darkgray font-semibold mb-0.5">Sorties</p>
                        <p class="font-mono text-[10px] font-bold text-tacir-darkblue truncate">{{ phase.st === 'idle' ? '—' : phase.out }}</p>
                      </div>
                    </div> -->

                    <!-- Resource bars -->
                    <!-- <div class="grid grid-cols-3 gap-2 mb-3">
                      <div v-for="(res, key) in { CPU: phase.cpu, RAM: phase.ram, 'I/O': phase.disk }" :key="key">
                        <div class="flex justify-between items-center mb-0.5">
                          <span class="text-[9px] font-semibold text-tacir-darkgray">{{ key }}</span>
                          <span class="text-[9px] font-black font-mono" :class="resourceTextClass(res, phase.st)">
                            {{ phase.st === 'idle' ? '—' : res + '%' }}
                          </span>
                        </div>
                        <div class="w-full h-1.5 bg-tacir-lightgray rounded-full overflow-hidden">
                          <div
                            class="h-full rounded-full transition-all duration-500"
                            :class="resourceBarClass(res, phase.st)"
                            :style="{ width: phase.st === 'idle' ? '0%' : res + '%' }"
                          ></div>
                        </div>
                      </div>
                    </div> -->

                    <!-- Taux de complétude (load phases only) -->
                    <!-- <div v-if="isLoadPhase(phase.name) && phase.st === 'ok'" class="mb-3">
                      <div class="flex justify-between items-center mb-0.5">
                        <span class="text-[9px] uppercase tracking-wider font-semibold text-tacir-darkgray">Taux de complétude</span>
                        <span class="text-[10px] font-black text-tacir-lightblue">{{ completionRate(phase) }}%</span>
                      </div>
                      <div class="w-full h-1.5 bg-tacir-lightgray rounded-full overflow-hidden">
                        <div class="h-full rounded-full bg-tacir-lightblue transition-all duration-700" :style="{ width: completionRate(phase) + '%' }"></div>
                      </div>
                    </div> -->

                    <!-- Error box -->
                    <!-- <div v-if="phase.err && phase.st === 'err'" class="bg-red-50 border border-red-200 rounded-xl p-3 font-mono text-[10px] text-red-800 mb-3">
                      <div class="flex items-center gap-1.5 mb-1.5 font-sans">
                        <AlertTriangle class="w-3 h-3 text-red-500" />
                        <span class="text-[9px] uppercase tracking-wider font-black text-red-600">Erreur d'exécution</span>
                      </div>
                      <pre class="whitespace-pre-wrap break-all text-[9px] leading-relaxed">{{ phase.err }}</pre>
                    </div> -->

                    <!-- Log toggle -->
                    <!-- <div class="h-px bg-border mb-2" />
                    <button
                      @click="toggleLog(pid, phase.name)"
                      class="flex items-center gap-1.5 text-[10px] font-bold text-tacir-darkgray hover:text-tacir-blue transition-colors rounded-lg hover:bg-tacir-lightgray px-2 py-1 -mx-2 w-full group"
                    >
                      <Terminal class="w-3 h-3 group-hover:text-tacir-blue" />
                      <span>Voir logs ({{ phase.logs.length }})</span>
                      <ChevronDown
                        class="w-3 h-3 ml-auto transition-transform duration-200"
                        :class="openLogs.has(pid + ':' + phase.name) ? 'rotate-180' : ''"
                      />
                    </button> -->

                    <!-- Log terminal -->
                    <!-- <div
                      v-if="openLogs.has(pid + ':' + phase.name)"
                      class="mt-2 bg-slate-900 rounded-lg p-2.5 font-mono overflow-y-auto max-h-48"
                    >
                      <div
                        v-for="(log, li) in phase.logs"
                        :key="li"
                        class="flex gap-1.5 py-0.5 border-b border-slate-800/60 last:border-0"
                      >
                        <span class="text-slate-500 flex-shrink-0 tabular-nums text-[9px]">{{ log.ts }}</span>
                        <span :class="logLevelClass(log.lvl)" class="flex-shrink-0 uppercase font-black w-6 text-[8px]">{{ log.lvl }}</span>
                        <span class="text-slate-300 break-all text-[9px]">{{ log.text }}</span>
                      </div>
                    </div> -->

                  <!-- </CardContent> -->
                <!-- </Card> --> 

                <!-- Connector -->
                <!-- <div v-if="idx < pipelines[pid].phases.length - 1" class="flex justify-center py-0.5">
                  <ChevronDown class="w-3.5 h-3.5 text-tacir-darkgray/30" />
                </div>

                  </template>
                </div>
              </div>
            </Transition> -->

          </div>
        </div>

      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import TheSidebar from '@/components/AppSidebar.vue'
import { Card, CardContent }  from '@/components/ui/card'
import { Badge }              from '@/components/ui/badge'
import { Button }             from '@/components/ui/button'
import {
  Clock, Play, Square, RotateCcw,
  CheckCircle2, XCircle, Loader2, Circle,
  Terminal, ChevronDown, AlertTriangle,
  RefreshCw, Database, ArrowUpDown, Timer
} from 'lucide-vue-next'
import { usePipeline } from '@/composables/usePipeline'
import ChartStatusByDag from '@/components/dashboard/ChartStatusByDag.vue'
import ChartDurationBottlenecks from '@/components/dashboard/ChartDurationBottlenecks.vue'
import ChartVolumeTrends from '@/components/dashboard/ChartVolumeTrends.vue'
import ChartQualityCompleteness from '@/components/dashboard/ChartQualityCompleteness.vue'
import ChartBoampQuality from '@/components/dashboard/ChartBoampQuality.vue'
// ─────────────────────────────────────────────
// CONFIG
// ─────────────────────────────────────────────

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8001'

const TASK_LABELS = {
  scrape_boamp:       'Scraping incrémental des marchés publics BOAMP via API',
  extract_boamp:      'Extraction et parsing JSON des champs normalisés',
  enrich_boamp:       'Enrichissement SIRET via API INSEE / Annuaire entreprises',
  load_raw_boamp:     'Chargement dans le schéma raw.boamp (PostgreSQL)',
  clean_boamp:        'Déduplication, normalisation et validation des données',
  load_clean_boamp:   'Chargement final dans le schéma clean.boamp',
  scrape_sirene:      'Téléchargement du fichier SIRENE (data.gouv.fr) en incrémental',
  extract_datagouv:   'Parsing CSV et mapping vers le modèle de données interne',
  load_raw_datagouv:  'Insertion dans le schéma raw.sirene (upsert par SIRET)',
  clean_datagouv:     'Nettoyage, normalisation des codes NAF et validation LUHN SIREN',
  load_clean_sirene:  'Chargement final dans clean.sirene — inserts + updates',
  rapport_final:      'Génération du rapport de synthèse et notifications',
  cleanup:            'Nettoyage des fichiers temporaires',
}

// Ordre attendu des phases par pipeline
const PIPELINE_PHASE_ORDER = {
  sync_boamp: [
    'scrape_boamp','extract_boamp','enrich_boamp',
    'load_raw_boamp','clean_boamp','load_clean_boamp','rapport_final'
  ],
  sync_datagouv: [
    'scrape_sirene','extract_datagouv','load_raw_datagouv',
    'clean_datagouv','load_clean_sirene','rapport_final'
  ],
}

// ─────────────────────────────────────────────
// STATE
// ─────────────────────────────────────────────
const router = useRouter()
const globalMetrics = ref({ inserted_today: 0, updated_today: 0 })
const taskResources = ref({})  // { sync_boamp: { scrape_boamp: {cpu,ram,disk}, ... }, sync_datagouv: {...} }
const boamp    = usePipeline('sync_boamp',    taskResources)
const datagouv = usePipeline('sync_datagouv', taskResources)

const todayRuns = reactive({
  sync_boamp:    { total: 0, success: 0, failed: 0 },
  sync_datagouv: { total: 0, success: 0, failed: 0 },
})
const pipelineIds = ['sync_boamp', 'sync_datagouv']

// Structure réactive alimentée par l'API (même shape que les mock data)
const pipelines = reactive({
  sync_boamp: buildEmptyPipeline('sync_boamp'),
  sync_datagouv: buildEmptyPipeline('sync_datagouv'),
})

const expandedPipelines = ref(new Set())

const togglePipeline = (pid) => {
  if (expandedPipelines.value.has(pid)) {
    expandedPipelines.value.delete(pid)
  } else {
    expandedPipelines.value.add(pid)
  }
}

const openLogs         = ref(new Set())
const liveClock        = ref('')
const connectionStatus = ref({ sync_boamp: false, sync_datagouv: false })
const loadingLogs      = ref(new Set())

// AbortControllers pour les streams actifs
const activeStreams = {}

// Timers polling
let pollTimers   = {}
let clockTimer   = null

// ─────────────────────────────────────────────
// BUILDERS
// ─────────────────────────────────────────────

function buildEmptyPipeline(dagId) {
  const phaseNames = PIPELINE_PHASE_ORDER[dagId] ?? []
  return {
    runId:    '—',
    status:   'idle',
    progress: 0,
    start:    '—',
    end:      '—',
    phases:   phaseNames.map((name, i) => buildEmptyPhase(name, i + 1)),
  }
}

function buildEmptyPhase(name, num) {
  return {
    num,
    name,
    sub:   TASK_LABELS[name] ?? name,
    st:    'idle',
    dur:   '—',
    inp:   '—',
    out:   '—',
    cpu:   0,
    ram:   0,
    ramMb: 0,   // ← ajoute
    disk:  0,
    err:   null,
    logs:  [],
  }
}

// ─────────────────────────────────────────────
// MAPPERS — Airflow → shape attendue par le template
// ─────────────────────────────────────────────

function mapState(airflowState) {
  const MAP = {
    success:         'ok',
    failed:          'err',
    upstream_failed: 'err',
    running:         'run',
    queued:          'idle',
    scheduled:       'idle',
    skipped:         'idle',
    none:            'idle',
  }
  return MAP[airflowState] ?? 'idle'
}

function formatDuration(seconds) {
  if (!seconds || seconds <= 0) return '—'
  const m = Math.floor(seconds / 60)
  const s = Math.round(seconds % 60)
  return `${m}m ${s}s`
}

function formatTime(isoString) {
  if (!isoString) return '—'
  return new Date(isoString).toLocaleTimeString('fr-FR', {
    hour:   '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

// ─────────────────────────────────────────────
// API — fetch état du pipeline
// ─────────────────────────────────────────────

async function fetchPipelineState(dagId) {
  try {
    const res  = await fetch(`${BASE_URL}/api/monitoring/state/${dagId}`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()

    connectionStatus.value[dagId] = true
    await applyStateToReactive(dagId, data)   // ← await ajouté
    await fetchTodayRuns(dagId)           // ← ajoute ça


  } catch (e) {
    connectionStatus.value[dagId] = false
    console.error(`[POLL ${dagId}]`, e.message)
  }
}

async function applyStateToReactive(dagId, data) {
  const pl  = pipelines[dagId]
  const run = data.run
  if (!run) return

  pl.runId    = run.run_id ?? '—'
  pl.status   = mapState(run.state)
  pl.start    = formatTime(run.start_date)
  pl.end      = formatTime(run.end_date)
  pl.progress = data.progress ?? 0

  const xcoms = await fetchRunMetrics(dagId, pl.runId)
  const taskMap = {}
  for (const t of (data.tasks ?? [])) taskMap[t.task_id] = t

  // ── Construire les phases depuis taskResources déjà en cache ──
  pl.phases = (PIPELINE_PHASE_ORDER[dagId] ?? []).map((name, i) => {
    const task     = taskMap[name]
    const existing = pl.phases.find(p => p.name === name)
    const cfg      = TASK_XCOM_MAP[name] ?? {}
    const taskXcom = xcoms[name] ?? {}
    const outVal   = cfg.out ? taskXcom[cfg.out] : undefined
    const inpVal   = resolveInp(name, dagId, xcoms)

    if (!task) return existing ?? buildEmptyPhase(name, i + 1)

    const st  = mapState(task.state)
    const res = taskResources.value[dagId]?.[name] ?? { cpu: 0, ram: 0, disk: 0 }

    return {
      num:            i + 1,
      name:           task.task_id,
      sub:            TASK_LABELS[task.task_id] ?? task.task_id,
      st,
      dur:            formatDuration(task.duration),
      inp:            st === 'idle' ? '—' : inpVal,
      out:            st === 'idle' ? '—' : fmtMetric(outVal),
      cpu:            res.cpu,
      ram:            res.ram,
      ram_mb:         res.ram_mb  ?? 0,
      disk:           res.disk,
      resourceSource: res.source  ?? null,
      err:            task.state === 'failed'
                        ? `Task ${task.task_id} failed\nDAG: ${dagId} | Voir logs`
                        : null,
      logs:           existing?.logs ?? [],
    }
  })

  // ── Charger les ressources en parallèle APRÈS avoir construit les phases ──
  const toLoad = (data.tasks ?? []).filter(
    t => t.state && !['queued', 'scheduled', 'none', null].includes(t.state)
  )

  await Promise.all(
    toLoad.map(async t => {
      const cached = taskResources.value[dagId]?.[t.task_id]
      // Recharger si : pas en cache, ou valeurs à 0, ou task encore running
      if (!cached || cached.cpu === 0 || t.state === 'running') {
        const data = await fetchTaskResources(dagId, run.run_id, t.task_id)
        if (data) {
          // Mettre à jour taskResources — Vue détecte le changement
          taskResources.value = {
            ...taskResources.value,
            [dagId]: {
              ...(taskResources.value[dagId] ?? {}),
              [t.task_id]: {
                cpu:    data.cpu    ?? 0,
                ram:    data.ram    ?? 0,
                ram_mb: data.ram_mb ?? 0,
                disk:   data.disk   ?? 0,
                source: data.source ?? 'estimated',
              }
            }
          }
          // Mettre à jour la phase directement aussi pour trigger la réactivité
          const phase = pl.phases.find(p => p.name === t.task_id)
          if (phase) {
            phase.cpu            = data.cpu    ?? 0
            phase.ram            = data.ram    ?? 0
            phase.ram_mb         = data.ram_mb ?? 0
            phase.disk           = data.disk   ?? 0
            phase.resourceSource = data.source ?? 'estimated'
          }
        }
      }
    })
  )
}

async function fetchTaskResources(dagId, runId, taskId) {
  try {
    const res  = await fetch(
      `${BASE_URL}/api/monitoring/resources/task/${dagId}/${runId}/${taskId}`
    )
    if (!res.ok) return null
    return await res.json()
  } catch {
    return null
  }
}



async function fetchTodayRuns(dagId) {
  try {
    const res  = await fetch(`${BASE_URL}/api/monitoring/runs/today/${dagId}`)
    const data = await res.json()
    todayRuns[dagId] = data
  } catch (e) {
    console.error(`[TODAY RUNS ${dagId}]`, e.message)
  }
}
// ─────────────────────────────────────────────
// API — Logs snapshot (task terminée)
// ─────────────────────────────────────────────

async function fetchLogsSnapshot(dagId, runId, taskId) {
  try {
    const res  = await fetch(
      `${BASE_URL}/api/monitoring/logs/${dagId}/${runId}/${taskId}`
    )
    const data = await res.json()
    return data.lines ?? []
  } catch {
    return []
  }
}

// ─────────────────────────────────────────────
// API — Stream logs (task en cours) — tail -f
// ─────────────────────────────────────────────

function startLogStream(dagId, runId, taskId) {
  // Stopper un éventuel stream précédent sur cette task
  stopLogStream(dagId, taskId)

  const key        = `${dagId}:${taskId}`
  const controller = new AbortController()
  activeStreams[key] = controller

  const phase = pipelines[dagId].phases.find(p => p.name === taskId)
  if (phase) phase.logs = []

  const url = `${BASE_URL}/api/monitoring/logs/${dagId}/${runId}/${taskId}/stream`

  fetch(url, { signal: controller.signal })
    .then(async (response) => {
      const reader  = response.body.getReader()
      const decoder = new TextDecoder()
      let   buffer  = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const line of lines) {
          if (!line.trim()) continue
          try {
            const parsed = JSON.parse(line)

            const phase  = pipelines[dagId].phases.find(p => p.name === taskId)
            if (phase) phase.logs.push(parsed)
          } catch { /* ligne non-JSON, ignorer */ }
        }
      }
      delete activeStreams[key]
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        console.error(`[STREAM ${key}]`, err.message)
      }
    })
}

function stopLogStream(dagId, taskId) {
  const key = `${dagId}:${taskId}`
  if (activeStreams[key]) {
    activeStreams[key].abort()
    delete activeStreams[key]
  }
}

// ─────────────────────────────────────────────
// WATCHER — démarre le stream quand une task passe en running
// ─────────────────────────────────────────────

pipelineIds.forEach(dagId => {
  watch(
    () => pipelines[dagId].phases.map(p => p.st),
    (newStates, oldStates) => {
      if (!oldStates) return
      const pl = pipelines[dagId]

      newStates.forEach((newSt, idx) => {
        const oldSt  = oldStates[idx]
        const phase  = pl.phases[idx]
        const runId  = pl.runId

        // Task vient de passer en running → démarrer le stream
        if (newSt === 'run' && oldSt !== 'run') {
          startLogStream(dagId, runId, phase.name)
        }

        // Task vient de terminer → arrêter le stream + snapshot final
        if ((newSt === 'ok' || newSt === 'err') && oldSt === 'run') {
          stopLogStream(dagId, phase.name)
          fetchLogsSnapshot(dagId, runId, phase.name).then(lines => {
            phase.logs = lines
          })
        }
      })
    },
    { deep: false }
  )
})

// ─────────────────────────────────────────────
// LOGS — toggle + chargement à la demande
// ─────────────────────────────────────────────

async function toggleLog(pid, phaseName) {
  const key = `${pid}:${phaseName}`
  const s   = new Set(openLogs.value)

  if (s.has(key)) {
    s.delete(key)
    openLogs.value = s
    return
  }

  s.add(key)
  openLogs.value = s

  // Charger les logs si pas encore chargés et task terminée
  const phase = pipelines[pid].phases.find(p => p.name === phaseName)
  if (phase && phase.logs.length === 0 && phase.st !== 'idle' && phase.st !== 'run') {
    const runId = pipelines[pid].runId
    if (runId && runId !== '—') {
      loadingLogs.value.add(key)
      const lines = await fetchLogsSnapshot(pid, runId, phaseName)
      phase.logs = lines
      loadingLogs.value.delete(key)
    }
  }
}

// ─────────────────────────────────────────────
// ACTIONS — Démarrer / Stop / Reset via API Airflow
// ─────────────────────────────────────────────

const simulatingPipelines = reactive(new Set())

async function handleStart(dagId) {
  if (simulatingPipelines.has(dagId)) return
  simulatingPipelines.add(dagId)

  try {
    const res  = await fetch(`${BASE_URL}/api/monitoring/trigger/${dagId}`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({}),
    })
    const data = await res.json()
    console.log(`[TRIGGER ${dagId}]`, data)

    // Forcer un poll immédiat après déclenchement
    setTimeout(() => fetchPipelineState(dagId), 1500)
    setTimeout(() => fetchPipelineState(dagId), 4000)

  } catch (e) {
    console.error(`[TRIGGER ${dagId}]`, e.message)
  } finally {
    // Retirer après 5s pour éviter double-clic
    setTimeout(() => simulatingPipelines.delete(dagId), 5000)
  }
}

async function handleStop(dagId) {
  // Appel API Airflow pour marquer le run comme failed
  try {
    const pl  = pipelines[dagId]
    const url = `${import.meta.env.VITE_AIRFLOW_URL ?? 'http://localhost:8080'}`
            + `/api/v2/dags/${dagId}/dagRuns/${pl.runId}`
    await fetch(url, {
      method:  'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Basic ' + btoa('ali:ali'),
      },
      body: JSON.stringify({ state: 'failed' }),
    })
  } catch (e) {
    console.warn('[STOP] Airflow API non disponible, application locale')
  }

  // Mise à jour locale immédiate
  const pl = pipelines[dagId]
  pl.status = 'err'
  pl.phases.forEach(p => { if (p.st === 'run') p.st = 'err' })

  // Arrêter tous les streams actifs de ce pipeline
  pl.phases.forEach(p => stopLogStream(dagId, p.name))
}

function handleReset(dagId) {
  // Arrêter les streams
  pipelines[dagId].phases.forEach(p => stopLogStream(dagId, p.name))

  // Remettre à zéro localement
  Object.assign(pipelines[dagId], buildEmptyPipeline(dagId))

  // Nettoyer les logs ouverts
  const s = new Set(openLogs.value)
  for (const key of s) {
    if (key.startsWith(`${dagId}:`)) s.delete(key)
  }
  openLogs.value = s
}

// ─────────────────────────────────────────────
// POLLING — toutes les 2 secondes
// ─────────────────────────────────────────────

function startPolling(dagId) {
  fetchPipelineState(dagId)  // poll immédiat au montage
  pollTimers[dagId] = setInterval(() => fetchPipelineState(dagId), 2000)
}

function stopPolling(dagId) {
  if (pollTimers[dagId]) {
    clearInterval(pollTimers[dagId])
    delete pollTimers[dagId]
  }
}

// ─────────────────────────────────────────────
// KPIs — computed depuis les données réelles
// ─────────────────────────────────────────────

const kpis = computed(() => {
  const totalRuns    = pipelineIds.reduce((acc, id) => acc + (todayRuns[id]?.total   ?? 0), 0)
  const totalSuccess = pipelineIds.reduce((acc, id) => acc + (todayRuns[id]?.success ?? 0), 0)
  const totalFailed  = pipelineIds.reduce((acc, id) => acc + (todayRuns[id]?.failed  ?? 0), 0)

  const successRate = totalRuns
    ? Math.round((totalSuccess / totalRuns) * 100)
    : 0

  // ← supprimé : allPhases, loadPhases, extractNum (plus utilisés)
  const rowsInserted = globalMetrics.value.inserted_today
  const rowsUpdated  = globalMetrics.value.updated_today

  const allPhases   = Object.values(pipelines).flatMap(p => p.phases)  // ← gardé uniquement pour avgDuration
  const parseDur    = d => {
    const m = (d || '').match(/(\d+)m\s*(\d+)s/)
    return m ? parseInt(m[1]) * 60 + parseInt(m[2]) : 0
  }
  const okPhases    = allPhases.filter(p => p.st === 'ok' && p.dur !== '—')
  const avgSec      = okPhases.length
    ? Math.round(okPhases.reduce((acc, p) => acc + parseDur(p.dur), 0) / okPhases.length)
    : 0
  const avgDuration = avgSec >= 60
    ? `${Math.floor(avgSec / 60)}m ${avgSec % 60}s`
    : avgSec > 0 ? `${avgSec}s` : '—'

  return {
    totalRuns,
    runsVsYesterday: 0,
    successRate,
    rowsInserted,
    rowsUpdated,
    errorsToday: totalFailed,
    avgDuration,
  }
})

// ─────────────────────────────────────────────
// CONFIG — mapping XCom par task
// ─────────────────────────────────────────────

const TASK_XCOM_MAP = {
  // sync_boamp
  scrape_boamp:      { inp: null,                  out: 'total_raw' },
  extract_boamp:     { inp: 'total_raw',            out: 'total_extracted' },
  enrich_boamp:      { inp: 'total_extracted',      out: 'total_extracted' },
  load_raw_boamp:    { inp: 'total_extracted',      out: 'total_raw_loaded' },
  clean_boamp:       { inp: 'total_raw_loaded',     out: 'total_clean' },
  load_clean_boamp:  { inp: 'total_clean',          out: 'total_clean_loaded' },
  // sync_datagouv
  scrape_sirene:     { inp: null,                   out: 'total_raw' },
  extract_datagouv:  { inp: 'total_raw',            out: 'total_extracted' },
  load_raw_datagouv: { inp: 'total_extracted',      out: 'total_raw_loaded' },
  clean_datagouv:    { inp: 'total_raw_loaded',     out: 'total_clean' },
  load_clean_sirene: { inp: 'total_clean',          out: 'total_clean_loaded' },
}

// ─────────────────────────────────────────────
// API — fetch métriques XCom pour un run
// ─────────────────────────────────────────────

async function fetchRunMetrics(dagId, runId) {
  if (!runId || runId === '—') return {}
  try {
    const res  = await fetch(`${BASE_URL}/api/monitoring/metrics/${dagId}/${runId}`)
    if (!res.ok) return {}
    const data = await res.json()
    return data.metrics ?? {}
  } catch {
    return {}
  }
}

// ─────────────────────────────────────────────
// API — fetch métriques des ligns inserees ou modifies dans la table entreprise chaque jour
// ─────────────────────────────────────────────



async function fetchGlobalMetrics() {
  try {
    const res  = await fetch(`${BASE_URL}/api/monitoring/metrics`)
    const data = await res.json()
    globalMetrics.value = {
      inserted_today: data.inserted_today ?? 0,
      updated_today:  data.updated_today  ?? 0,
    }
  } catch (e) {
    console.error('[METRICS]', e.message)
  }
}
// ─────────────────────────────────────────────
// HELPER — formater une valeur XCom en lisible
// ─────────────────────────────────────────────

function fmtMetric(val) {
  if (val === null || val === undefined) return '—'
  return `${Number(val).toLocaleString('fr-FR')} lignes`
}

// ─────────────────────────────────────────────
// HELPER — résoudre inp d'une task depuis les XComs voisins
// ─────────────────────────────────────────────

function resolveInp(taskName, dagId, xcoms) {
  const cfg = TASK_XCOM_MAP[taskName]
  if (!cfg || !cfg.inp) return '—'

  // Chercher la clé inp dans toutes les tasks du dag
  const phaseOrder = PIPELINE_PHASE_ORDER[dagId] ?? []
  for (const name of phaseOrder) {
    if (xcoms[name]?.[cfg.inp] !== undefined) {
      return fmtMetric(xcoms[name][cfg.inp])
    }
  }
  return '—'
}

// ─────────────────────────────────────────────
// STYLE HELPERS — identiques à l'original
// ─────────────────────────────────────────────

function pipelineStatusLabel(st) {
  return ({ ok: 'SUCCESS', err: 'FAILED', run: 'RUNNING', idle: 'IDLE' })[st] ?? st
}
function pipelineStatusIcon(st) {
  return ({ ok: CheckCircle2, err: XCircle, run: Loader2, idle: Circle })[st] ?? Circle
}
function pipelineStatusBadgeClass(st) {
  return ({
    ok:   'bg-emerald-50 text-emerald-700 border-emerald-200 rounded-lg font-black uppercase text-[9px] tracking-widest px-2 py-0',
    err:  'bg-red-50 text-red-700 border-red-200 rounded-lg font-black uppercase text-[9px] tracking-widest px-2 py-0',
    run:  'bg-tacir-blue/10 text-tacir-blue border-tacir-blue/20 rounded-lg font-black uppercase text-[9px] tracking-widest px-2 py-0',
    idle: 'bg-tacir-lightgray text-tacir-darkgray border-border rounded-lg font-black uppercase text-[9px] tracking-widest px-2 py-0',
  })[st] ?? ''
}
function phaseBorderClass(st) {
  return ({ ok: 'border-l-4 border-l-emerald-400', err: 'border-l-4 border-l-red-400', run: 'border-l-4 border-l-tacir-blue', idle: 'border-l-4 border-l-tacir-lightgray' })[st] ?? ''
}
function phaseCircleClass(st) {
  return ({ ok: 'bg-emerald-100 text-emerald-700', err: 'bg-red-100 text-red-600', run: 'bg-tacir-blue/10 text-tacir-blue', idle: 'bg-tacir-lightgray text-tacir-darkgray' })[st] ?? ''
}
function phaseStatusBadgeClass(st) {
  return ({ ok: 'bg-emerald-50 text-emerald-700 border-emerald-200', err: 'bg-red-50 text-red-700 border-red-200', run: 'bg-tacir-blue/10 text-tacir-blue border-tacir-blue/20', idle: 'bg-tacir-lightgray text-tacir-darkgray border-border' })[st] ?? ''
}
function phaseStatusLabel(st) {
  return ({ ok: 'Succès', err: 'Échec', run: 'En cours', idle: 'En attente' })[st] ?? st
}
function phaseStatusIcon(st) {
  return ({ ok: CheckCircle2, err: XCircle, run: Loader2, idle: Circle })[st] ?? Circle
}
function resourceBarClass(val, st) {
  if (st === 'idle') return 'bg-tacir-lightgray'
  if (val < 45)  return 'bg-emerald-500'
  if (val <= 70) return 'bg-amber-400'
  return 'bg-red-500'
}
function resourceTextClass(val, st) {
  if (st === 'idle') return 'text-tacir-darkgray'
  if (val < 45)  return 'text-emerald-600'
  if (val <= 70) return 'text-amber-600'
  return 'text-red-600'
}
function logLevelClass(lvl) {
  return ({ ok: 'text-emerald-400', warn: 'text-amber-400', err: 'text-red-400', info: 'text-slate-500' })[lvl] ?? 'text-slate-400'
}
function isLoadPhase(name)  { return name.startsWith('load_') }
function completionRate(phase) {
  const extract = s => { const m = (s || '').match(/[\d\s]+/); return m ? Number(m[0].replace(/\s/g, '')) : 0 }
  const inp = extract(phase.inp), out = extract(phase.out)
  if (!inp || !out) return 100
  return Math.min(100, Math.round((out / inp) * 100))
}

// ─────────────────────────────────────────────
// LIFECYCLE
// ─────────────────────────────────────────────

onMounted(() => {
  // Démarrer le polling pour les deux pipelines
  pipelineIds.forEach(startPolling)
  fetchGlobalMetrics()
  setInterval(fetchGlobalMetrics, 30000) 
  // Horloge
  updateClock()
  clockTimer = setInterval(updateClock, 1000)
})

onUnmounted(() => {
  pipelineIds.forEach(stopPolling)
  pipelineIds.forEach(dagId => {
    pipelines[dagId].phases.forEach(p => stopLogStream(dagId, p.name))
  })
  if (clockTimer) clearInterval(clockTimer)
})

function updateClock() {
  liveClock.value = new Date().toLocaleTimeString('fr-FR', {
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  })
}
</script>