<template>
  <Card class="border-border shadow-sm rounded-2xl bg-white p-4 w-full h-full">
    <h4 class="text-[10px] font-bold text-tacir-darkgray mb-4 uppercase tracking-widest flex items-center gap-2">
      <AlertTriangle class="w-3.5 h-3.5 text-tacir-blue" />
      Qualité JSON (BOAMP)
    </h4>

    <div v-if="loading" class="h-[250px] flex items-center justify-center text-xs text-slate-400">
      Chargement...
    </div>
    <div v-else-if="error" class="h-[250px] flex items-center justify-center text-xs text-red-400">
      Erreur : {{ error }}
    </div>
    <div v-else class="h-[250px] flex items-center justify-center">
      <VueApexCharts
        type="bar"
        width="100%"
        height="250"
        :options="chartOptions"
        :series="series"
      />
    </div>
  </Card>
</template>

<script setup>
import { computed } from 'vue'
import VueApexCharts from 'vue3-apexcharts'
import { Card } from '@/components/ui/card'
import { AlertTriangle } from 'lucide-vue-next'
import { useMonitoringETL } from '@/composables/usePipeline'

const { dataQualityBoamp, loading, error } = useMonitoringETL()

// Dynamic color computation
function colorForRate(rate) {
  if (rate >= 90) return '#059669' // Green (success)
  if (rate >= 70) return '#f59e0b' // Amber (warning)
  return '#dc2626'                 // Red (critical)
}

const series = computed(() => [{
  name: 'Taux (Complétude)',
  data: (dataQualityBoamp.value || []).map(d => ({
    x: d.field_name.replace('boamp_', ''), // Clean naming
    y: d.fill_rate,
    fillColor: colorForRate(d.fill_rate)
  }))
}])

const chartOptions = computed(() => ({
  chart: {
    type: 'bar',
    toolbar: { show: false },
    fontFamily: 'inherit'
  },
  plotOptions: {
    bar: {
      horizontal: true,
      borderRadius: 4,
      distributed: true,
    }
  },
  dataLabels: {
    enabled: true,
    textAnchor: 'start',
    style: { colors: ['#fff'], fontSize: '10px' },
    formatter: function (val, opt) {
      return val + "%"
    },
    offsetX: 10
  },
  xaxis: {
    max: 100,
    labels: { style: { colors: '#94a3b8' } }
  },
  yaxis: {
    labels: { style: { fontWeight: 600, colors: '#475569' } }
  },
  legend: { show: false },
  tooltip: {
    y: {
      formatter: (val) => `${val}%`
    }
  }
}))
</script>
