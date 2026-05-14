<template>
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
          <div class="relative">
            <button
              class="relative inline-flex h-9 w-9 items-center justify-center rounded-md border border-input bg-white text-tacir-darkblue transition-colors hover:bg-accent"
              title="Notifications"
              @click="showNotifications = !showNotifications"
            >
              <Bell class="h-4 w-4" />
              <span
                v-if="notifications.length"
                class="absolute -right-1.5 -top-1.5 flex h-5 min-w-5 items-center justify-center rounded-full bg-red-600 px-1 text-[10px] font-bold leading-none text-white"
              >
                {{ notifications.length > 99 ? '99+' : notifications.length }}
              </span>
            </button>

            <div
              v-if="showNotifications"
              class="absolute right-0 top-11 z-50 w-[min(92vw,420px)] overflow-hidden rounded-md border border-border bg-white shadow-xl"
            >
              <div class="flex items-center justify-between border-b border-border px-4 py-3">
                <div>
                  <p class="text-sm font-semibold text-tacir-darkblue">Notifications</p>
                  <p class="text-xs text-muted-foreground">{{ notifications.length }} alertes commerciales</p>
                </div>
                <button class="rounded-md border border-input p-1.5 hover:bg-accent" @click="showNotifications = false">
                  <X class="h-3.5 w-3.5" />
                </button>
              </div>

              <div class="max-h-96 overflow-y-auto">
                <button
                  v-for="notification in notifications"
                  :key="notification.id"
                  class="block w-full border-b border-border/70 px-4 py-3 text-left transition-colors hover:bg-muted/40"
                  @click="openNotification(notification)"
                >
                  <div class="flex items-center justify-between gap-3">
                    <span class="text-xs font-semibold text-tacir-darkblue">
                      {{ notificationTypeLabel(notification.notification_type) }}
                    </span>
                    <div class="flex shrink-0 items-center gap-2">
                      <span
                        v-if="scoreTrendValue(notification) !== null"
                        :class="scoreTrendClass(notification)"
                      >
                        {{ scoreTrendLabel(notification) }}
                      </span>
                      <span class="text-[11px] text-muted-foreground">
                        {{ formatDate(notification.last_visit_date) }}
                      </span>
                    </div>
                  </div>
                  <p class="mt-1 line-clamp-2 text-xs leading-5 text-muted-foreground">
                    {{ notification.message }}
                  </p>
                </button>

                <p v-if="!notifications.length" class="px-4 py-8 text-center text-sm text-muted-foreground">
                  Aucune notification.
                </p>
              </div>
            </div>
          </div>
          <button
            class="inline-flex h-9 items-center gap-2 rounded-md border border-input px-4 text-sm font-semibold transition-colors hover:bg-accent disabled:cursor-not-allowed disabled:opacity-60"
            :disabled="isRecalculating"
            @click="recalculate"
          >
            <RefreshCcw :class="['h-4 w-4', isRecalculating ? 'animate-spin' : '']" />
            Recalculer
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

            <Card class="border-border/80 xl:col-span-3">
              <CardContent class="p-5">
                <div class="flex items-center justify-between gap-3">
                  <ChartTitle :title="`Evolution des visites par ${visitPeriod === 'year' ? 'annee' : 'mois'}`" />
                  <div class="inline-flex rounded-md border border-input bg-white p-0.5">
                    <button
                      v-for="period in visitPeriods"
                      :key="period.value"
                      :class="[
                        'h-7 rounded px-3 text-xs font-semibold transition-colors',
                        visitPeriod === period.value ? 'bg-tacir-blue text-white' : 'text-muted-foreground hover:bg-accent',
                      ]"
                      @click="setVisitPeriod(period.value)"
                    >
                      {{ period.label }}
                    </button>
                  </div>
                </div>
                <div class="mt-5 flex h-56 items-end gap-2 overflow-x-auto pb-2">
                  <div
                    v-for="row in visitsEvolution"
                    :key="row.period_label || row.period_start"
                    class="flex h-full min-w-12 flex-1 flex-col justify-end gap-2"
                    :title="`${row.period_label}: ${row.visits} visites`"
                  >
                    <span class="text-center text-[11px] font-semibold text-tacir-darkblue">
                      {{ compactNumber(row.visits) }}
                    </span>
                    <div
                      class="mx-auto w-full rounded-t bg-tacir-blue/70"
                      :style="{ height: `${barHeight(row.visits, visitsMax)}%` }"
                    />
                    <span class="truncate text-center text-[11px] text-muted-foreground">
                      {{ row.period_label }}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card class="border-border/80 xl:col-span-2">
              <CardContent class="p-5">
                <ChartTitle title="Repartition appareils" />
                <div class="mt-5 grid gap-5 sm:grid-cols-[180px_1fr] sm:items-center">
                  <div
                    class="mx-auto h-44 w-44 rounded-full"
                    :style="devicePieStyle"
                    title="Repartition appareils"
                  />
                  <div class="space-y-3">
                    <div
                      v-for="(row, index) in deviceDistribution"
                      :key="row.device_category"
                      class="flex items-center justify-between gap-3 text-xs"
                    >
                      <div class="flex min-w-0 items-center gap-2">
                        <span
                          class="h-3 w-3 shrink-0 rounded-full"
                          :style="{ backgroundColor: deviceColor(index) }"
                        />
                        <span class="truncate font-semibold text-tacir-darkblue">{{ row.device_category }}</span>
                      </div>
                      <span class="shrink-0 text-muted-foreground">
                        {{ compactNumber(row.count) }} / {{ formatPercent(row.count / deviceTotal) }}
                      </span>
                    </div>
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
          </section>

          <section>
            <Card class="border-border/80">
              <CardContent class="p-0">
                <div class="flex flex-col gap-3 border-b border-border p-4 md:flex-row md:items-center md:justify-between">
                  <div>
                    <h2 class="text-sm font-semibold text-tacir-darkblue">Top Leads</h2>
                    <p class="text-xs text-muted-foreground">Classement par score comportemental /100.</p>
                  </div>
                  <div class="flex items-center gap-2">
                    <button
                      v-for="limit in [10, 20]"
                      :key="limit"
                      :class="[
                        'h-8 rounded-md border px-3 text-xs font-semibold',
                        topLimit === limit ? 'border-tacir-blue bg-tacir-blue text-white' : 'border-input bg-white hover:bg-accent',
                      ]"
                      @click="setTopLimit(limit)"
                    >
                      Top {{ limit }}
                    </button>
                  </div>
                </div>

                <div class="overflow-x-auto">
                  <table class="w-full min-w-[820px] text-sm">
                    <thead class="border-b border-border bg-muted/40 text-left text-[11px] uppercase tracking-wide text-muted-foreground">
                      <tr>
                        <th class="px-4 py-3">Rang</th>
                        <th class="px-4 py-3">full_visitor_id</th>
                        <th class="px-4 py-3">Score</th>
                        <th class="px-4 py-3">Segment</th>
                        <th class="px-4 py-3">Sessions</th>
                        <th class="px-4 py-3">Derniere visite</th>
                        <th class="px-4 py-3">Appareil</th>
                        <th class="px-4 py-3">Bounce rate</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr
                        v-for="lead in topLeads"
                        :key="lead.full_visitor_id"
                        class="cursor-pointer border-b border-border/70 transition-colors hover:bg-muted/40"
                        @click="openLead(lead.full_visitor_id)"
                      >
                        <td class="px-4 py-3 font-semibold">{{ lead.rank_position }}</td>
                        <td class="px-4 py-3 font-mono text-xs">{{ lead.full_visitor_id }}</td>
                        <td class="px-4 py-3 font-semibold">{{ formatScore(lead.lead_score_100) }}</td>
                        <td class="px-4 py-3"><SegmentBadge :segment="lead.segment" /></td>
                        <td class="px-4 py-3">{{ lead.nombre_sessions }}</td>
                        <td class="px-4 py-3">{{ formatDate(lead.last_visit_date) }}</td>
                        <td class="px-4 py-3">{{ lead.device_category || '-' }}</td>
                        <td class="px-4 py-3">{{ formatPercent(lead.bounce_rate) }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </section>

          <Card class="border-border/80">
            <CardContent class="p-0">
              <div class="flex flex-col gap-3 border-b border-border p-4 md:flex-row md:items-center md:justify-between">
                <div>
                  <h2 class="text-sm font-semibold text-tacir-darkblue">Leads comportementaux</h2>
                  <p class="text-xs text-muted-foreground">{{ leads.total }} leads analyses</p>
                </div>
                <div class="flex flex-col gap-2 sm:flex-row">
                  <div class="relative">
                    <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <input
                      v-model="search"
                      class="h-9 w-full rounded-md border border-input bg-white pl-9 pr-3 text-sm outline-none focus:border-tacir-blue sm:w-72"
                      placeholder="Rechercher full_visitor_id"
                      @input="handleSearchInput"
                    />
                  </div>
                  <select
                    v-model="segmentFilter"
                    class="h-9 rounded-md border border-input bg-white px-3 text-sm outline-none focus:border-tacir-blue"
                    @change="reloadLeads"
                  >
                    <option value="">Tous segments</option>
                    <option value="HOT">HOT</option>
                    <option value="WARM">WARM</option>
                    <option value="COLD">COLD</option>
                  </select>
                  <select
                    v-model="deviceFilter"
                    class="h-9 rounded-md border border-input bg-white px-3 text-sm outline-none focus:border-tacir-blue"
                    @change="reloadLeads"
                  >
                    <option value="">Tous appareils</option>
                    <option
                      v-for="device in deviceFilterOptions"
                      :key="device"
                      :value="device"
                    >
                      {{ device }}
                    </option>
                  </select>
                </div>
              </div>

              <div class="overflow-x-auto">
                <table class="w-full min-w-[820px] text-sm">
                  <thead class="border-b border-border bg-muted/40 text-left text-[11px] uppercase tracking-wide text-muted-foreground">
                    <tr>
                      <th class="px-4 py-3">Rang</th>
                      <th class="px-4 py-3">Lead</th>
                      <th class="px-4 py-3">Score</th>
                      <th class="px-4 py-3">Segment</th>
                      <th class="px-4 py-3">Sessions</th>
                      <th class="px-4 py-3">Derniere visite</th>
                      <th class="px-4 py-3">Appareil</th>
                      <th class="px-4 py-3">Bounce</th>
                      <th class="px-4 py-3">Détails</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="lead in leads.results"
                      :key="lead.full_visitor_id"
                      class="cursor-pointer border-b border-border/70 transition-colors hover:bg-muted/40"
                      @click="openLead(lead.full_visitor_id)"
                    >
                      <td class="px-4 py-3 font-semibold">{{ lead.rank_position }}</td>
                      <td class="px-4 py-3 font-mono text-xs">{{ lead.full_visitor_id }}</td>
                      <td class="px-4 py-3 font-semibold">{{ formatScore(lead.lead_score_100) }}</td>
                      <td class="px-4 py-3"><SegmentBadge :segment="lead.segment" /></td>
                      <td class="px-4 py-3">{{ lead.nombre_sessions }}</td>
                      <td class="px-4 py-3">{{ formatDate(lead.last_visit_date) }}</td>
                      <td class="px-4 py-3">{{ lead.device_category || '-' }}</td>
                      <td class="px-4 py-3">{{ formatPercent(lead.bounce_rate) }}</td>
                      <td class="px-4 py-3">
                        <button
                          class="h-8 rounded-md border border-input px-3 text-xs font-semibold transition-colors hover:bg-accent"
                          @click.stop="openLead(lead.full_visitor_id)"
                        >
                          Détails
                        </button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div class="flex items-center justify-between p-4">
                <p class="text-xs text-muted-foreground">Page {{ leads.page }} / {{ leads.total_pages }}</p>
                <div class="flex gap-2">
                  <button class="h-8 rounded-md border px-3 text-xs font-semibold disabled:opacity-50" :disabled="page <= 1" @click="changePage(page - 1)">
                    Precedent
                  </button>
                  <button class="h-8 rounded-md border px-3 text-xs font-semibold disabled:opacity-50" :disabled="page >= leads.total_pages" @click="changePage(page + 1)">
                    Suivant
                  </button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  </div>

  <div v-if="selectedLead" class="fixed inset-0 z-50 bg-black/30" @click.self="selectedLead = null">
    <aside class="ml-auto h-full w-full max-w-3xl overflow-y-auto bg-white shadow-xl">
      <div class="sticky top-0 z-10 flex items-center justify-between border-b border-border bg-white p-5">
        <div>
          <p class="text-xs uppercase tracking-wide text-muted-foreground">Detail Lead</p>
          <h2 class="font-mono text-sm font-semibold text-tacir-darkblue">{{ selectedLead.full_visitor_id }}</h2>
        </div>
        <button class="rounded-md border border-input p-2 hover:bg-accent" @click="selectedLead = null">
          <X class="h-4 w-4" />
        </button>
      </div>

      <div class="space-y-5 p-5">
        <section class="grid gap-3 sm:grid-cols-3">
          <MetricCard label="Score" :value="formatScore(selectedLead.lead_score_100)" />
          <MetricCard label="Segment" :value="selectedLead.segment" />
          <MetricCard label="Recency" :value="formatScore(selectedLead.recency_score)" />
          <MetricCard label="Sessions" :value="selectedLead.nombre_sessions" />
          <MetricCard label="Premiere visite" :value="formatDate(selectedLead.first_visit_date)" />
          <MetricCard label="Derniere visite" :value="formatDate(selectedLead.last_visit_date)" />
        </section>

        <Card class="border-border/80">
          <CardContent class="grid gap-3 p-5 sm:grid-cols-2">
            <InfoRow label="Activite suspecte" :value="selectedLead.suspicious_activity ? 'Oui' : 'Non'" />
            <InfoRow label="Appareil" :value="selectedLead.device_category" />
            <InfoRow label="Navigateur" :value="selectedLead.browser" />
            <InfoRow label="Pays" :value="selectedLead.country" />
            <InfoRow label="Ville" :value="selectedLead.city" />
            <InfoRow label="Source trafic" :value="selectedLead.traffic_source" />
            <InfoRow label="Hits moyens" :value="formatNumber(selectedLead.avg_hits_per_session)" />
            <InfoRow label="Pageviews moyens" :value="formatNumber(selectedLead.avg_pageviews_per_session)" />
            <InfoRow label="Bounce rate" :value="formatPercent(selectedLead.bounce_rate)" />
            <InfoRow label="Temps moyen" :value="formatSeconds(selectedLead.avg_time_on_site)" />
          </CardContent>
        </Card>

        <Card class="border-border/80">
          <CardContent class="p-5">
            <div class="flex items-center justify-between gap-3">
              <div>
                <h3 class="text-sm font-semibold text-tacir-darkblue">Pourquoi ce segment ?</h3>
                <p class="text-xs text-muted-foreground">
                  Explication basee sur le score comportemental et les penalites appliquees.
                </p>
              </div>
              <SegmentBadge :segment="selectedLead.segment" />
            </div>
            <div class="mt-4 space-y-3">
              <div
                v-for="reason in leadReasons(selectedLead)"
                :key="reason.label"
                class="rounded-md border border-border bg-muted/20 p-3"
              >
                <div class="flex items-center justify-between gap-3">
                  <p class="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    {{ reason.label }}
                  </p>
                  <span :class="reasonToneClass(reason.tone)">
                    {{ reason.value }}
                  </span>
                </div>
                <p class="mt-1 text-sm leading-5 text-tacir-darkblue">
                  {{ reason.description }}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card class="border-border/80">
          <CardContent class="p-0">
            <div class="border-b border-border p-4">
              <h3 class="text-sm font-semibold text-tacir-darkblue">Historique sessions</h3>
            </div>
            <div class="overflow-x-auto">
              <table class="w-full min-w-[680px] text-sm">
                <thead class="border-b border-border bg-muted/40 text-left text-[11px] uppercase tracking-wide text-muted-foreground">
                  <tr>
                    <th class="px-4 py-3">Date</th>
                    <th class="px-4 py-3">Heure</th>
                    <th class="px-4 py-3">Browser</th>
                    <th class="px-4 py-3">Device</th>
                    <th class="px-4 py-3">Hits</th>
                    <th class="px-4 py-3">Pageviews</th>
                    <th class="px-4 py-3">Bounce</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="session in selectedLead.sessions" :key="session.session_id" class="border-b border-border/70">
                    <td class="px-4 py-3">{{ formatDate(session.visit_date) }}</td>
                    <td class="px-4 py-3">{{ session.visit_hour ?? '-' }}h</td>
                    <td class="px-4 py-3">{{ session.browser || '-' }}</td>
                    <td class="px-4 py-3">{{ session.device_category || '-' }}</td>
                    <td class="px-4 py-3">{{ session.totals_hits }}</td>
                    <td class="px-4 py-3">{{ session.totals_pageviews }}</td>
                    <td class="px-4 py-3">{{ session.totals_bounces ? 'Oui' : 'Non' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </aside>
  </div>

  <div v-if="selectedNotification" class="fixed inset-0 z-50 bg-black/30" @click.self="selectedNotification = null">
    <div class="mx-auto mt-24 w-[calc(100%-2rem)] max-w-xl rounded-md bg-white shadow-xl">
      <div class="flex items-center justify-between border-b border-border p-5">
        <div>
          <p class="text-xs uppercase tracking-wide text-muted-foreground">Notification</p>
          <h2 class="text-sm font-semibold text-tacir-darkblue">
            {{ notificationTypeLabel(selectedNotification.notification_type) }}
          </h2>
        </div>
        <button class="rounded-md border border-input p-2 hover:bg-accent" @click="selectedNotification = null">
          <X class="h-4 w-4" />
        </button>
      </div>
      <div class="space-y-4 p-5">
        <p class="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm leading-6 text-amber-900">
          {{ selectedNotification.message }}
        </p>
        <div class="grid gap-3 sm:grid-cols-2">
          <InfoRow label="Lead" :value="selectedNotification.full_visitor_id" />
          <InfoRow label="Date derniere visite" :value="formatDate(selectedNotification.last_visit_date)" />
          <InfoRow label="Score trend" :value="scoreTrendLabel(selectedNotification)" />
          <InfoRow label="Ancien score" :value="formatScore(selectedNotification.old_score)" />
          <InfoRow label="Nouveau score" :value="formatScore(selectedNotification.new_score)" />
          <InfoRow label="Ancien segment" :value="selectedNotification.old_segment || '-'" />
          <InfoRow label="Nouveau segment" :value="selectedNotification.new_segment || '-'" />
        </div>
      </div>
    </div>
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
const visitPeriods = [
  { value: 'month', label: 'Mois' },
  { value: 'year', label: 'Annee' },
]

const segmentDistribution = computed(() => kpis.value.segment_distribution || [])
const visitsEvolution = computed(() => kpis.value.visits_evolution || [])
const deviceDistribution = computed(() => kpis.value.device_distribution || [])
const deviceFilterOptions = computed(() => deviceDistribution.value.map((row) => row.device_category).filter(Boolean))
const scoreDistribution = computed(() => kpis.value.score_distribution || [])
const segmentMax = computed(() => maxValue(segmentDistribution.value, 'count'))
const segmentTotal = computed(() => Math.max(1, segmentDistribution.value.reduce((sum, row) => sum + Number(row.count || 0), 0)))
const visitsMax = computed(() => maxValue(visitsEvolution.value, 'visits'))
const scoreMax = computed(() => maxValue(scoreDistribution.value, 'count'))
const deviceTotal = computed(() => Math.max(1, deviceDistribution.value.reduce((sum, row) => sum + Number(row.count || 0), 0)))
const devicePalette = ['#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#14b8a6', '#64748b', '#ec4899']
const devicePieStyle = computed(() => {
  let cursor = 0
  const segments = deviceDistribution.value.map((row, index) => {
    const start = cursor
    const size = (Number(row.count || 0) / deviceTotal.value) * 100
    cursor += size
    return `${deviceColor(index)} ${start}% ${cursor}%`
  })
  return {
    background: `conic-gradient(${segments.join(', ') || '#e5e7eb 0% 100%'})`,
    boxShadow: 'inset 0 0 0 34px #fff',
  }
})

async function fetchKpis() {
  const { data } = await behavioralApi.get('/analyse-comportementale/kpis', {
    params: { visits_period: visitPeriod.value },
  })
  kpis.value = { ...emptyKpis, ...data }
}

async function fetchTopLeads() {
  const { data } = await behavioralApi.get('/analyse-comportementale/top-leads', {
    params: { limit: topLimit.value },
  })
  topLeads.value = data || []
}

async function fetchNotifications() {
  const { data } = await behavioralApi.get('/analyse-comportementale/notifications')
  notifications.value = data || []
}

async function fetchLeads() {
  const params = {
    page: page.value,
    page_size: 20,
  }
  if (segmentFilter.value) params.segment = segmentFilter.value
  if (deviceFilter.value) params.device_category = deviceFilter.value
  if (activeSearch.value) params.search = activeSearch.value

  const { data } = await behavioralApi.get('/analyse-comportementale/leads', { params })
  leads.value = data
}

async function loadDashboard() {
  try {
    await Promise.all([fetchKpis(), fetchTopLeads(), fetchNotifications(), fetchLeads()])
  } catch (error) {
    console.error('[AnalyseComportementale] load error:', error)
    toast.error("Impossible de charger l'analyse comportementale.")
  }
}

async function recalculate() {
  isRecalculating.value = true
  try {
    const { data } = await behavioralApi.post('/analyse-comportementale/recalculate')
    toast.success('Analyse comportementale recalculee.', {
      description: `${data.scores || 0} leads scores, ${data.notifications || 0} notifications.`,
    })
    await loadDashboard()
  } catch (error) {
    console.error('[AnalyseComportementale] recalculate error:', error)
    toast.error('Impossible de recalculer les scores comportementaux.')
  } finally {
    isRecalculating.value = false
  }
}

async function openLead(fullVisitorId) {
  try {
    const { data } = await behavioralApi.get(`/analyse-comportementale/leads/${fullVisitorId}`)
    selectedLead.value = data
  } catch (error) {
    console.error('[AnalyseComportementale] detail error:', error)
    toast.error('Impossible de charger le detail du lead.')
  }
}

function setTopLimit(limit) {
  topLimit.value = limit
  fetchTopLeads()
}

function setVisitPeriod(period) {
  if (visitPeriod.value === period) return
  visitPeriod.value = period
  fetchKpis()
}

function openNotification(notification) {
  selectedNotification.value = notification
  showNotifications.value = false
}

function reloadLeads() {
  page.value = 1
  fetchLeads()
}

function handleSearchInput() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    activeSearch.value = search.value.trim()
    reloadLeads()
  }, 250)
}

