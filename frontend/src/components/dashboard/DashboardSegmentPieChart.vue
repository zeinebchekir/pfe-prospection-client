<template>
  <div class="rounded-xl border border-border bg-card p-5">
    <h3 class="text-sm font-semibold text-foreground mb-4">Répartition des prospects par segment</h3>

    <!-- Skeleton -->
    <template v-if="loading">
      <div class="flex gap-4 mb-4 flex-wrap">
        <div v-for="i in 4" :key="i" class="h-3 w-24 bg-muted rounded animate-pulse" />
      </div>
      <div class="flex items-center justify-center h-[260px]">
        <div class="w-44 h-44 rounded-full bg-muted animate-pulse" />
      </div>
    </template>

    <template v-else>
      <!-- Legend -->
      <div class="flex items-center gap-4 mb-4 flex-wrap">
        <span
          v-for="d in distribution"
          :key="d.name"
          class="flex items-center gap-1.5 text-xs text-muted-foreground"
        >
          <span class="w-2.5 h-2.5 rounded-sm flex-shrink-0" :style="{ backgroundColor: SEGMENT_COLORS[d.name] ?? '#94a3b8' }" />
          {{ d.name }} <span class="font-semibold text-foreground">{{ d.percent }}%</span>
        </span>
      </div>

      <!-- SVG Donut Chart -->
      <div class="relative flex items-center justify-center">
        <svg :width="svgSize" :height="svgSize" :viewBox="`0 0 ${svgSize} ${svgSize}`">
          <g :transform="`translate(${svgSize / 2}, ${svgSize / 2})`">
            <!-- Background ring -->
            <circle :r="outerR" fill="none" stroke="hsl(var(--border))" :stroke-width="thickness" />

            <!-- Arcs -->
            <path
              v-for="arc in arcs"
              :key="arc.name"
              :d="arc.d"
              :fill="SEGMENT_COLORS[arc.name] ?? '#94a3b8'"
              class="transition-all duration-500 cursor-pointer hover:opacity-80"
              :title="`${arc.name}: ${arc.value} (${arc.percent}%)`"
              @mouseenter="hovered = arc"
              @mouseleave="hovered = null"
            />
          </g>
        </svg>

        <!-- Center label -->
        <div class="absolute text-center pointer-events-none">
          <transition name="fade" mode="out-in">
            <div v-if="hovered" :key="hovered.name">
              <p class="text-lg font-bold text-foreground">{{ hovered.value }}</p>
              <p class="text-[10px] text-muted-foreground leading-tight">{{ hovered.name }}</p>
              <p class="text-xs font-semibold" :style="{ color: SEGMENT_COLORS[hovered.name] }">{{ hovered.percent }}%</p>
            </div>
            <div v-else key="total">
              <p class="text-2xl font-bold text-foreground">{{ totalLeads }}</p>
              <p class="text-[10px] text-muted-foreground">prospects</p>
            </div>
          </transition>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { SEGMENT_COLORS } from '@/lib/dashboardData'

const props = defineProps({
  distribution: { type: Array,  required: true },
  totalLeads:   { type: Number, required: true },  // always reflects KPI total
  loading:      { type: Boolean, default: false },
})

const svgSize   = 260
const outerR    = 110
const innerR    = 65
const thickness = outerR - innerR
const hovered   = ref(null)

const total = computed(() => props.distribution.reduce((s, d) => s + d.value, 0))

// Build SVG arc paths from distribution percentages
const arcs = computed(() => {
  const gap        = 3   // degrees gap between arcs
  const totalItems = props.distribution.length
  const total      = props.distribution.reduce((s, d) => s + d.value, 0)
  if (!total) return []

  let currentAngle = -90 // start at top

  return props.distribution.map((d) => {
    const pct          = d.value / total
    const sweepDeg     = pct * 360 - (totalItems > 1 ? gap : 0)
    const startAngle   = (currentAngle * Math.PI) / 180
    const endAngle     = ((currentAngle + sweepDeg) * Math.PI) / 180
    currentAngle      += pct * 360

    const midR     = (outerR + innerR) / 2
    const x1Outer  = outerR * Math.cos(startAngle)
    const y1Outer  = outerR * Math.sin(startAngle)
    const x2Outer  = outerR * Math.cos(endAngle)
    const y2Outer  = outerR * Math.sin(endAngle)
    const x1Inner  = innerR * Math.cos(endAngle)
    const y1Inner  = innerR * Math.sin(endAngle)
    const x2Inner  = innerR * Math.cos(startAngle)
    const y2Inner  = innerR * Math.sin(startAngle)
    const largeArc = sweepDeg > 180 ? 1 : 0

    const pathD = [
      `M ${x1Outer} ${y1Outer}`,
      `A ${outerR} ${outerR} 0 ${largeArc} 1 ${x2Outer} ${y2Outer}`,
      `L ${x1Inner} ${y1Inner}`,
      `A ${innerR} ${innerR} 0 ${largeArc} 0 ${x2Inner} ${y2Inner}`,
      'Z',
    ].join(' ')

    return { ...d, d: pathD }
  })
})
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.15s ease; }
.fade-enter-from, .fade-leave-to       { opacity: 0; }
</style>
