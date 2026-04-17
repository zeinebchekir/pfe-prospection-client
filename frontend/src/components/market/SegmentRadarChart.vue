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
          :style="selected.includes(s.cluster)
            ? { backgroundColor: s.color, color: '#fff', border: `1px solid ${s.color}` }
            : { backgroundColor: 'transparent', color: '#666', border: '1px solid #ddd' }"
        >
          {{ shortLabel(s) }}
        </button>
      </div>
    </div>
    <v-chart class="h-72" :option="radarOption" autoresize />
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import VChart from "vue-echarts";
import { use } from "echarts/core";
import { RadarChart } from "echarts/charts";
import { RadarComponent, TooltipComponent, LegendComponent } from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";

use([RadarChart, RadarComponent, TooltipComponent, LegendComponent, CanvasRenderer]);

const props = defineProps({ segments: { type: Array, default: () => [] } });

const selected = ref(props.segments.slice(0, 3).map(s => s.cluster));

function toggle(c) {
  if (selected.value.includes(c)) { selected.value = selected.value.filter(x => x !== c); }
  else if (selected.value.length < 3) { selected.value = [...selected.value, c]; }
  else { selected.value = [...selected.value.slice(1), c]; }
}

function shortLabel(s) { return s.label.split(" ").slice(0, 2).join(" "); }

const activeSegs = computed(() => props.segments.filter(s => selected.value.includes(s.cluster)));

const radarOption = computed(() => {
  const segs = activeSegs.value;
  if (!segs.length) return {};

  const maxEmp = Math.max(...segs.map(s => s.employes_moyen), 1);
  const maxCA  = Math.max(...segs.map(s => s.ca_moyen || 0), 1);
  const maxAge = Math.max(...segs.map(s => s.age_moyen), 1);
  const maxLoc = Math.max(...segs.map(s => s.nb_locaux_moyen || 0), 1);

  return {
    tooltip: {},
    legend:  { bottom: 0, textStyle: { fontSize: 11 } },
    radar:   {
      indicator: [
        { name: "Taille", max: 100 }, { name: "Valeur CA", max: 100 },
        { name: "Ancienneté", max: 100 }, { name: "Multi-sites", max: 100 },
        { name: "Concentr. géo", max: 100 },
      ],
      radius: "65%",
    },
    series: [{
      type: "radar",
      data: segs.map(s => ({
        name: shortLabel(s),
        value: [
          Math.round((s.employes_moyen / maxEmp) * 100),
          Math.round(((s.ca_moyen || 0) / maxCA) * 100),
          Math.round((s.age_moyen / maxAge) * 100),
          Math.round(((s.nb_locaux_moyen || 0) / maxLoc) * 100),
          s.region_dominante === "Ile-de-France" ? 90 : 50,
        ],
        lineStyle: { color: s.color, width: 2 },
        areaStyle: { color: s.color, opacity: 0.12 },
        itemStyle: { color: s.color },
      })),
    }],
  };
});
</script>