function changePage(nextPage) {
  page.value = nextPage
  fetchLeads()
}

function maxValue(rows, key) {
  return Math.max(1, ...rows.map((row) => Number(row[key] || 0)))
}

function barHeight(value, max) {
  return Math.max(4, Math.round((Number(value || 0) / max) * 100))
}

function segmentPercent(value) {
  return (Number(value || 0) / segmentTotal.value) * 100
}

function formatScore(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '-'
  return Number(value).toFixed(1)
}

function formatPercent(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '-'
  return `${(Number(value) * 100).toFixed(1)}%`
}

function formatNumber(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '-'
  return Number(value).toFixed(2)
}

function compactNumber(value) {
  const numericValue = Number(value || 0)
  if (numericValue >= 1000000) return `${(numericValue / 1000000).toFixed(1)}M`
  if (numericValue >= 1000) return `${(numericValue / 1000).toFixed(1)}k`
  return String(numericValue)
}

function deviceColor(index) {
  return devicePalette[index % devicePalette.length]
}

function notificationTypeLabel(type) {
  const labels = {
    NEW_VISIT: 'Nouvelle visite',
    SCORE_CHANGED: 'Score modifie',
    SEGMENT_CHANGED: 'Segment modifie',
    BECAME_HOT: 'Devient HOT',
    SUSPICIOUS_ACTIVITY: 'Activite suspecte',
  }
  return labels[type] || type
}

