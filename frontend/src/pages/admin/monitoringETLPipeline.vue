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

        <!-- ── SIDE BY SIDE PIPELINES GRID ── -->
        <div class="grid grid-cols-1 xl:grid-cols-2 gap-6 items-start">

          <div
            v-for="pid in pipelineIds"
            :key="pid"
            class="flex flex-col gap-4"
          >
            <!-- Pipeline header label -->
            <div class="flex items-center gap-2">
              <span class="text-base">{{ pid === 'sync_boamp' ? '📄' : '🇫🇷' }}</span>
              <h3 class="text-sm font-black text-tacir-darkblue tracking-tight">{{ pid }}</h3>
              <Badge :class="pipelineStatusBadgeClass(pipelines[pid].status)" class="ml-1">
                <component :is="pipelineStatusIcon(pipelines[pid].status)" class="w-2.5 h-2.5 mr-1" :class="pipelines[pid].status === 'run' ? 'animate-spin' : ''" />
                {{ pipelineStatusLabel(pipelines[pid].status) }}
              </Badge>
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

                <!-- Action buttons -->
                <div class="flex items-center gap-2">
                  <Button
                    @click="handleStart(pid)"
                    :disabled="simulatingPipelines.has(pid)"
                    class="flex-1 h-8 bg-tacir-blue hover:bg-tacir-darkblue text-white rounded-lg gap-1.5 shadow-sm transition-all active:scale-95 text-[11px] font-bold disabled:opacity-50"
                  >
                    <Play class="w-3 h-3" />
                    Démarrer
                  </Button>
                  <Button
                    @click="handleStop(pid)"
                    variant="destructive"
                    class="flex-1 h-8 rounded-lg gap-1.5 text-[11px] font-bold transition-all active:scale-95"
                  >
                    <Square class="w-3 h-3" />
                    Stop
                  </Button>
                  <Button
                    @click="handleReset(pid)"
                    variant="outline"
                    class="flex-1 h-8 rounded-lg gap-1.5 border-border text-tacir-darkblue hover:bg-tacir-lightgray text-[11px] font-bold transition-all active:scale-95"
                  >
                    <RotateCcw class="w-3 h-3" />
                    Reset
                  </Button>
                </div>

              </CardContent>
            </Card>

            <!-- ── PHASE CARDS ── -->
            <div class="space-y-0">
              <template v-for="(phase, idx) in pipelines[pid].phases" :key="phase.name">

                <Card
                  class="border-border shadow-sm rounded-2xl bg-white overflow-hidden"
                  :class="phaseBorderClass(phase.st)"
                >
                  <CardContent class="p-4">

                    <!-- Phase header -->
                    <div class="flex items-start gap-2.5 mb-3">
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
                    </div>

                    <!-- Metadata row -->
                    <div class="grid grid-cols-4 gap-1.5 mb-3">
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
                    </div>

                    <!-- Resource bars -->
                    <div class="grid grid-cols-3 gap-2 mb-3">
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
                    </div>

                    <!-- Taux de complétude (load phases only) -->
                    <div v-if="isLoadPhase(phase.name) && phase.st === 'ok'" class="mb-3">
                      <div class="flex justify-between items-center mb-0.5">
                        <span class="text-[9px] uppercase tracking-wider font-semibold text-tacir-darkgray">Taux de complétude</span>
                        <span class="text-[10px] font-black text-tacir-lightblue">{{ completionRate(phase) }}%</span>
                      </div>
                      <div class="w-full h-1.5 bg-tacir-lightgray rounded-full overflow-hidden">
                        <div class="h-full rounded-full bg-tacir-lightblue transition-all duration-700" :style="{ width: completionRate(phase) + '%' }"></div>
                      </div>
                    </div>

                    <!-- Error box -->
                    <div v-if="phase.err && phase.st === 'err'" class="bg-red-50 border border-red-200 rounded-xl p-3 font-mono text-[10px] text-red-800 mb-3">
                      <div class="flex items-center gap-1.5 mb-1.5 font-sans">
                        <AlertTriangle class="w-3 h-3 text-red-500" />
                        <span class="text-[9px] uppercase tracking-wider font-black text-red-600">Erreur d'exécution</span>
                      </div>
                      <pre class="whitespace-pre-wrap break-all text-[9px] leading-relaxed">{{ phase.err }}</pre>
                    </div>

                    <!-- Log toggle -->
                    <div class="h-px bg-border mb-2" />
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
                    </button>

                    <!-- Log terminal -->
                    <div
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
                        <span class="text-slate-300 break-all text-[9px]">{{ log.msg }}</span>
                      </div>
                    </div>

                  </CardContent>
                </Card>

                <!-- Connector -->
                <div v-if="idx < pipelines[pid].phases.length - 1" class="flex justify-center py-0.5">
                  <ChevronDown class="w-3.5 h-3.5 text-tacir-darkgray/30" />
                </div>

              </template>
            </div>

          </div>
        </div>

      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import TheSidebar from '@/components/AppSidebar.vue'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Clock, Play, Square, RotateCcw,
  CheckCircle2, XCircle, Loader2, Circle,
  Terminal, ChevronDown, AlertTriangle,
  RefreshCw, Database, ArrowUpDown, Timer
} from 'lucide-vue-next'

