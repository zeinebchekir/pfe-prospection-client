<template>
  <div class="flex items-center gap-2">
    <div class="w-12 h-1.5 rounded-full bg-muted overflow-hidden">
      <div
        class="h-full rounded-full transition-all duration-300"
        :class="barColor"
        :style="{ width: `${value}%` }"
      />
    </div>
    <span v-if="showLabel" class="text-[11px] font-medium text-muted-foreground">
      {{ value }}%
    </span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  value: { type: Number, required: true },
  showLabel: { type: Boolean, default: true },
})

const barColor = computed(() => {
  if (props.value >= 70) return 'bg-emerald-500'
  if (props.value >= 40) return 'bg-blue-500'
  return 'bg-orange-500'
})
</script>
