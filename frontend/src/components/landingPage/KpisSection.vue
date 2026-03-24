<template>
  <section id="impact" class="py-20 px-6 kpi-gradient">
    <div class="container mx-auto max-w-5xl">

      <div class="text-center mb-12">
        <p class="text-tacir-lightblue font-semibold text-sm uppercase tracking-widest mb-3">
          Indicateurs visés
        </p>
        <h2 class="text-3xl font-bold text-white">
          Les gains attendus pour notre équipe
        </h2>
        <p class="text-white/60 text-sm mt-3 max-w-lg mx-auto">
          Objectifs internes basés sur l'analyse de nos processus commerciaux actuels et les benchmarks sectoriels.
        </p>
      </div>

      <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div v-for="k in kpis" :key="k.label" class="kpi-card">
          <div :class="`text-4xl font-extrabold ${k.color} mb-1`">
            {{ k.prefix }}<AnimatedCounter :target="k.value" :suffix="k.suffix" />
          </div>
          <div class="text-white/80 text-sm font-medium">{{ k.label }}</div>
        </div>
      </div>

    </div>
  </section>
</template>

<script setup>
import AnimatedCounter from './AnimatedCounter.vue'

const kpis = [
  { value: 30, suffix: '%', label: 'Taux de transformation',  prefix: '+', color: 'text-white'           },
  { value: 40, suffix: '%', label: 'Temps de qualification',  prefix: '-', color: 'text-tacir-lightblue' },
  { value: 60, suffix: '%', label: 'Complétude CRM',          prefix: '+', color: 'text-white'           },
  { value: 25, suffix: '%', label: 'Opportunités qualifiées', prefix: '+', color: 'text-tacir-lightblue' },
]
</script>

<style scoped>
.kpi-gradient { background: linear-gradient(135deg, #2d3773 0%, #303e8c 60%, #04adbf 100%); }
.kpi-card {
  background-color: rgba(255,255,255,0.1);
  backdrop-filter: blur(8px);
  border-radius: 1rem;
  padding: 1.5rem;
  text-align: center;
  border: 1px solid rgba(255,255,255,0.1);
}
</style>