// ─────────────────────────────────────────────
// MOCK DATA
// ─────────────────────────────────────────────

const BOAMP_PIPELINE = {
  runId: 'run_boamp_20260411_0600',
  status: 'err',
  progress: 28,
  start: '06:00:01',
  end: '06:04:52',
  phases: [
    {
      num: 1, name: 'scrape_boamp',
      sub: 'Scraping incrémental des marchés publics BOAMP via API',
      st: 'ok', dur: '1m 18s', inp: '—', out: '1 247 marchés',
      cpu: 38, ram: 42, disk: 22, err: null,
      logs: [
        { ts: '06:00:01', lvl: 'info', msg: 'Démarrage du scraping incrémental BOAMP' },
        { ts: '06:00:05', lvl: 'info', msg: 'Connexion API BOAMP établie (endpoint: api.boamp.fr/avis)' },
        { ts: '06:00:23', lvl: 'ok',   msg: '623 avis récupérés depuis le dernier curseur' },
        { ts: '06:01:07', lvl: 'warn', msg: 'Rate-limit détecté — pause 5s automatique' },
        { ts: '06:01:18', lvl: 'ok',   msg: '1 247 marchés scrappés au total' },
      ]
    },
    {
      num: 2, name: 'extract_boamp',
      sub: 'Extraction et parsing JSON des champs normalisés',
      st: 'err', dur: '0m 32s', inp: '1 247 lignes', out: '0 lignes',
      cpu: 61, ram: 55, disk: 31,
      err: `Traceback (most recent call last):
  File "/opt/airflow/dags/boamp/extract.py", line 87, in process_record
    siret = record['acheteur'].get('siret')
AttributeError: 'NoneType' object has no attribute 'get'

Task exited with return code 1
DAG: sync_boamp | Task: extract_boamp`,
      logs: [
        { ts: '06:01:20', lvl: 'info', msg: 'Chargement de /tmp/boamp_raw_20260411.jsonl (1 247 entrées)' },
        { ts: '06:01:45', lvl: 'warn', msg: 'Enregistrement #412: champ "acheteur" est null — skipping' },
        { ts: '06:01:51', lvl: 'err',  msg: "AttributeError: 'NoneType' object has no attribute 'get' @ ligne 87" },
        { ts: '06:01:51', lvl: 'err',  msg: 'Extraction interrompue. Rollback effectué.' },
      ]
    },
    { num: 3, name: 'enrich_boamp',     sub: 'Enrichissement SIRET via API INSEE / Annuaire entreprises', st: 'idle', dur: '—', inp: '—', out: '—', cpu: 0, ram: 0, disk: 0, err: null, logs: [] },
    { num: 4, name: 'load_raw_boamp',   sub: 'Chargement dans le schéma raw.boamp (PostgreSQL)',          st: 'idle', dur: '—', inp: '—', out: '—', cpu: 0, ram: 0, disk: 0, err: null, logs: [] },
    { num: 5, name: 'clean_boamp',      sub: 'Déduplication, normalisation et validation des données',    st: 'idle', dur: '—', inp: '—', out: '—', cpu: 0, ram: 0, disk: 0, err: null, logs: [] },
    { num: 6, name: 'load_clean_boamp', sub: 'Chargement final dans le schéma clean.boamp',               st: 'idle', dur: '—', inp: '—', out: '—', cpu: 0, ram: 0, disk: 0, err: null, logs: [] },
    { num: 7, name: 'rapport_final',    sub: 'Génération du rapport de synthèse et notifications',        st: 'idle', dur: '—', inp: '—', out: '—', cpu: 0, ram: 0, disk: 0, err: null, logs: [] },
  ]
}

