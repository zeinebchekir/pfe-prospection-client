<template>
  <Card class="border-border shadow-sm rounded-2xl bg-white p-4 w-full h-full">
    <h4 class="text-[10px] font-bold text-tacir-darkgray mb-4 uppercase tracking-widest flex items-center gap-2">
      <Timer class="w-3.5 h-3.5 text-tacir-blue" />
      Durée Moyenne par Tâche (Goulots)
    </h4>

    <div v-if="loading" class="h-[250px] flex items-center justify-center text-xs text-slate-400">
      Chargement...
    </div>
    <div v-else-if="error" class="h-[250px] flex items-center justify-center text-xs text-red-400">
      Erreur : {{ error }}
    </div>
    <VueApexCharts
      v-else
      type="bar"
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
import { Timer } from 'lucide-vue-next'
import { useMonitoringETL } from '@/composables/usePipeline'

const ALERT_THRESHOLD = 120

const { taskDuration, loading, error } = useMonitoringETL()

const series = computed(() => [{
  name: 'Durée (secondes)',
  data: taskDuration.value.map(d => ({
    x: d.task_id,
    y: d.avg_duration_sec
  }))
}])

const chartOptions = computed(() => ({
  chart: {
    type: 'bar',
    toolbar: { show: false },
    fontFamily: 'inherit'
  },
  plotOptions: {
    bar: { horizontal: true, borderRadius: 4 }
  },
  colors: [
    function ({ value }) {
      return value > ALERT_THRESHOLD ? '#dc2626' : '#3b82f6'
    }
  ],
  annotations: {
    xaxis: [{
      x: ALERT_THRESHOLD,
      borderColor: '#f59e0b',
      strokeDashArray: 4,
      label: {
        text: "Seuil d'Alerte (120s)",
        style: { color: '#fff', background: '#f59e0b', fontSize: '10px' }
      }
    }]
  },
  dataLabels: {
    enabled: true,
    formatter: val => `${val}s`
  },
  xaxis: {
    labels: { style: { colors: '#94a3b8' } }
  },
  yaxis: {
    labels: { style: { fontWeight: 600, colors: '#475569' } }
  },
  tooltip: {
    y: {
      formatter: (val, { dataPointIndex }) => {
        const row = taskDuration.value[dataPointIndex]
        return row ? `moy: ${val}s  |  max: ${row.max_duration_sec}s` : `${val}s`
      }
    }
  }
}))
</script>