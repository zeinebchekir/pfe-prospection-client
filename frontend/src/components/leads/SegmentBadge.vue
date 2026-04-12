<template>
  <Badge
    variant="outline"
    :class="`text-[10px] font-semibold px-2 py-0.5 ${SEGMENT_STYLES[segment] ?? SEGMENT_STYLES.Inconnu}`"
  >
    {{ segment }}
  </Badge>
</template>

<script setup>
import { Badge } from '@/components/ui/badge'

const props = defineProps({
  segment: { type: String, required: true },
})

const SEGMENT_STYLES = {
  PME:     'bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100',
  ETI:     'bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100',
  GE:      'bg-orange-50 text-orange-700 border-orange-200 hover:bg-orange-100',
  Micro:   'bg-purple-50 text-purple-700 border-purple-200 hover:bg-purple-100',
  Inconnu: 'bg-muted text-muted-foreground border-border',
}
</script>
