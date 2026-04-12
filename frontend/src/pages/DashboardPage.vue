<template>
  <div class="flex min-h-screen bg-tacir-lightgray/30">

    <!-- Sidebar -->
    <TheSidebar />

    <!-- Main -->
    <div class="flex-1 flex flex-col min-w-0">

      <!-- Header -->
      <header class="h-16 border-b border-border bg-white sticky top-0 z-40 px-6 flex items-center justify-between shadow-sm">
        <div class="flex items-center gap-3">
          <div class="md:hidden w-10" />
          <div>
            <h2 class="text-sm font-semibold text-tacir-darkblue hidden sm:block">{{ pageTitle }}</h2>
            <p class="text-[11px] text-tacir-darkgray hidden sm:block">{{ today }}</p>
          </div>
        </div>

        <div class="flex items-center gap-3">
          <span class="hidden sm:inline-flex items-center gap-1.5 bg-tacir-blue/8 text-tacir-blue border border-tacir-blue/15 text-[10px] font-semibold uppercase tracking-widest px-3 py-1 rounded-full">
            <span class="w-1.5 h-1.5 rounded-full bg-tacir-lightblue animate-pulse" />
            {{ user?.role }}
          </span>
          <button class="relative w-9 h-9 flex items-center justify-center rounded-lg hover:bg-tacir-lightgray text-tacir-darkgray transition-colors">
            <Bell class="h-4 w-4" />
            <span class="absolute top-1.5 right-1.5 w-2 h-2 bg-tacir-lightblue rounded-full" />
          </button>
          <RouterLink to="/profil" class="w-8 h-8 rounded-lg gradient-brand flex items-center justify-center text-white text-xs font-bold cursor-pointer hover:opacity-90 transition-opacity">
            {{ userInitial }}
          </RouterLink>
        </div>
      </header>

      <!-- Page content -->
      <main class="flex-1 p-6 md:p-8 overflow-y-auto">
        <Transition name="fade" mode="out-in" appear>
          <div :key="$route.path" class="max-w-7xl mx-auto space-y-8">

            <!-- Welcome -->
            <div>
              <h1 class="text-2xl font-bold text-tacir-darkblue mb-1">
                Bonjour, <span class="text-gradient">{{ firstName }}</span> 
              </h1>
              <p class="text-tacir-darkgray text-sm">{{ roleDescription }}</p>
            </div>

            <!-- KPI cards -->
            <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
              <div
                v-for="stat in stats"
                :key="stat.label"
                class="bg-white rounded-xl border border-border shadow-card p-5 flex items-start gap-4 hover:-translate-y-0.5 transition-transform duration-150"
              >
                <div :class="`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${stat.iconBg}`">
                  <component :is="stat.icon" :class="`h-5 w-5 ${stat.iconColor}`" />
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-[10px] font-semibold text-tacir-darkgray uppercase tracking-widest mb-1">{{ stat.label }}</p>
                  <p class="text-2xl font-bold text-tacir-darkblue leading-none mb-1.5">{{ stat.value }}</p>
                  <span class="inline-flex items-center gap-1 text-[11px] font-medium text-tacir-green bg-tacir-green/8 px-2 py-0.5 rounded-full">
                    <TrendingUp class="h-3 w-3" /> {{ stat.trend }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Charts row -->
            <div class="grid lg:grid-cols-7 gap-5">

              <!-- Bar chart: Pipeline -->
              <div class="lg:col-span-4 bg-white rounded-xl border border-border shadow-card p-6">
                <div class="flex items-center justify-between mb-6">
                  <div>
                    <p class="text-[10px] font-semibold text-tacir-darkgray uppercase tracking-widest mb-0.5">Pipeline mensuel</p>
                    <h3 class="text-sm font-semibold text-tacir-darkblue">Leads qualifiés par mois</h3>
                  </div>
                  <span class="text-[10px] text-tacir-lightblue font-medium bg-tacir-lightblue/10 px-2.5 py-1 rounded-full">2024</span>
                </div>
                <div class="flex items-end gap-2 h-40">
                  <div
                    v-for="(bar, i) in pipelineChart"
                    :key="bar.month"
                    class="flex-1 flex flex-col items-center gap-1.5 group"
                  >
                    <span class="text-[9px] text-tacir-darkgray opacity-0 group-hover:opacity-100 transition-opacity font-medium">
                      {{ bar.value }}
                    </span>
                    <div
                      class="w-full rounded-t-md transition-all duration-300 group-hover:opacity-100"
                      :style="{
                        height: `${(bar.value / maxPipeline) * 100}%`,
                        background: i === currentMonth
                          ? 'linear-gradient(180deg, #04ADBF, #303E8C)'
                          : '#EEF0F8',
                        opacity: i === currentMonth ? 1 : 0.7,
                      }"
                    />
                    <span class="text-[9px] text-tacir-darkgray font-medium">{{ bar.month }}</span>
                  </div>
                </div>
              </div>

              <!-- Donut chart: Score distribution -->
              <div class="lg:col-span-3 bg-white rounded-xl border border-border shadow-card p-6">
                <div class="mb-6">
                  <p class="text-[10px] font-semibold text-tacir-darkgray uppercase tracking-widest mb-0.5">Scoring</p>
                  <h3 class="text-sm font-semibold text-tacir-darkblue">Distribution des leads</h3>
                </div>

                <!-- SVG Donut -->
                <div class="flex items-center gap-6">
                  <div class="relative flex-shrink-0">
                    <svg viewBox="0 0 80 80" class="w-24 h-24 -rotate-90">
                      <circle cx="40" cy="40" r="28" fill="none" stroke="#F2F2F2" stroke-width="12" />
                      <!-- A: Chaud -->
                      <circle cx="40" cy="40" r="28" fill="none" stroke="#56A632" stroke-width="12"
                        :stroke-dasharray="`${scoreA.pct * 1.759} 175.9`"
                        stroke-dashoffset="0" stroke-linecap="round" />
                      <!-- B: Tiède -->
                      <circle cx="40" cy="40" r="28" fill="none" stroke="#303E8C" stroke-width="12"
                        :stroke-dasharray="`${scoreB.pct * 1.759} 175.9`"
                        :stroke-dashoffset="`-${scoreA.pct * 1.759}`"
                        stroke-linecap="round" />
                      <!-- C: Froid -->
                      <circle cx="40" cy="40" r="28" fill="none" stroke="#C5C5C5" stroke-width="12"
                        :stroke-dasharray="`${scoreC.pct * 1.759} 175.9`"
                        :stroke-dashoffset="`-${(scoreA.pct + scoreB.pct) * 1.759}`"
                        stroke-linecap="round" />
                    </svg>
                    <div class="absolute inset-0 flex flex-col items-center justify-center">
                      <span class="text-lg font-bold text-tacir-darkblue leading-none">{{ scoreA.pct }}%</span>
                      <span class="text-[9px] text-tacir-darkgray">chauds</span>
                    </div>
                  </div>

                  <div class="flex-1 space-y-3">
                    <div v-for="s in scoreItems" :key="s.label">
                      <div class="flex justify-between text-[11px] mb-1">
                        <span class="font-medium text-tacir-darkgray flex items-center gap-1.5">
                          <span class="w-2 h-2 rounded-full inline-block" :style="{ background: s.color }" />
                          {{ s.label }}
                        </span>
                        <span class="font-semibold text-tacir-darkblue">{{ s.pct }}%</span>
                      </div>
                      <div class="h-1.5 bg-tacir-lightgray rounded-full overflow-hidden">
                        <div class="h-full rounded-full" :style="{ width: `${s.pct}%`, background: s.color }" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Bottom row -->
            <div class="grid lg:grid-cols-7 gap-5">

              <!-- Activity feed -->
              <div class="lg:col-span-4 bg-white rounded-xl border border-border shadow-card p-6">
                <div class="flex items-center justify-between mb-5">
                  <div>
                    <p class="text-[10px] font-semibold text-tacir-darkgray uppercase tracking-widest mb-0.5">Activité</p>
                    <h3 class="text-sm font-semibold text-tacir-darkblue">Flux récent</h3>
                  </div>
                  <Activity class="h-4 w-4 text-tacir-lightblue" />
                </div>
                <div class="space-y-4">
                  <div v-for="(item, i) in activityFeed" :key="i" class="flex gap-3 items-start">
                    <div class="mt-1 w-2 h-2 rounded-full flex-shrink-0" :style="{ background: item.color }" />
                    <div class="flex-1 min-w-0">
                      <p class="text-sm font-medium text-tacir-darkblue leading-snug">{{ item.title }}</p>
                      <p class="text-xs text-tacir-darkgray mt-0.5">{{ item.desc }}</p>
                    </div>
                    <span class="text-[10px] text-tacir-darkgray flex-shrink-0 mt-0.5">{{ item.time }}</span>
                  </div>
                </div>
              </div>

              <!-- System status + quick actions -->
              <div class="lg:col-span-3 bg-white rounded-xl border border-border shadow-card p-6 flex flex-col gap-5">

                <!-- Status -->
                <div>
                  <div class="flex items-center justify-between mb-4">
                    <div>
                      <p class="text-[10px] font-semibold text-tacir-darkgray uppercase tracking-widest mb-0.5">Systèmes</p>
                      <h3 class="text-sm font-semibold text-tacir-darkblue">État des services</h3>
                    </div>
                    <ShieldCheck class="h-4 w-4 text-tacir-green" />
                  </div>
                  <div class="space-y-2.5">
                    <div
                      v-for="service in services"
                      :key="service.name"
                      class="flex items-center justify-between px-3.5 py-2.5 bg-tacir-lightgray/50 rounded-lg border border-border/50"
                    >
                      <div class="flex items-center gap-2.5">
                        <div class="w-2 h-2 rounded-full bg-tacir-green animate-pulse" />
                        <span class="text-xs font-medium text-tacir-darkblue">{{ service.name }}</span>
                      </div>
                      <span class="text-[10px] font-semibold text-tacir-green bg-tacir-green/10 px-2 py-0.5 rounded-full">
                        {{ service.status }}
                      </span>
                    </div>
                  </div>
                </div>

                <div class="border-t border-border" />

                <!-- Quick actions -->
                <div>
                  <p class="text-[10px] font-semibold text-tacir-darkgray uppercase tracking-widest mb-3">Actions rapides</p>
                  <div class="grid grid-cols-2 gap-2.5">
                    <button
                      v-for="action in quickActions"
                      :key="action.label"
                      class="flex flex-col items-center gap-2 p-3.5 rounded-lg border border-border hover:border-tacir-blue/30 hover:bg-tacir-blue/[0.04] transition-all group"
                    >
                      <component :is="action.icon" :class="`h-5 w-5 ${action.color} group-hover:scale-110 transition-transform`" />
                      <span class="text-[10px] font-semibold text-tacir-darkgray uppercase tracking-wider">{{ action.label }}</span>
                    </button>
                  </div>
                </div>

              </div>
            </div>

          </div>
        </Transition>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import TheSidebar from '@/components/AppSidebar.vue'

