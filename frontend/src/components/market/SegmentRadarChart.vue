<template>
  <div class="bg-white border border-border rounded-xl p-5 shadow-sm">
    <div class="flex items-start justify-between mb-3 flex-wrap gap-3">
      <div>
        <h3 class="font-semibold text-tacir-darkblue text-sm">Comparaison multidimensionnelle</h3>
        <p class="text-xs text-tacir-darkgray">Sélectionnez jusqu'à 3 segments</p>
      </div>
      <div class="flex flex-wrap gap-1.5">
        <button
          v-for="s in segments"
          :key="s.cluster"
          @click="toggle(s.cluster)"
          class="text-[11px] px-2.5 py-1 rounded-full border transition-all"
          :style="
            selected.includes(s.cluster)
              ? { backgroundColor: s.color, color: '#fff', borderColor: s.color }
              : { backgroundColor: 'transparent', color: '#666', borderColor: '#ddd' }
          "
        >
          {{ shortLabel(s) }}
        </button>
      </div>
    </div>
    <div v-if="ready" class="w-full">
      <apexchart
        type="radar"
        height="280"
        :options="radarOptions"
        :series="radarSeries"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import VueApexCharts from "vue3-apexcharts";
const apexchart = VueApexCharts;

const props = defineProps({ segments: { type: Array, default: () => [] } });

const selected = ref([]);

// initialise with first 3 clusters when segments load
function initSelected() {
  if (selected.value.length === 0 && props.segments.length) {
    selected.value = props.segments.slice(0, 3).map(s => s.cluster);
  }
}

function toggle(c) {
  if (selected.value.includes(c)) {
    selected.value = selected.value.filter(x => x !== c);
  } else if (selected.value.length < 3) {
    selected.value = [...selected.value, c];
  } else {
    selected.value = [...selected.value.slice(1), c];
  }
}

function shortLabel(s) {
  return s.label.split(" ").slice(0, 2).join(" ");
}

const activeSegs = computed(() => {
  initSelected();
  return props.segments.filter(s => selected.value.includes(s.cluster));
});

const ready = computed(() => props.segments.length > 0);

const maxEmp = computed(() => Math.max(...props.segments.map(s => s.employes_moyen), 1));
const maxCA  = computed(() => Math.max(...props.segments.map(s => s.ca_moyen ?? 0), 1));
const maxAge = computed(() => Math.max(...props.segments.map(s => s.age_moyen), 1));
const maxLoc = computed(() => Math.max(...props.segments.map(s => s.nb_locaux_moyen ?? 0), 1));

const radarSeries = computed(() =>
  activeSegs.value.map(s => ({
    name: shortLabel(s),
    data: [
      Math.round((s.employes_moyen / maxEmp.value) * 100),
      Math.round(((s.ca_moyen ?? 0) / maxCA.value) * 100),
      Math.round((s.age_moyen / maxAge.value) * 100),
      Math.round(((s.nb_locaux_moyen ?? 0) / maxLoc.value) * 100),
      s.region_dominante === "Ile-de-France" ? 90 : 50,
    ],
  }))
);

const radarOptions = computed(() => ({
  chart: {
    toolbar: { show: false },
    parentHeightOffset: 0,
  },
  xaxis: {
    categories: ["Taille", "Valeur CA", "Ancienneté", "Multi-sites", "Concentr. géo"],
  },
  yaxis: { show: false, min: 0, max: 100 },
  colors: activeSegs.value.map(s => s.color),
  markers: { size: 4 },
  fill: { opacity: 0.15 },
  stroke: { width: 2 },
  legend: {
    show: true,
    position: "bottom",
    fontSize: "11px",
    markers: { size: 6, strokeWidth: 0 },
  },
  plotOptions: {
    radar: {
      polygons: {
        strokeColors: "#e5e7eb",
        fill: { colors: ["#f9fafb", "#ffffff"] },
      },
    },
  },
  dataLabels: { enabled: false },
  tooltip: { y: { formatter: val => `${val}%` } },
}));
</script>
