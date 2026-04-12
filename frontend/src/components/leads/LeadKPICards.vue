<template>
  <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
    <Card
      v-for="c in cards"
      :key="c.key"
      class="p-3 border-border shadow-sm hover:shadow-md transition-shadow"
    >
      <div class="flex items-center gap-2 mb-1">
        <div :class="`w-7 h-7 rounded-lg ${c.bg} flex items-center justify-center`">
          <component :is="c.icon" :class="`w-3.5 h-3.5 ${c.color}`" />
        </div>
      </div>
      <p class="text-lg font-semibold text-foreground leading-tight">
        {{ displayValue(c) }}
      </p>
      <p class="text-[10px] text-muted-foreground">{{ c.label }}</p>
    </Card>
  </div>
</template>

<script setup>
import { Card } from '@/components/ui/card'
import { Building2, TrendingUp, Target, BarChart3, DollarSign, CheckCircle, Sparkles } from 'lucide-vue-next'
import { formatCA } from '@/lib/leadAdapter'

const props = defineProps({
  kpis: {
    type: Object,
    required: true,
    // { total, avgScore, avgProba, avgCompletude, totalCA, qualified, opportunities }
  },
})

const cards = [
  { key: 'total',          label: 'Total leads',       icon: Building2,   color: 'text-tacir-blue',     bg: 'bg-blue-50'    },
  { key: 'avgScore',       label: 'Score moyen',        icon: TrendingUp,  color: 'text-emerald-600',    bg: 'bg-emerald-50', suffix: '/100' },
  { key: 'avgProba',       label: 'Proba. moy.',        icon: Target,      color: 'text-amber-600',      bg: 'bg-amber-50',   suffix: '%'   },
  { key: 'avgCompletude',  label: 'Complétude moy.',    icon: BarChart3,   color: 'text-blue-600',       bg: 'bg-blue-50',    suffix: '%'   },
  { key: 'totalCA',        label: 'CA cumulé',          icon: DollarSign,  color: 'text-emerald-600',    bg: 'bg-emerald-50', isCA: true    },
  { key: 'qualified',      label: 'Qualifiés',          icon: CheckCircle, color: 'text-tacir-blue',     bg: 'bg-blue-50'    },
  { key: 'opportunities',  label: 'Opportunités',       icon: Sparkles,    color: 'text-amber-600',      bg: 'bg-amber-50'   },
]

function displayValue(card) {
  const val = props.kpis[card.key] ?? 0
  if (card.isCA) return formatCA(val)
  return `${val}${card.suffix ?? ''}`
}
</script>
