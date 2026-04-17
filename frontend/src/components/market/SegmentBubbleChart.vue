<template>
  <div class="relative w-full" style="aspect-ratio: 16/9">
    <!-- SVG bubbles -->
    <svg viewBox="0 0 100 56" class="w-full h-full" preserveAspectRatio="xMidYMid meet">
      <g v-for="b in bubbles" :key="b.cluster">
        <circle
          :cx="b.cx" :cy="b.cy * 0.56" :r="b.r"
          :fill="b.color" fill-opacity="0.18"
          :stroke="b.color" stroke-width="0.3"
        />
        <circle :cx="b.cx" :cy="b.cy * 0.56" :r="b.r * 0.5" :fill="b.color" fill-opacity="0.35" />
      </g>
    </svg>
    <!-- Text overlay -->
    <div class="absolute inset-0 pointer-events-none">
      <div
        v-for="b in bubbles"
        :key="b.cluster"
        class="absolute -translate-x-1/2 -translate-y-1/2 text-center"
        :style="{ left: `${b.cx}%`, top: `${(b.cy * 0.56 / 56) * 100}%`, maxWidth: `${b.r * 2.2}%` }"
      >
        <div class="text-[11px] font-semibold leading-tight" :style="{ color: b.color }">{{ b.shortName }}</div>
        <div class="text-[10px] font-bold text-gray-800 mt-0.5">{{ b.percent }}%</div>
        <div class="text-[9px] text-gray-500">{{ b.n }} leads</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { SEGMENT_META } from "@/services/segmentation.js";

const POSITIONS = [
  { x: 50, y: 50 }, { x: 22, y: 38 }, { x: 78, y: 40 }, { x: 32, y: 75 }, { x: 72, y: 75 },
];

const props = defineProps({
  segments:   { type: Array,  default: () => [] },
  totalLeads: { type: Number, default: 0 },
});

const bubbles = computed(() => {
  const sorted   = [...props.segments].sort((a, b) => b.n - a.n);
  const maxCount = sorted[0]?.n ?? 1;
  return sorted.map((s, i) => {
    const ratio = s.n / maxCount;
    return {
      ...s,
      shortName: SEGMENT_META[s.cluster]?.shortName || s.label,
      cx:        POSITIONS[i]?.x ?? 50,
      cy:        POSITIONS[i]?.y ?? 50,
      r:         6 + ratio * 12,
      percent:   Math.round((s.n / props.totalLeads) * 100),
    };
  });
});
</script>
