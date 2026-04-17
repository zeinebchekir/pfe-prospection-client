<template>
  <div class="bg-white border border-border rounded-xl p-5 shadow-sm">
    <h3 class="font-semibold text-tacir-darkblue text-sm mb-1">Matrice Opportunités</h3>
    <p class="text-xs text-tacir-darkgray mb-3">Volume (leads) × Valeur économique (CA moyen)</p>
    <v-chart class="h-72" :option="scatterOption" autoresize />
  </div>
</template>

<script setup>
import { computed } from "vue";
import VChart from "vue-echarts";
import { use } from "echarts/core";
import { ScatterChart } from "echarts/charts";
import { GridComponent, TooltipComponent, LegendComponent } from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import { formatRevenue } from "@/services/segmentation.js";

use([ScatterChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer]);

const props = defineProps({ segments: { type: Array, default: () => [] } });

const scatterOption = computed(() => ({
  tooltip: {
    trigger: "item",
    formatter: (p) => {
      const s = props.segments[p.seriesIndex];
      return `<b>${s.label}</b><br/>Leads: ${s.n}<br/>CA moy: ${formatRevenue(s.ca_moyen)}<br/>Âge: ${s.age_moyen} ans`;
    },
  },
  legend: { bottom: 0, textStyle: { fontSize: 10 } },
  grid:   { left: 32, right: 16, top: 8, bottom: 48, containLabel: true },
  xAxis:  { type: "value", name: "Volume (leads)", nameTextStyle: { fontSize: 10 } },
  yAxis:  { type: "value", name: "CA moyen (€)",   nameTextStyle: { fontSize: 10 },
            axisLabel: { formatter: v => formatRevenue(v) } },
  series: props.segments.map(s => ({
    name: s.label.split(" ").slice(0,2).join(" "),
    type: "scatter",
    symbolSize: 30 + (s.n / Math.max(...props.segments.map(x => x.n))) * 40,
    data:        [[s.n, s.ca_moyen ?? 0]],
    itemStyle:   { color: s.color, opacity: 0.85 },
    label:       { show: true, formatter: s.label.split(" ")[0], position: "top", fontSize: 10 },
  })),
}));
</script>
