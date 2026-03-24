<template>
  <div class="relative bg-white rounded-2xl shadow-card border border-border overflow-hidden">
    <!-- Browser top bar -->
    <div class="bg-tacir-lightgray border-b border-border px-4 py-2.5 flex items-center gap-2">
      <div class="w-2.5 h-2.5 rounded-full bg-red-400" />
      <div class="w-2.5 h-2.5 rounded-full bg-yellow-400" />
      <div class="w-2.5 h-2.5 rounded-full bg-green-400" />
      <div class="flex-1 mx-4 bg-white rounded-md px-3 py-1 text-xs text-tacir-darkgray border border-border">
        taciriq.internal / dashboard
      </div>
    </div>

    <!-- Dashboard content -->
    <div class="p-5">
      <!-- KPI row -->
      <div class="grid grid-cols-4 gap-3 mb-4">
        <div v-for="kpi in kpis" :key="kpi.label" class="bg-tacir-lightgray rounded-xl p-3">
          <div :class="`text-lg font-bold ${kpi.color}`">{{ kpi.value }}</div>
          <div class="text-[10px] text-tacir-darkgray mt-0.5">{{ kpi.label }}</div>
          <div class="text-[10px] text-tacir-green font-medium mt-1">{{ kpi.trend }}</div>
        </div>
      </div>

      <!-- Charts -->
      <div class="grid grid-cols-3 gap-3">
        <!-- Bar chart -->
        <div class="col-span-2 bg-tacir-lightgray rounded-xl p-3">
          <div class="text-[10px] font-semibold text-tacir-darkblue mb-2">Pipeline de leads qualifiés</div>
          <div class="flex items-end gap-1 h-16">
            <div
              v-for="(barH, i) in bars"
              :key="i"
              class="flex-1 rounded-sm"
              :style="{
                height: `${barH}%`,
                background: i % 3 === 0 ? '#303E8C' : i % 3 === 1 ? '#04ADBF' : '#2D3773',
                opacity: 0.7 + i / 30,
              }"
            />
          </div>
        </div>

        <!-- Score distribution -->
        <div class="bg-tacir-lightgray rounded-xl p-3">
          <div class="text-[10px] font-semibold text-tacir-darkblue mb-2">Score distribution</div>
          <div class="space-y-1.5">
            <div v-for="s in scores" :key="s.label">
              <div class="flex justify-between text-[9px] text-tacir-darkgray mb-0.5">
                <span>{{ s.label }}</span>
                <span>{{ s.pct }}%</span>
              </div>
              <div class="h-1.5 bg-white rounded-full overflow-hidden">
                <div
                  class="h-full rounded-full transition-all"
                  :style="{ width: `${s.pct}%`, background: s.color }"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const kpis = [
  { label: 'Leads enrichis',   value: '1,284',  color: 'text-tacir-blue',      trend: '+12%'   },
  { label: 'Score moyen',      value: '78/100', color: 'text-tacir-green',     trend: '+5pts'  },
  { label: 'Signaux détectés', value: '342',    color: 'text-tacir-lightblue', trend: '+23%'   },
  { label: 'Sync CRM',         value: '99.9%',  color: 'text-tacir-darkblue',  trend: 'uptime' },
]
const bars   = [40, 60, 45, 75, 55, 85, 70, 90, 65, 80, 95, 88]
const scores = [
  { label: 'A — Chaud', pct: 72, color: '#56A632' },
  { label: 'B — Tiède', pct: 54, color: '#303E8C' },
  { label: 'C — Froid', pct: 28, color: '#7B797A' },
]
</script>

<style scoped>
.shadow-card {
  box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(48,62,140,0.06);
}
</style>
