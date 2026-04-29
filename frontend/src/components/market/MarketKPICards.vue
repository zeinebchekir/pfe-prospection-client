<template>
  <div class="flex items-center gap-2 flex-wrap">
    <div
      v-for="kpi in kpis"
      :key="kpi.label"
      class="flex-1 min-w-[140px] bg-white border border-border rounded-xl px-4 py-3 shadow-sm"
    >
      <p class="text-[10px] font-semibold uppercase tracking-widest text-tacir-darkgray mb-1">
        {{ kpi.label }}
      </p>
      <p class="text-xl font-bold text-tacir-darkblue leading-none">{{ kpi.value }}</p>
      <p v-if="kpi.sub" class="text-[11px] text-tacir-darkgray mt-0.5">{{ kpi.sub }}</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { formatRevenue } from "@/services/segmentation.js";

const props = defineProps({
  segments: { type: Array, default: () => [] },
  totalLeads: { type: Number, default: 0 },
});

const kpis = computed(() => {
  const segs = props.segments;
  if (!segs.length) return [];

  const dominant  = [...segs].sort((a, b) => b.n - a.n)[0];
  const totalN    = segs.reduce((s, x) => s + x.n, 0);
  const weightedCA = segs.reduce((s, x) => s + (x.ca_moyen || 0) * x.n, 0) / totalN;
  const weightedAge = segs.reduce((s, x) => s + x.age_moyen * x.n, 0) / totalN;
  const priority  = [...segs].sort((a, b) => (b.ca_moyen || 0) * b.n - (a.ca_moyen || 0) * a.n)[0];

  return [
    { label: "Total leads",        value: props.totalLeads.toLocaleString("fr-FR"), sub: "entreprises segmentées" },
    { label: "Segments",           value: segs.length,                              sub: "segments identifiÃ©s" },
    { label: "Segment dominant",   value: dominant?.label?.split(" ")[0] + "…",     sub: `${dominant?.n} leads (${Math.round(dominant?.n / totalN * 100)}%)` },
    { label: "CA moyen pondéré",   value: formatRevenue(Math.round(weightedCA)),    sub: "chiffre d'affaires" },
    { label: "Âge moyen",          value: `${weightedAge.toFixed(1)} ans`,          sub: "ancienneté des entreprises" },
    { label: "Priorité CA",        value: priority?.label?.split(" ")[0] + "…",     sub: priority?.recommendation },
  ];
});
</script>
