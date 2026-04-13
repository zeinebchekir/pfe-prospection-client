<template>
  <div class="rounded-xl border border-border bg-card p-5">
    <h3 class="text-sm font-semibold text-foreground mb-1">CA moyen par segment</h3>
    <p class="text-[11px] text-muted-foreground mb-4">Comparaison CA moyen vs CA médian (€)</p>

    <!-- Legend -->
    <div class="flex items-center gap-4 mb-4 text-xs text-muted-foreground">
      <span class="flex items-center gap-1.5">
        <span class="w-2.5 h-2.5 rounded-sm bg-tacir-blue" />
        CA moyen
      </span>
      <span class="flex items-center gap-1.5">
        <span class="w-2.5 h-2.5 rounded-sm bg-emerald-500" />
        CA médian
      </span>
    </div>

    <!-- Skeleton -->
    <template v-if="loading">
      <div class="flex items-end justify-around gap-4 h-[200px] px-2">
        <div v-for="i in 4" :key="i" class="flex-1 flex gap-1 items-end">
          <div class="flex-1 rounded-t-md bg-muted animate-pulse" :style="{ height: `${50 + i*25}px` }" />
          <div class="flex-1 rounded-t-md bg-muted/60 animate-pulse" :style="{ height: `${35 + i*18}px` }" />
        </div>
      </div>
    </template>

    <template v-else>
      <!-- SVG Bar Chart -->
      <div class="relative">
        <!-- Y-axis labels -->
        <div class="absolute left-0 top-0 bottom-6 flex flex-col justify-between pr-2 text-right">
          <span v-for="tick in yTicks" :key="tick" class="text-[9px] text-muted-foreground leading-none">
            {{ tick }}
          </span>
        </div>

        <!-- Chart area -->
        <div class="ml-12">
          <svg
            :width="'100%'"
            :viewBox="`0 0 ${chartW} ${chartH}`"
            preserveAspectRatio="none"
            class="overflow-visible"
          >
            <!-- Grid lines -->
            <line
              v-for="(tick, i) in yTicks"
              :key="i"
              x1="0" :y1="yScale(yValues[i])"
              :x2="chartW" :y2="yScale(yValues[i])"
              stroke="hsl(var(--border))"
              stroke-dasharray="3 3"
              stroke-width="0.5"
            />

            <!-- Bar groups -->
            <g v-for="(seg, i) in segments" :key="seg.name">
              <!-- CA moyen -->
              <rect
                :x="groupX(i)"
                :y="yScale(seg.caMoyenRaw)"
                :width="barW"
                :height="chartH - yScale(seg.caMoyenRaw)"
                fill="hsl(234 50% 37%)"
                rx="3"
                class="transition-all duration-500 cursor-pointer hover:opacity-80"
                @mouseenter="hoveredBar = { label: seg.name, caM: seg.caMoyen, type: 'moyen' }"
                @mouseleave="hoveredBar = null"
              />
              <!-- CA médian -->
              <rect
                :x="groupX(i) + barW + barGap"
                :y="yScale(seg.caMedianRaw)"
                :width="barW"
                :height="chartH - yScale(seg.caMedianRaw)"
                fill="#56A632"
                rx="3"
                class="transition-all duration-500 cursor-pointer hover:opacity-80"
                @mouseenter="hoveredBar = { label: seg.name, caM: formatCAVal(seg.caMedianRaw), type: 'médian' }"
                @mouseleave="hoveredBar = null"
              />
              <!-- X label -->
              <text
                :x="groupX(i) + barW + barGap / 2"
                :y="chartH + 14"
                text-anchor="middle"
                class="text-[9px] fill-muted-foreground"
                font-size="9"
              >
                {{ seg.name.replace('Microentreprise', 'Micro').replace('Grande Entreprise', 'GE') }}
              </text>
            </g>
          </svg>
        </div>
      </div>

      <!-- Tooltip -->
      <transition name="fade">
        <div
          v-if="hoveredBar"
          class="mt-3 px-3 py-2 rounded-lg border border-border bg-muted/50 text-xs text-foreground flex items-center gap-2"
        >
          <span class="font-semibold">{{ hoveredBar.label }}</span>
          <span class="text-muted-foreground">—</span>
          <span>CA {{ hoveredBar.type }} : <strong>{{ hoveredBar.caM }}</strong></span>
        </div>
      </transition>
    </template>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { formatCA } from '@/lib/leadAdapter'

const props = defineProps({
  segments: { type: Array, required: true },
  loading:  { type: Boolean, default: false },
})

const hoveredBar = ref(null)
const formatCAVal = (v) => formatCA(v)

const chartW  = 400
const chartH  = 200
const groupW  = chartW / (props.segments.length || 1)
const barW    = Math.min(28, groupW * 0.35)
const barGap  = 4

function groupX(i) {
  return i * groupW + (groupW - 2 * barW - barGap) / 2
}

// Y scale
const maxCA = computed(() =>
  Math.max(...props.segments.flatMap((s) => [s.caMoyenRaw, s.caMedianRaw]), 1)
)

function yScale(val) {
  return chartH - (val / maxCA.value) * (chartH - 10)
}

const Y_TICK_COUNT = 4
const yValues = computed(() =>
  Array.from({ length: Y_TICK_COUNT + 1 }, (_, i) =>
    Math.round((maxCA.value / Y_TICK_COUNT) * (Y_TICK_COUNT - i))
  )
)
const yTicks = computed(() => yValues.value.map((v) => formatCA(v)))
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.15s ease; }
.fade-enter-from, .fade-leave-to       { opacity: 0; }
</style>
