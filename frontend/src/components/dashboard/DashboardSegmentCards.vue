<template>
  <!-- One card per segment with coloured left border -->
  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">

    <template v-if="loading">
      <div
        v-for="i in 4" :key="i"
        class="rounded-xl border border-border bg-card p-4 animate-pulse"
      >
        <div class="h-3 w-20 bg-muted rounded mb-4" />
        <div class="space-y-2">
          <div class="h-3 w-full bg-muted rounded" />
          <div class="h-3 w-4/5 bg-muted rounded" />
          <div class="h-3 w-3/4 bg-muted rounded" />
        </div>
        <div class="mt-4 h-2 w-full bg-muted rounded-full" />
      </div>
    </template>

    <template v-else>
      <div
        v-for="seg in segments"
        :key="seg.name"
        class="rounded-xl border border-border border-l-4 bg-card p-4 hover:shadow-md hover:-translate-y-0.5 transition-all duration-200"
        :style="{ borderLeftColor: SEGMENT_COLORS[seg.name] ?? '#94a3b8' }"
      >
        <!-- Header -->
        <div class="flex items-center gap-2 mb-3">
          <span class="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">Segment</span>
          <span
            class="text-[11px] font-semibold px-2 py-0.5 rounded-md"
            :class="SEGMENT_BG[seg.name] ?? 'bg-muted text-muted-foreground'"
          >
            {{ seg.name }}
          </span>
        </div>

        <!-- Stats rows -->
        <div class="space-y-1.5 text-sm">
          <div class="flex items-center justify-between">
            <span class="text-xs text-muted-foreground">CA moyen</span>
            <span class="text-xs font-medium text-foreground">{{ seg.caMoyen }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-xs text-muted-foreground">Complétude</span>
            <span class="text-xs font-medium text-foreground">{{ seg.completude }}%</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-xs text-muted-foreground">Âge moyen</span>
            <span class="text-xs font-medium text-foreground">{{ seg.ageMoyen }} ans</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-xs text-muted-foreground">Prospects</span>
            <span class="text-xs font-semibold text-foreground">{{ seg.count.toLocaleString('fr-FR') }}</span>
          </div>
        </div>

        <!-- Potentiel commercial — en attente scoring ML -->
        <div class="mt-3 pt-3 border-t border-border/60">
          <div class="flex items-center justify-between">
            <p class="text-[10px] text-muted-foreground">Potentiel commercial</p>
            <span class="text-[9px] font-semibold px-2 py-0.5 rounded-full bg-muted text-muted-foreground border border-border">
              En attente ML
            </span>
          </div>
        </div>
      </div>
    </template>

  </div>
</template>

<script setup>
import { SEGMENT_COLORS, SEGMENT_BG } from '@/lib/dashboardData'

defineProps({
  segments: { type: Array, required: true },
  loading:  { type: Boolean, default: false },
})
</script>