const DATAGOUV_PIPELINE = {
  runId: 'run_datagouv_20260411_1200',
  status: 'ok',
  progress: 100,
  start: '12:00:00',
  end: '12:14:37',
  phases: [
    {
      num: 1, name: 'scrape_sirene',
      sub: 'Téléchargement du fichier SIRENE (data.gouv.fr) en incrémental',
      st: 'ok', dur: '2m 05s', inp: '—', out: '1 240 établissements',
      cpu: 29, ram: 35, disk: 58, err: null,
      logs: [
        { ts: '12:00:00', lvl: 'info', msg: 'Démarrage du scraping SIRENE — delta depuis 2026-04-10' },
        { ts: '12:00:04', lvl: 'info', msg: 'GET https://files.data.gouv.fr/insee-sirene/... → 200 OK' },
        { ts: '12:01:12', lvl: 'ok',   msg: '1 240 lignes extraites du fichier CSV delta' },
        { ts: '12:02:05', lvl: 'ok',   msg: 'Scraping terminé. Fichier: /tmp/sirene_delta_20260411.csv' },
      ]
    },
    {
      num: 2, name: 'extract_datagouv',
      sub: 'Parsing CSV et mapping vers le modèle de données interne',
      st: 'ok', dur: '0m 48s', inp: '1 240 lignes', out: '1 238 lignes',
      cpu: 44, ram: 39, disk: 26, err: null,
      logs: [
        { ts: '12:02:06', lvl: 'info', msg: 'Parsing du CSV SIRENE (1 240 lignes)' },
        { ts: '12:02:18', lvl: 'warn', msg: '2 lignes ignorées: NIC vide ou format SIREN invalide' },
        { ts: '12:02:54', lvl: 'ok',   msg: '1 238 enregistrements extraits et mappés avec succès' },
      ]
    },
    {
      num: 3, name: 'load_raw_datagouv',
      sub: 'Insertion dans le schéma raw.sirene (upsert par SIRET)',
      st: 'ok', dur: '1m 12s', inp: '1 238 lignes', out: '1 238 insérées',
      cpu: 72, ram: 68, disk: 81, err: null,
      logs: [
        { ts: '12:02:55', lvl: 'info', msg: 'Connexion PostgreSQL établie (pool=5)' },
        { ts: '12:02:56', lvl: 'info', msg: 'UPSERT batch de 1 238 enregistrements dans raw.sirene' },
        { ts: '12:04:07', lvl: 'ok',   msg: 'Load raw terminé: 1 238 lignes insérées / 0 erreurs' },
      ]
    },
    {
      num: 4, name: 'clean_datagouv',
      sub: 'Nettoyage, normalisation des codes NAF et validation LUHN SIREN',
      st: 'ok', dur: '2m 31s', inp: '1 238 lignes', out: '1 201 lignes valides',
      cpu: 53, ram: 47, disk: 34, err: null,
      logs: [
        { ts: '12:04:08', lvl: 'info', msg: 'Démarrage du nettoyage SIRENE' },
        { ts: '12:04:15', lvl: 'warn', msg: '23 entrées avec code NAF invalide → normalisation forcée' },
        { ts: '12:04:52', lvl: 'warn', msg: '14 entrées rejetées: SIREN échoue la validation LUHN' },
        { ts: '12:06:39', lvl: 'ok',   msg: '1 201 lignes validées — 37 rejetées → quarantine.sirene' },
      ]
    },
    {
      num: 5, name: 'load_clean_sirene',
      sub: 'Chargement final dans clean.sirene — 980 inserts + 221 updates',
      st: 'ok', dur: '1m 03s', inp: '1 201 lignes', out: '980 inserts + 221 updates',
      cpu: 66, ram: 61, disk: 74, err: null,
      logs: [
        { ts: '12:06:40', lvl: 'info', msg: 'Début du load dans clean.sirene' },
        { ts: '12:07:35', lvl: 'info', msg: 'UPDATE clean.sirene — 221 mises à jour' },
        { ts: '12:07:43', lvl: 'ok',   msg: '980 nouvelles entrées + 221 mises à jour — 0 conflits' },
      ]
    },
    {
      num: 6, name: 'rapport_final',
      sub: 'Génération du rapport de qualité et envoi des notifications',
      st: 'ok', dur: '0m 54s', inp: '—', out: 'Rapport PDF + e-mail',
      cpu: 18, ram: 22, disk: 12, err: null,
      logs: [
        { ts: '12:07:44', lvl: 'info', msg: 'Génération du rapport Jinja2 — template: rapport_sirene.html' },
        { ts: '12:08:05', lvl: 'ok',   msg: 'Rapport PDF généré: rapport_sirene_20260411.pdf (42 KB)' },
        { ts: '12:08:21', lvl: 'ok',   msg: 'E-mail envoyé à [data-team@entreprise.fr]' },
        { ts: '12:08:38', lvl: 'ok',   msg: 'Pipeline sync_datagouv terminé — durée totale: 14m 37s' },
      ]
    },
  ]
}

