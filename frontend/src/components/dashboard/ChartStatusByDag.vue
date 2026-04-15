<template>
  <Card class="border-border shadow-sm rounded-2xl bg-white p-4 w-full h-full">
    <h4 class="text-[10px] font-bold text-tacir-darkgray mb-4 uppercase tracking-widest flex items-center gap-2">
      <CheckCircle2 class="w-3.5 h-3.5 text-tacir-blue" />
      Status des Runs (Derniers 30 Jours)
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
import { CheckCircle2 } from 'lucide-vue-next'
import { useMonitoringETL } from '@/composables/usePipeline'

const { dagSuccess, loading, error } = useMonitoringETL()

// Transforme le tableau d'objets API en séries ApexCharts
const series = computed(() => [
  {
    name: 'Succès',
    data: dagSuccess.value.map(d => d.success)
  },
  {
    name: 'Échecs',
    data: dagSuccess.value.map(d => d.failed)
  },
  {
    name: 'Retry',
    data: dagSuccess.value.map(d => d.up_for_retry)
  }
])

const chartOptions = computed(() => ({
  chart: {
    type: 'bar',
    stacked: true,
    toolbar: { show: false },
    fontFamily: 'inherit'
  },
  plotOptions: {
    bar: {
      horizontal: false,
      borderRadius: 4,
      columnWidth: '40%'
    }
  },
  colors: ['#059669', '#dc2626', '#f59e0b'],
  xaxis: {
    categories: dagSuccess.value.map(d => d.dag_id),
    labels: {
      style: { fontWeight: 600, colors: '#64748b' }
    }
  },
  dataLabels: {
    enabled: true,
    style: { colors: ['#fff'], fontSize: '10px' }
  },
  legend: { position: 'top', markers: { radius: 12 } },
  stroke: { width: 0 },
  tooltip: {
    y: {
      formatter: (val, { seriesIndex, dataPointIndex }) => {
        const row = dagSuccess.value[dataPointIndex]
        if (!row) return val
        const pct = row.total > 0 ? ((val / row.total) * 100).toFixed(1) : 0
        return `${val} runs (${pct}%)`
      }
    }
  }
}))
</script>