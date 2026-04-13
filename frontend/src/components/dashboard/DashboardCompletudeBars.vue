<template>
  <div class="rounded-xl border border-border bg-card p-5">
    <h3 class="text-sm font-semibold text-foreground mb-1">Complétude des données par segment</h3>
    <p class="text-[11px] text-muted-foreground mb-5">Taux de remplissage moyen des fiches (%)</p>

    <!-- Skeleton -->
    <template v-if="loading">
      <div class="space-y-4">
        <div v-for="i in 4" :key="i" class="space-y-1.5">
          <div class="h-3 w-24 bg-muted rounded animate-pulse" />
          <div class="h-5 bg-muted rounded-full animate-pulse" :style="{ width: `${30 + i * 15}%` }" />
        </div>
      </div>
    </template>

    <template v-else>
      <div class="space-y-5">
        <div v-for="seg in segments" :key="seg.name" class="space-y-1.5">

          <!-- Label + value -->
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold" :style="{ color: SEGMENT_COLORS[seg.name] ?? '#94a3b8' }">
              {{ seg.name }}
            </span>
            <span class="text-xs font-bold text-foreground">{{ seg.completude }}%</span>
          </div>

          <!-- Track -->
          <div class="w-full h-5 rounded-full bg-muted overflow-hidden">
            <div
              class="h-full rounded-full flex items-center justify-end pr-2 transition-all duration-700 ease-out"
              :style="{
                width: `${seg.completude}%`,
                backgroundColor: SEGMENT_COLORS[seg.name] ?? '#94a3b8',
              }"
            >
              <span v-if="seg.completude >= 20" class="text-[9px] font-bold text-white">
                {{ seg.completude }}%
              </span>
            </div>
          </div>

          <!-- Sub info -->
          <p class="text-[10px] text-muted-foreground">{{ seg.count }} prospect{{ seg.count !== 1 ? 's' : '' }}</p>
        </div>
      </div>
    </template>

  </div>
</template>

<script setup>
import { SEGMENT_COLORS } from '@/lib/dashboardData'

defineProps({
  segments: { type: Array, required: true },
  loading:  { type: Boolean, default: false },
})
</script>
