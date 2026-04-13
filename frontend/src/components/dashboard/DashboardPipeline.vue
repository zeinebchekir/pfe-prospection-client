<template>
  <div class="rounded-xl border border-border bg-card p-5">

    <!-- Header -->
    <div class="mb-5">
      <h3 class="text-sm font-semibold text-foreground">Pipeline commercial</h3>
      <p class="text-[11px] text-muted-foreground mt-0.5">Répartition des leads par statut de qualification</p>
    </div>

    <!-- Skeleton -->
    <template v-if="loading">
      <div class="flex items-end gap-3 h-28">
        <div v-for="i in 3" :key="i" class="flex-1 flex flex-col items-center gap-1">
          <div class="h-3 w-8 bg-muted rounded animate-pulse" />
          <div class="w-full rounded-t-md bg-muted animate-pulse" :style="{ height: `${30 + i * 20}px` }" />
          <div class="h-3 w-16 bg-muted rounded animate-pulse" />
        </div>
      </div>
    </template>

    <template v-else>
      <!-- Funnel bars -->
      <div class="flex items-end gap-4">
        <div
          v-for="(step, i) in funnel"
          :key="step.name"
          class="flex-1 flex flex-col items-center gap-1.5"
        >
          <span class="text-lg font-bold text-foreground">{{ step.value }}</span>
          <div
            class="w-full rounded-t-xl transition-all duration-700 ease-out"
            :style="{
              height: `${Math.max(12, funnelBarHeight(step.value))}px`,
              backgroundColor: FUNNEL_COLORS[i] ?? '#94a3b8',
              opacity: 0.85,
            }"
          />
          <span class="text-[10px] text-muted-foreground text-center leading-tight">{{ step.name }}</span>
        </div>
      </div>

      <!-- Summary badges -->
      <div class="mt-5 flex flex-wrap gap-2">
        <span
          v-for="(step, i) in funnel"
          :key="step.name"
          class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold text-white"
          :style="{ backgroundColor: FUNNEL_COLORS[i] ?? '#94a3b8' }"
        >
          {{ step.value }} {{ step.name }}
        </span>
      </div>

      <!-- Scoring ML placeholder -->
      <div class="mt-5 pt-4 border-t border-border flex items-center justify-between">
        <div>
          <p class="text-xs font-semibold text-foreground">Scoring ML</p>
          <p class="text-[10px] text-muted-foreground mt-0.5">Probabilité de conversion par lead</p>
        </div>
        <span class="text-[10px] font-semibold px-2.5 py-1 rounded-full bg-muted text-muted-foreground border border-border">
          Non disponible
        </span>
      </div>
    </template>

  </div>
</template>

<script setup>
import { computed } from 'vue'
import { SEGMENT_COLORS } from '@/lib/dashboardData'

const props = defineProps({
  segments: { type: Array, required: true },
  funnel:   { type: Array, required: true },
  loading:  { type: Boolean, default: false },
})

const FUNNEL_COLORS = ['#303E8C', '#56A632', '#04ADBF']
const MAX_BAR_H = 100

function funnelBarHeight(value) {
  const max = Math.max(...props.funnel.map((f) => f.value), 1)
  return Math.max(16, (value / max) * MAX_BAR_H)
}
</script>
