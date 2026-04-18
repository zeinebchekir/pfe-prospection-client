<template>
  <div class="bg-white border border-border rounded-xl p-5 shadow-sm">
    <h3 class="font-semibold text-tacir-darkblue text-sm mb-1">Matrice Opportunités</h3>
    <p class="text-xs text-tacir-darkgray mb-3">Volume (leads) × Valeur économique (CA moyen)</p>
    <div v-if="ready" class="w-full">
      <apexchart
        type="scatter"
        height="280"
        :options="scatterOptions"
        :series="scatterSeries"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import VueApexCharts from "vue3-apexcharts";
const apexchart = VueApexCharts;

const props = defineProps({ segments: { type: Array, default: () => [] } });

const ready = computed(() => props.segments.length > 0);

function formatRevenue(v) {
  if (v == null || isNaN(v)) return "0";
  if (v >= 1e9) return `${(v / 1e9).toFixed(1)} Md€`;
  if (v >= 1e6) return `${(v / 1e6).toFixed(1)} M€`;
  if (v >= 1e3) return `${(v / 1e3).toFixed(0)} k€`;
  return `${v.toFixed(0)} €`;
}

// ApexCharts scatter needs one series per point to get individual colors
const scatterSeries = computed(() =>
  props.segments.map(s => ({
    name: s.label.split(" ").slice(0, 2).join(" "),
    data: [[s.n, s.ca_moyen ?? 0]],
  }))
);

const scatterOptions = computed(() => ({
  chart: {
    toolbar: { show: false },
    zoom: { enabled: false },
    parentHeightOffset: 0,
  },
  colors: props.segments.map(s => s.color),
  markers: {
    size: props.segments.map(s => {
      const max = Math.max(...props.segments.map(x => x.n), 1);
      return 8 + Math.round((s.n / max) * 20);
    }),
    strokeWidth: 0,
    fillOpacity: 0.85,
  },
  xaxis: {
    title: {
      text: "Volume (leads)",
      style: { fontSize: "11px", color: "#6b7280" },
    },
    labels: { style: { fontSize: "10px", colors: "#6b7280" } },
    tickAmount: 5,
  },
  yaxis: {
    title: {
      text: "CA moyen",
      style: { fontSize: "11px", color: "#6b7280" },
    },
    labels: {
      style: { fontSize: "10px", colors: "#6b7280" },
      formatter: val => formatRevenue(val),
    },
  },
  dataLabels: {
    enabled: true,
    formatter: (val, opts) =>
      props.segments[opts.seriesIndex]?.label.split(" ")[0] ?? "",
    style: { fontSize: "10px", colors: ["#374151"] },
    offsetY: -10,
    background: { enabled: false },
  },
  legend: {
    show: true,
    position: "bottom",
    fontSize: "10px",
    markers: { size: 6 },
  },
  grid: {
    borderColor: "#f3f4f6",
    strokeDashArray: 4,
  },
  tooltip: {
    custom: ({ seriesIndex }) => {
      const s = props.segments[seriesIndex];
      if (!s) return "";
      return `
        <div style="padding:8px 12px;font-size:12px;line-height:1.6">
          <b style="color:${s.color}">${s.label}</b><br/>
          Leads: <b>${s.n}</b><br/>
          CA moy: <b>${formatRevenue(s.ca_moyen)}</b><br/>
          Âge: <b>${s.age_moyen} ans</b>
        </div>`;
    },
  },
}));
</script>
