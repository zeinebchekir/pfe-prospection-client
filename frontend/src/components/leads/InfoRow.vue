<template>
  <div class="flex items-center justify-between py-2 border-b border-border last:border-b-0">
    <span class="text-[11px] text-muted-foreground">{{ label }}</span>
    <!-- Badge style for taille/segment -->
    <span
      v-if="badge"
      class="text-[10px] font-semibold px-2 py-0.5 rounded-sm bg-blue-50 text-tacir-blue border border-blue-200"
    >
      {{ value }}
    </span>
    <!-- Regular value -->
    <span
      v-else
      :class="[
        'text-xs font-medium text-right max-w-[200px] truncate',
        isMissing || muted ? 'text-muted-foreground italic' :
        link ? 'text-tacir-blue' :
        highlight ? 'text-emerald-600' :
        'text-foreground'
      ]"
    >
      {{ value }}
    </span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label:     { type: String,  required: true },
  value:     { type: String,  required: true },
  link:      { type: Boolean, default: false },
  highlight: { type: Boolean, default: false },
  muted:     { type: Boolean, default: false },
  badge:     { type: Boolean, default: false },
})

const isMissing = computed(() => props.value === '—' || props.value === 'Non renseigné')
</script>