import {
  Bell, TrendingUp, Users, Target, RefreshCw,
  Activity, ShieldCheck, Zap, FileText, LayoutDashboard,
} from 'lucide-vue-next'

const { user } = useAuth()

// ── User helpers ─────────────────────────────────────────────────
const firstName = computed(() => user.value?.prenom || user.value?.email?.split('@')[0] || 'Utilisateur')
const userInitial = computed(() => (user.value?.full_name || user.value?.email || 'U').charAt(0).toUpperCase())
const today       = computed(() => new Date().toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' }))

// ── Page meta ────────────────────────────────────────────────────
const pageTitle = computed(() => {
  const r = user.value?.role
  if (r === 'ADMIN') return 'Centre de contrôle'
  if (r === 'CEO') return 'Management commercial'
  return 'Pipeline commercial'
})

const roleDescription = computed(() => {
  const r = user.value?.role
  if (r === 'ADMIN') return 'Accès complet au système. Gérez les utilisateurs, les intégrations CRM et les algorithmes de scoring.'
  if (r === 'CEO') return 'Suivez la performance de votre équipe, validez les qualifications et pilotez la sync CRM.'
  return 'Accédez à vos outils de prospection, qualifiez vos leads et synchronisez vos succès avec Boond.'
})

// ── KPI stats ────────────────────────────────────────────────────
const stats = computed(() => {
  const r = user.value?.role
  if (r === 'ADMIN') return [
    { label: 'Utilisateurs actifs', value: '42', icon: Users, iconBg: 'bg-tacir-blue/[0.08]', iconColor: 'text-tacir-blue', trend: '+12% ce mois' },
    { label: 'Uptime système', value: '99.9%', icon: Activity, iconBg: 'bg-tacir-green/[0.08]', iconColor: 'text-tacir-green', trend: 'Stable' },
    { label: 'Syncs totaux', value: '12.4k', icon: RefreshCw, iconBg: 'bg-tacir-lightblue/[0.10]', iconColor: 'text-tacir-lightblue', trend: '+5.2k cette sem' },
  ]
  if (r === 'CEO') return [
    { label: 'Pipeline équipe', value: '€1.2M', icon: TrendingUp, iconBg: 'bg-tacir-blue/[0.08]', iconColor: 'text-tacir-blue', trend: '+18% vs mois dernier' },
    { label: 'Taux conversion', value: '24%', icon: Target, iconBg: 'bg-tacir-green/[0.08]', iconColor: 'text-tacir-green', trend: '+3% amélioration' },
    { label: 'Activité équipe', value: '85%', icon: Activity, iconBg: 'bg-tacir-lightblue/[0.10]', iconColor: 'text-tacir-lightblue', trend: 'Haute performance' },
  ]
  return [
    { label: 'Mon pipeline', value: '€145k', icon: TrendingUp, iconBg: 'bg-tacir-blue/[0.08]', iconColor: 'text-tacir-blue', trend: '+€12k aujourd\'hui' },
    { label: 'Leads qualifiés', value: '18', icon: Target, iconBg: 'bg-tacir-green/[0.08]', iconColor: 'text-tacir-green', trend: '4 en attente sync' },
    { label: 'Score sync', value: '92/100', icon: Zap, iconBg: 'bg-tacir-lightblue/[0.10]', iconColor: 'text-tacir-lightblue', trend: 'Qualité excellente' },
  ]
})

// ── Bar chart data ────────────────────────────────────────────────
const pipelineChart = [
  { month: 'Jan', value: 42 }, { month: 'Fév', value: 58 }, { month: 'Mar', value: 51 },
  { month: 'Avr', value: 73 }, { month: 'Mai', value: 64 }, { month: 'Jun', value: 89 },
  { month: 'Jul', value: 77 }, { month: 'Aoû', value: 95 }, { month: 'Sep', value: 68 },
  { month: 'Oct', value: 83 }, { month: 'Nov', value: 91 }, { month: 'Déc', value: 76 },
]
const maxPipeline  = Math.max(...pipelineChart.map(b => b.value))
const currentMonth = new Date().getMonth()

// ── Donut chart data ──────────────────────────────────────────────
const scoreA     = { pct: 42, label: 'A — Chaud',  color: '#56A632' }
const scoreB     = { pct: 35, label: 'B — Tiède',  color: '#303E8C' }
const scoreC     = { pct: 23, label: 'C — Froid',  color: '#C5C5C5' }
const scoreItems = [scoreA, scoreB, scoreC]

// ── Activity feed ─────────────────────────────────────────────────
const activityFeed = [
  { title: 'Prospect #1027 qualifié pour sync Boond', desc: 'Score atteint : 87/100 — pipeline commercial', time: 'Il y a 12min', color: '#56A632'  },
  { title: 'Synchronisation CRM terminée',            desc: '24 fiches mises à jour dans Boond Manager',   time: 'Il y a 45min', color: '#04ADBF'  },
  { title: 'Nouveau lead enrichi automatiquement',    desc: 'Données juridiques et financières ajoutées',  time: 'Il y a 1h',   color: '#303E8C'  },
  { title: 'Rapport hebdomadaire généré',             desc: 'Disponible dans la section Rapports',         time: 'Il y a 3h',   color: '#7B797A'  },
]

// ── Services status ───────────────────────────────────────────────
const services = [
  { name: 'Sync Boond CRM',       status: 'Actif'   },
  { name: 'Moteur de scoring',    status: 'En ligne' },
  { name: 'Enrichissement auto',  status: 'Actif'   },
]

// ── Quick actions ─────────────────────────────────────────────────
const quickActions = [
  { label: 'Nouvelle sync', icon: Zap,      color: 'text-tacir-blue'      },
  { label: 'Rapports',      icon: FileText,  color: 'text-tacir-lightblue' },
  { label: 'Prospects',     icon: Target,    color: 'text-tacir-green'     },
  { label: 'Dashboard',     icon: LayoutDashboard, color: 'text-tacir-darkblue' },
]
</script>

<style scoped>
.gradient-brand {
  background: linear-gradient(135deg, #303e8c, #04adbf);
}
.text-gradient {
  background: linear-gradient(135deg, #303e8c, #04adbf);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.shadow-card {
  box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(48,62,140,0.06);
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>