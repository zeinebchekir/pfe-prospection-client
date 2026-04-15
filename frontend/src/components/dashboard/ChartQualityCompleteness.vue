<template>
  <Card class="border-border shadow-sm rounded-2xl bg-white p-4 w-full h-full">
    <h4 class="text-[10px] font-bold text-tacir-darkgray mb-4 uppercase tracking-widest flex items-center gap-2">
      <AlertTriangle class="w-3.5 h-3.5 text-tacir-blue" />
      Qualité des Données (Complétude)
    </h4>

    <div v-if="loading" class="h-[250px] flex items-center justify-center text-xs text-slate-400">
      Chargement...
    </div>
    <div v-else-if="error" class="h-[250px] flex items-center justify-center text-xs text-red-400">
      Erreur : {{ error }}
    </div>
    <div v-else class="h-[250px] flex items-center justify-center">
      <VueApexCharts
        type="radialBar"
        height="300"
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

const { dataQuality, loading, error } = useMonitoringETL()

// Couleur dynamique selon le seuil
function colorForRate(rate) {
  if (rate >= 90) return '#059669'  // vert
  if (rate >= 70) return '#f59e0b'  // orange
  return '#dc2626'                  // rouge critique
}

const series  = computed(() => dataQuality.value.map(d => d.fill_rate))
const labels  = computed(() => dataQuality.value.map(d => d.field_name))
const colors  = computed(() => dataQuality.value.map(d => colorForRate(d.fill_rate)))

const chartOptions = computed(() => ({
  chart: {
    type: 'radialBar',
    fontFamily: 'inherit',
    offsetY: -10
  },
  plotOptions: {
    radialBar: {
      hollow: { size: '30%' },
      dataLabels: {
        name:  { fontSize: '12px' },
        value: { fontSize: '12px', fontWeight: 700 },
        total: {
          show: true,
          label: 'Général',
          formatter(w) {
            const avg = w.globals.seriesTotals.reduce((a, b) => a + b, 0)
                        / (w.globals.seriesTotals.length || 1)
            return avg.toFixed(0) + '%'
          }
        }
      }
    }
  },
  labels:  labels.value,
  colors:  colors.value
}))
</script>