// ─────────────────────────────────────────────
// STATE
// ─────────────────────────────────────────────

const pipelineIds = ['sync_boamp', 'sync_datagouv']

const pipelines = reactive({
  sync_boamp:    JSON.parse(JSON.stringify(BOAMP_PIPELINE)),
  sync_datagouv: JSON.parse(JSON.stringify(DATAGOUV_PIPELINE)),
})

// Track which pipelines are currently simulating
const simulatingPipelines = reactive(new Set())
const simTimers = {}

// Log open state: key = "pid:phaseName"
const openLogs = ref(new Set())

const liveClock = ref('')

// ─────────────────────────────────────────────
// GLOBAL KPIs — computed from reactive pipeline data
// ─────────────────────────────────────────────

const kpis = computed(() => {
  const allPipelines = Object.values(pipelines)

  // Total runs = number of pipelines that have been started (not idle)
  const totalRuns = allPipelines.filter(p => p.status !== 'idle').length

  // Successful phases across all pipelines
  const allPhases   = allPipelines.flatMap(p => p.phases)
  const okPhases    = allPhases.filter(p => p.st === 'ok')
  const errPhases   = allPhases.filter(p => p.st === 'err')
  const successRate = allPhases.length
    ? Math.round((okPhases.length / allPhases.length) * 100)
    : 0

  // Count error-status phases as "pipeline errors today"
  const errorsToday = errPhases.length

  // Rows inserted: sum numeric values found in 'out' fields of load phases (raw + clean)
  const extractNum = str => {
    const nums = (str || '').match(/\d[\d\s]*/g)
    return nums ? nums.reduce((acc, n) => acc + Number(n.replace(/\s/g, '')), 0) : 0
  }
  const loadPhases = allPhases.filter(p => p.name.startsWith('load_') && p.st === 'ok')
  // Rows inserted = phases whose output does NOT contain 'updates' (pure inserts)
  const rowsInserted = loadPhases.reduce((acc, p) => {
    if (!p.out.includes('updates')) return acc + extractNum(p.out)
    // If output is "980 inserts + 221 updates", take only the first number
    const m = p.out.match(/^(\d[\d\s]*)/)
    return acc + (m ? Number(m[1].replace(/\s/g, '')) : 0)
  }, 0)

  // Rows updated = sum of numbers following 'updates' keyword in all load phase outputs
  const rowsUpdated = loadPhases.reduce((acc, p) => {
    const m = p.out.match(/(\d[\d\s]*)\s*updates?/)
    return acc + (m ? Number(m[1].replace(/\s/g, '')) : 0)
  }, 0)

  // Average duration: parse "Xm Ys" strings to seconds, average, then format back
  const parseDur = d => {
    const m = (d || '').match(/(\d+)m\s*(\d+)s/)
    return m ? parseInt(m[1]) * 60 + parseInt(m[2]) : 0
  }
  const finishedPhases = okPhases.filter(p => p.dur !== '—')
  const avgSec = finishedPhases.length
    ? Math.round(finishedPhases.reduce((acc, p) => acc + parseDur(p.dur), 0) / finishedPhases.length)
    : 0
  const avgDuration = avgSec >= 60
    ? `${Math.floor(avgSec / 60)}m ${avgSec % 60}s`
    : `${avgSec}s`

  return {
    totalRuns,
    runsVsYesterday: 33,   // static mock delta vs yesterday
    successRate,
    rowsInserted,
    rowsUpdated,
    errorsToday,
    avgDuration,
  }
})