function scoreTrendValue(notification) {
  const oldScore = Number(notification?.old_score)
  const newScore = Number(notification?.new_score)
  if (Number.isNaN(oldScore) || Number.isNaN(newScore)) return null
  return Number((newScore - oldScore).toFixed(1))
}

function scoreTrendLabel(notification) {
  const trend = scoreTrendValue(notification)
  if (trend === null) return '-'
  if (trend > 0) return `+${trend.toFixed(1)} pts`
  if (trend < 0) return `${trend.toFixed(1)} pts`
  return 'Stable'
}

function scoreTrendClass(notification) {
  const trend = scoreTrendValue(notification)
  const baseClass = 'rounded-full px-2 py-0.5 text-[11px] font-bold'
  if (trend === null || trend === 0) return `${baseClass} bg-slate-100 text-slate-700`
  if (trend > 0) return `${baseClass} bg-emerald-50 text-emerald-700`
  return `${baseClass} bg-rose-50 text-rose-700`
}

function leadReasons(lead) {
  if (!lead) return []

  const score = Number(lead.lead_score_100 || 0)
  const recency = Number(lead.recency_score || 0)
  const sessions = Number(lead.nombre_sessions || 0)
  const hits = Number(lead.avg_hits_per_session || 0)
  const pageviews = Number(lead.avg_pageviews_per_session || 0)
  const bounce = Number(lead.bounce_rate || 0)
  const suspicious = Number(lead.suspicious_activity || 0)

  const reasons = [
    {
      label: 'Score final',
      value: `${formatScore(score)}/100`,
      tone: lead.segment === 'HOT' ? 'positive' : lead.segment === 'WARM' ? 'warning' : 'negative',
      description: segmentReasonText(lead.segment, score),
    },
    {
      label: 'Recence',
      value: `${formatScore(recency)}/100`,
      tone: recency >= 70 ? 'positive' : recency >= 35 ? 'warning' : 'negative',
      description: recency >= 70
        ? 'Le lead a une visite recente, ce qui augmente fortement son potentiel.'
        : recency >= 35
          ? 'La derniere visite est moyennement recente.'
          : 'La derniere visite est ancienne, ce qui tire le score vers le bas.',
    },
    {
      label: 'Engagement',
      value: `${sessions} sessions`,
      tone: sessions > 1 ? 'positive' : 'warning',
      description: sessions > 1
        ? `Le lead a plusieurs sessions, avec ${formatNumber(hits)} hits et ${formatNumber(pageviews)} pageviews en moyenne.`
        : 'Le lead a une seule session, donc une penalite de prudence est appliquee.',
    },
    {
      label: 'Bounce rate',
      value: formatPercent(bounce),
      tone: bounce <= 0.35 ? 'positive' : bounce <= 0.7 ? 'warning' : 'negative',
      description: bounce <= 0.35
        ? 'Faible taux de rebond : les sessions semblent qualifiees.'
        : bounce <= 0.7
          ? 'Taux de rebond moyen : le comportement reste a surveiller.'
          : 'Taux de rebond eleve : le lead montre peu de profondeur de navigation.',
    },
  ]

  if (suspicious === 1) {
    reasons.push({
      label: 'Activite suspecte',
      value: 'Penalite -20%',
      tone: 'negative',
      description: 'Le lead presente une activite anormale. Il n’est pas supprime, mais son score est reduit.',
    })
  }

  return reasons
}

