<template>
  <th
    class="text-[11px] font-medium text-muted-foreground px-4 py-3 text-left whitespace-nowrap cursor-pointer select-none hover:bg-muted/50 transition-colors"
    @click="emit('sort', field)"
  >
    <span class="flex items-center gap-1">
      {{ label }}
      <ChevronUp v-if="sortField === field && sortDir === 'asc'" class="w-3 h-3" />
      <ChevronDown v-else-if="sortField === field && sortDir === 'desc'" class="w-3 h-3" />
      <ChevronDown v-else class="w-3 h-3 opacity-30" />
    </span>
  </th>
</template>

<script setup>
import { ChevronDown, ChevronUp } from 'lucide-vue-next'

const props = defineProps({
  field:     { type: String, required: true },
  label:     { type: String, required: true },
  sortField: { type: String, required: true },
  sortDir:   { type: String, required: true },
})

const emit = defineEmits(['sort'])
</script>
