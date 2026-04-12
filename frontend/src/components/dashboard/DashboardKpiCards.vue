<template>
  <!-- 4 KPI cards: Total, CA moyen, Complétude, Âge moyen -->
  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">

    <div
      v-for="card in cards"
      :key="card.label"
      class="rounded-xl border border-border bg-card p-4 hover:shadow-md hover:-translate-y-0.5 transition-all duration-200"
    >
      <!-- Skeleton -->
      <template v-if="loading">
        <div class="flex items-center gap-2 mb-3">
          <div class="w-8 h-8 rounded-lg bg-muted animate-pulse" />
          <div class="h-3 w-24 rounded bg-muted animate-pulse" />
        </div>
        <div class="h-7 w-20 rounded bg-muted animate-pulse mb-1" />
        <div class="h-2.5 w-28 rounded bg-muted animate-pulse" />
      </template>

      <!-- Real data -->
      <template v-else>
        <div class="flex items-center gap-2 mb-2">
          <div class="w-8 h-8 rounded-lg bg-tacir-blue/10 flex items-center justify-center flex-shrink-0">
            <component :is="card.icon" class="w-4 h-4 text-tacir-blue" />
          </div>
          <span class="text-xs text-muted-foreground font-medium">{{ card.label }}</span>
        </div>
        <p class="text-2xl font-bold text-foreground tracking-tight">{{ card.value }}</p>
        <p class="text-[11px] text-muted-foreground mt-0.5">{{ card.sub }}</p>
      </template>
    </div>

  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Users, TrendingUp, Clock, BarChart3 } from 'lucide-vue-next'

const props = defineProps({
  kpis:    { type: Object, required: true },
  loading: { type: Boolean, default: false },
})

const cards = computed(() => [
  {
    icon:  Users,
    label: 'Total Prospects',
    value: props.kpis.totalLeads?.toLocaleString('fr-FR') ?? '—',
    sub:   'DataGouv + BOAMP',
  },
  {
    icon:  BarChart3,
    label: 'CA moyen',
    value: props.kpis.averageRevenue ?? '—',
    sub:   'Tous segments confondus',
  },
  {
    icon:  TrendingUp,
    label: 'Complétude moyenne',
    value: `${props.kpis.averageCompleteness ?? 0}%`,
    sub:   'Données enrichies',
  },
  {
    icon:  Clock,
    label: 'Âge moyen',
    value: `${props.kpis.averageAge ?? 0} ans`,
    sub:   'Ancienneté des entreprises',
  },
])
</script>