function segmentReasonText(segment, score) {
  if (segment === 'HOT') return `Score >= 60 : ce lead est prioritaire pour une action commerciale.`
  if (segment === 'WARM') return `Score entre 35 et 60 : ce lead est interessant mais pas encore prioritaire.`
  return `Score < 35 : ce lead est froid et demande une surveillance plutot qu'une action immediate.`
}

function reasonToneClass(tone) {
  const baseClass = 'shrink-0 rounded-full px-2 py-1 text-[11px] font-bold'
  if (tone === 'positive') return `${baseClass} bg-emerald-50 text-emerald-700`
  if (tone === 'warning') return `${baseClass} bg-amber-50 text-amber-700`
  return `${baseClass} bg-rose-50 text-rose-700`
}

function formatDate(value) {
  if (!value) return '-'
  return new Date(value).toLocaleDateString('fr-FR')
}

function formatSeconds(value) {
  const seconds = Number(value || 0)
  if (!seconds) return '0s'
  if (seconds < 60) return `${Math.round(seconds)}s`
  return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`
}

const MetricCard = defineComponent({
  props: {
    label: { type: String, required: true },
    value: { type: [String, Number], default: '-' },
    tone: { type: String, default: '' },
  },
  setup(props) {
    return () => h(Card, { class: 'border-border/80' }, {
      default: () => h(CardContent, { class: 'p-5' }, [
        h('p', { class: 'text-[11px] font-semibold uppercase tracking-widest text-muted-foreground' }, props.label),
        h('p', {
          class: [
            'mt-2 text-2xl font-bold',
            props.tone === 'hot' ? 'text-emerald-700' : '',
            props.tone === 'warm' ? 'text-amber-700' : '',
            props.tone === 'cold' ? 'text-rose-700' : '',
            !props.tone ? 'text-tacir-darkblue' : '',
          ],
        }, String(props.value ?? '-')),
      ]),
    })
  },
})

const ChartTitle = defineComponent({
  props: { title: { type: String, required: true } },
  setup(props) {
    return () => h('h2', { class: 'text-sm font-semibold text-tacir-darkblue' }, props.title)
  },
})

const SegmentBadge = defineComponent({
  props: { segment: { type: String, required: true } },
  setup(props) {
    return () => h('span', {
      class: [
        'inline-flex rounded-full px-2.5 py-1 text-xs font-semibold',
        props.segment === 'HOT' ? 'bg-emerald-50 text-emerald-700' : '',
        props.segment === 'WARM' ? 'bg-amber-50 text-amber-700' : '',
        props.segment === 'COLD' ? 'bg-rose-50 text-rose-700' : '',
      ],
    }, props.segment)
  },
})

const SegmentBar = defineComponent({
  props: {
    label: { type: String, required: true },
    value: { type: Number, required: true },
    percent: { type: Number, required: true },
    max: { type: Number, required: true },
  },
  setup(props) {
    return () => h('div', [
      h('div', { class: 'mb-1 flex items-center justify-between text-xs' }, [
        h('span', { class: 'font-semibold text-tacir-darkblue' }, props.label),
        h('span', { class: 'text-muted-foreground' }, `${props.percent.toFixed(1)}% (${props.value})`),
      ]),
      h('div', { class: 'h-2 rounded-full bg-muted' }, [
        h('div', {
          class: [
            'h-2 rounded-full',
            props.label === 'HOT' ? 'bg-emerald-500' : '',
            props.label === 'WARM' ? 'bg-amber-500' : '',
            props.label === 'COLD' ? 'bg-rose-500' : '',
          ],
          style: { width: `${Math.max(4, props.percent)}%` },
        }),
      ]),
    ])
  },
})

const PlainBar = defineComponent({
  props: {
    label: { type: String, required: true },
    value: { type: Number, required: true },
    max: { type: Number, required: true },
  },
  setup(props) {
    return () => h('div', [
      h('div', { class: 'mb-1 flex items-center justify-between gap-3 text-xs' }, [
        h('span', { class: 'truncate font-semibold text-tacir-darkblue' }, props.label),
        h('span', { class: 'text-muted-foreground' }, props.value),
      ]),
      h('div', { class: 'h-2 rounded-full bg-muted' }, [
        h('div', {
          class: 'h-2 rounded-full bg-tacir-blue',
          style: { width: `${barHeight(props.value, props.max)}%` },
        }),
      ]),
    ])
  },
})

const InfoRow = defineComponent({
  props: {
    label: { type: String, required: true },
    value: { type: [String, Number], default: '-' },
  },
  setup(props) {
    return () => h('div', { class: 'rounded-md border border-border bg-muted/20 p-3' }, [
      h('p', { class: 'text-[11px] font-semibold uppercase tracking-wide text-muted-foreground' }, props.label),
      h('p', { class: 'mt-1 text-sm font-semibold text-tacir-darkblue' }, String(props.value || '-')),
    ])
  },
})

onMounted(loadDashboard)
</script>

<style scoped>
.shadow-card {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 4px 16px rgba(48, 62, 140, 0.06);
}
</style>
