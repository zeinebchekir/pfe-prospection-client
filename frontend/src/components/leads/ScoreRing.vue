<template>
  <!-- Score ring (colored circle with score number) -->
  <span
    :class="[
      'inline-flex items-center justify-center rounded-full font-semibold',
      colorClass,
      sizeClass,
    ]"
  >
    {{ score }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  score: { type: Number, required: true },
  size: { type: String, default: 'sm' }, // 'sm' | 'md'
})

const colorClass = computed(() => {
  if (props.score >= 70) return 'text-emerald-700 bg-emerald-50'
  if (props.score >= 40) return 'text-blue-700 bg-blue-50'
  return 'text-orange-700 bg-orange-50'
})

const sizeClass = computed(() =>
  props.size === 'md' ? 'w-10 h-10 text-sm' : 'w-7 h-7 text-[11px]'
)
</script>