// ─────────────────────────────────────────────
// STYLE HELPERS
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
function isLoadPhase(name) { return name.startsWith('load_') }
function completionRate(phase) {
  const extract = s => { const m = (s || '').match(/[\d\s]+/); return m ? Number(m[0].replace(/\s/g, '')) : 0 }
  const inp = extract(phase.inp), out = extract(phase.out)
  if (!inp || !out) return 100
  return Math.min(100, Math.round((out / inp) * 100))
}
function toggleLog(pid, phaseName) {
  const key = pid + ':' + phaseName
  const s = new Set(openLogs.value)
  s.has(key) ? s.delete(key) : s.add(key)
  openLogs.value = s
}

// ─────────────────────────────────────────────
// SIMULATION (per pipeline)
// ─────────────────────────────────────────────

function handleStart(pid) {
  if (simulatingPipelines.has(pid)) return
  const pl = pipelines[pid]
  simulatingPipelines.add(pid)
  pl.phases.forEach(p => { p.st = 'idle'; p.cpu = 0; p.ram = 0; p.disk = 0 })
  pl.status = 'run'; pl.progress = 0; pl.end = ''
  pl.start = new Date().toLocaleTimeString('fr-FR')

  let idx = 0
  const step = () => {
    if (idx >= pl.phases.length) {
      pl.status = 'ok'; pl.progress = 100
      pl.end = new Date().toLocaleTimeString('fr-FR')
      simulatingPipelines.delete(pid); return
    }
    const phase = pl.phases[idx]
    phase.st = 'run'
    phase.cpu  = Math.floor(Math.random() * 75 + 15)
    phase.ram  = Math.floor(Math.random() * 70 + 20)
    phase.disk = Math.floor(Math.random() * 80 + 5)
    simTimers[pid] = setTimeout(() => {
      phase.st = 'ok'; idx++
      pl.progress = Math.round((idx / pl.phases.length) * 100)
      step()
    }, 1200)
  }
  step()
}

function handleStop(pid) {
  if (simTimers[pid]) clearTimeout(simTimers[pid])
  simulatingPipelines.delete(pid)
  const pl = pipelines[pid]
  pl.status = 'err'
  pl.phases.forEach(p => { if (p.st === 'run') p.st = 'err' })
}

function handleReset(pid) {
  if (simTimers[pid]) clearTimeout(simTimers[pid])
  simulatingPipelines.delete(pid)
  pipelines[pid] = JSON.parse(JSON.stringify(pid === 'sync_boamp' ? BOAMP_PIPELINE : DATAGOUV_PIPELINE))
  // Clear logs for this pipeline
  const s = new Set(openLogs.value)
  for (const key of s) { if (key.startsWith(pid + ':')) s.delete(key) }
  openLogs.value = s
}

// ─────────────────────────────────────────────
// LIVE CLOCK
// ─────────────────────────────────────────────

let clockTimer = null
function updateClock() {
  liveClock.value = new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}
onMounted(() => { updateClock(); clockTimer = setInterval(updateClock, 1000) })
onUnmounted(() => {
  if (clockTimer) clearInterval(clockTimer)
  Object.values(simTimers).forEach(t => clearTimeout(t))
})
</script>
