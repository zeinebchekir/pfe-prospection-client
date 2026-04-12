<template>
  <Badge
    variant="outline"
    :class="`text-[10px] font-semibold px-2 py-0.5 ${STATUS_STYLES[status] ?? ''}`"
  >
    {{ status }}
  </Badge>
</template>

<script setup>
import { Badge } from '@/components/ui/badge'

const props = defineProps({
  status: { type: String, required: true },
})

const STATUS_STYLES = {
  Nouveau:     'bg-blue-50 text-blue-700 border-blue-200',
  Qualifié:   'bg-emerald-50 text-emerald-700 border-emerald-200',
  Opportunité: 'bg-amber-50 text-amber-700 border-amber-200',
}
</script>
