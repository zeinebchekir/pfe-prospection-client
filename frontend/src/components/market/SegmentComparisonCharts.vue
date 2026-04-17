<template>
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
    <!-- CA Moyen bar chart -->
    <div class="bg-white border border-border rounded-xl p-5 shadow-sm">
      <h3 class="font-semibold text-tacir-darkblue text-sm mb-1">CA moyen par segment</h3>
      <p class="text-xs text-tacir-darkgray mb-3">Chiffre d'affaires moyen (€)</p>
      <v-chart class="h-56" :option="caOption" autoresize />
    </div>

    <!-- Effectif bar chart -->
    <div class="bg-white border border-border rounded-xl p-5 shadow-sm">
      <h3 class="font-semibold text-tacir-darkblue text-sm mb-1">Effectif moyen par segment</h3>
      <p class="text-xs text-tacir-darkgray mb-3">Nombre d'employés (moyenne)</p>
      <v-chart class="h-56" :option="empOption" autoresize />
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import VChart from "vue-echarts";
import { use } from "echarts/core";
import { BarChart } from "echarts/charts";
import { GridComponent, TooltipComponent } from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import { formatRevenue } from "@/services/segmentation.js";

use([BarChart, GridComponent, TooltipComponent, CanvasRenderer]);

const props = defineProps({ segments: { type: Array, default: () => [] } });

const labels  = computed(() => props.segments.map(s => s.label.split(" ").slice(0,2).join(" ")));
const colors  = computed(() => props.segments.map(s => s.color));

const caOption = computed(() => ({
  tooltip: { trigger: "axis", formatter: (p) => `${p[0].name}<br/>${formatRevenue(p[0].value)}` },
  grid:    { left: 8, right: 8, top: 4, bottom: 32, containLabel: true },
  xAxis:   { type: "category", data: labels.value, axisLabel: { fontSize: 10 } },
  yAxis:   { type: "value",    axisLabel: { formatter: v => formatRevenue(v), fontSize: 10 } },
  series:  [{
    type: "bar", barMaxWidth: 32,
    data: props.segments.map((s, i) => ({ value: s.ca_moyen ?? 0, itemStyle: { color: colors.value[i], borderRadius: [4,4,0,0] } })),
  }],
}));

const empOption = computed(() => ({
  tooltip: { trigger: "axis", formatter: (p) => `${p[0].name}<br/>${p[0].value.toLocaleString("fr-FR")} emp.` },
  grid:    { left: 8, right: 8, top: 4, bottom: 32, containLabel: true },
  xAxis:   { type: "category", data: labels.value, axisLabel: { fontSize: 10 } },
  yAxis:   { type: "value",    axisLabel: { fontSize: 10 } },
  series:  [{
    type: "bar", barMaxWidth: 32,
    data: props.segments.map((s, i) => ({ value: s.employes_moyen, itemStyle: { color: colors.value[i], borderRadius: [4,4,0,0] } })),
  }],
}));
</script>
