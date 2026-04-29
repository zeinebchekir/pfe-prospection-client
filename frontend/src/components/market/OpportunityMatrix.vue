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
import { formatRevenue } from "@/services/segmentation.js";

const apexchart = VueApexCharts;

const props = defineProps({ segments: { type: Array, default: () => [] } });

const ready = computed(() => props.segments.length > 0);

const scatterSeries = computed(() =>
  props.segments.map((s) => ({
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
  colors: props.segments.map((s) => s.color),
  markers: {
    size: props.segments.map((s) => {
      const max = Math.max(...props.segments.map((x) => x.n), 1);
      return 8 + Math.round((s.n / max) * 20);
    }),
    strokeWidth: props.segments.map((s) => {
      const gap = s.digital_gap ?? 5;
      if (gap >= 7) return 4;
      if (gap >= 4) return 2;
      return 1;
    }),
    strokeColors: props.segments.map((s) => {
      const gap = s.digital_gap ?? 5;
      if (gap >= 7) return "#F29F05";
      if (gap >= 4) return "#04ADBF";
      return "#56A632";
    }),
    fillOpacity: 0.82,
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
      formatter: (val) => formatRevenue(val),
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

      const gap = s.digital_gap ?? null;
      const matScore = s.digital_maturity_score ?? null;
      const matLevel = s.digital_maturity_level ?? null;
      const gapColor =
        gap == null ? "#9ca3af" : gap >= 7 ? "#F29F05" : gap >= 4 ? "#04ADBF" : "#56A632";
      const matHTML =
        matScore != null
          ? `<div style="margin-top:4px;padding-top:4px;border-top:1px solid #f3f4f6">
               Maturité: <b style="color:${s.color}">${matScore.toFixed(1)}/10</b>
               &nbsp;·&nbsp;
               Écart: <b style="color:${gapColor}">${gap?.toFixed(1) ?? "—"}</b>
               <span style="color:${gapColor};margin-left:4px">${
                 matLevel === "Élevé"
                   ? "↑ Déjà mature"
                   : gap >= 7
                     ? "● Fort potentiel"
                     : gap >= 4
                       ? "○ Potentiel modéré"
                       : "↓ Faible écart"
               }</span>
             </div>`
          : "";

      return `
        <div style="padding:8px 12px;font-size:12px;line-height:1.6">
          <b style="color:${s.color}">${s.label}</b><br/>
          Leads: <b>${s.n}</b><br/>
          CA moy: <b>${formatRevenue(s.ca_moyen)}</b><br/>
          Âge: <b>${s.age_moyen} ans</b>
          ${matHTML}
        </div>`;
    },
  },
}));
</script>
