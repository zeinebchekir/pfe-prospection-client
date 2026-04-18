<template>
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
    <!-- CA Moyen bar chart -->
    <div class="bg-white border border-border rounded-xl p-5 shadow-sm">
      <h3 class="font-semibold text-tacir-darkblue text-sm mb-1">CA moyen par segment</h3>
      <p class="text-xs text-tacir-darkgray mb-3">Chiffre d'affaires moyen (€)</p>
      <div v-if="ready" class="w-full">
        <apexchart
          type="bar"
          height="220"
          :options="caOptions"
          :series="caSeries"
        />
      </div>
    </div>

    <!-- Effectif moyen bar chart -->
    <div class="bg-white border border-border rounded-xl p-5 shadow-sm">
      <h3 class="font-semibold text-tacir-darkblue text-sm mb-1">Effectif moyen par segment</h3>
      <p class="text-xs text-tacir-darkgray mb-3">Nombre d'employés (moyenne)</p>
      <div v-if="ready" class="w-full">
        <apexchart
          type="bar"
          height="220"
          :options="empOptions"
          :series="empSeries"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import VueApexCharts from "vue3-apexcharts";
const apexchart = VueApexCharts;

const props = defineProps({ segments: { type: Array, default: () => [] } });

const ready = computed(() => props.segments.length > 0);

const labels = computed(() => props.segments.map(s => s.label.split(" ").slice(0, 2).join(" ")));
const colors = computed(() => props.segments.map(s => s.color));

function formatRevenue(v) {
  if (v == null || isNaN(v)) return "0";
  if (v >= 1e9) return `${(v / 1e9).toFixed(1)} Md€`;
  if (v >= 1e6) return `${(v / 1e6).toFixed(1)} M€`;
  if (v >= 1e3) return `${(v / 1e3).toFixed(0)} k€`;
  return `${v.toFixed(0)} €`;
}

const baseBarOptions = computed(() => ({
  chart: {
    toolbar: { show: false },
    animations: { enabled: true },
    parentHeightOffset: 0,
  },
  plotOptions: {
    bar: {
      borderRadius: 4,
      distributed: true,
      columnWidth: "55%",
    },
  },
  dataLabels: { enabled: false },
  legend: { show: false },
  xaxis: {
    categories: labels.value,
    labels: {
      style: { fontSize: "11px", colors: "#6b7280" },
      trim: true,
      maxHeight: 60,
    },
    axisBorder: { show: false },
    axisTicks: { show: false },
  },
  yaxis: {
    labels: { style: { fontSize: "10px", colors: "#6b7280" } },
  },
  grid: {
    borderColor: "#f3f4f6",
    strokeDashArray: 4,
    padding: { top: 0, right: 8, bottom: 0, left: 8 },
  },
  tooltip: { shared: false, intersect: true },
  colors: colors.value,
}));

const caOptions = computed(() => ({
  ...baseBarOptions.value,
  yaxis: {
    labels: {
      style: { fontSize: "10px", colors: "#6b7280" },
      formatter: val => formatRevenue(val),
    },
  },
  tooltip: {
    y: { formatter: val => formatRevenue(val) },
  },
}));

const caSeries = computed(() => [{
  name: "CA moyen",
  data: props.segments.map(s => Math.round(s.ca_moyen ?? 0)),
}]);

const empOptions = computed(() => ({
  ...baseBarOptions.value,
  tooltip: {
    y: { formatter: val => `${val.toLocaleString("fr-FR")} emp.` },
  },
}));

const empSeries = computed(() => [{
  name: "Effectif moyen",
  data: props.segments.map(s => s.employes_moyen ?? 0),
}]);
</script>
