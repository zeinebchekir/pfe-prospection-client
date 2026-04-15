<template>
  <Card class="border-border shadow-sm rounded-2xl bg-white p-4 w-full h-full">
    <h4 class="text-[10px] font-bold text-tacir-darkgray mb-4 uppercase tracking-widest flex items-center gap-2">
      <Database class="w-3.5 h-3.5 text-tacir-blue" />
      Volume de Données Traitées
    </h4>

    <div v-if="loading" class="h-[250px] flex items-center justify-center text-xs text-slate-400">
      Chargement...
    </div>
    <div v-else-if="error" class="h-[250px] flex items-center justify-center text-xs text-red-400">
      Erreur : {{ error }}
    </div>
    <VueApexCharts
      v-else
      type="area"
      height="250"
      :options="chartOptions"
      :series="series"
    />
  </Card>
</template>

<script setup>
import { computed } from 'vue'
import VueApexCharts from 'vue3-apexcharts'
import { Card } from '@/components/ui/card'
import { Database } from 'lucide-vue-next'
import { useMonitoringETL } from '@/composables/usePipeline'

const { volumeOverTime, loading, error } = useMonitoringETL()

/*
  L'API retourne : [{ date, dag_id, records_processed }, ...]
  On doit pivoter par dag_id pour avoir une série par source.
*/
const pivoted = computed(() => {
  const dates   = [...new Set(volumeOverTime.value.map(r => r.date))].sort()
  const dagIds  = [...new Set(volumeOverTime.value.map(r => r.dag_id))]

  // Index rapide : "date|dag_id" → records_processed
  const idx = {}
  volumeOverTime.value.forEach(r => { idx[`${r.date}|${r.dag_id}`] = r.records_processed })

  const seriesList = dagIds.map(dagId => ({
    name: dagId,
    data: dates.map(date => idx[`${date}|${dagId}`] ?? 0)
  }))

  return { dates, seriesList }
})

const series = computed(() => pivoted.value.seriesList)

const COLORS = ['#1a365d', '#3b82f6', '#059669', '#f59e0b', '#dc2626']

const chartOptions = computed(() => ({
  chart: {
    type: 'area',
    toolbar: { show: false },
    fontFamily: 'inherit'
  },
  colors: COLORS,
  fill: {
    type: 'gradient',
    gradient: { shadeIntensity: 1, opacityFrom: 0.7, opacityTo: 0.1, stops: [0, 90, 100] }
  },
  dataLabels: { enabled: false },
  stroke: { curve: 'smooth', width: 3 },
  xaxis: {
    categories: pivoted.value.dates,
    labels: { style: { colors: '#94a3b8' } }
  },
  yaxis: {
    labels: {
      formatter: val => val >= 1000 ? (val / 1000).toFixed(1) + 'k' : val,
      style: { fontWeight: 600, colors: '#64748b' }
    }
  },
  legend: { position: 'top' },
  tooltip: {
    y: { formatter: val => `${val} lignes` }
  }
}))
</script>