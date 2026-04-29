<script setup>
import { computed } from 'vue'
import { ProgressIndicator, ProgressRoot } from 'radix-vue'
import { cn } from '@/lib/utils'

const props = defineProps({
  modelValue: { type: [Number, null], default: 0 },
  max: { type: Number, default: 100 },
  getValueLabel: { type: Function, default: undefined },
  asChild: { type: Boolean, default: false },
  as: { type: null, default: undefined },
  class: { type: null, default: undefined },
})

const delegatedProps = computed(() => {
  const { class: _, ...delegated } = props
  return delegated
})
</script>

<template>
  <ProgressRoot
    v-bind="delegatedProps"
    :class="
      cn(
        'relative h-4 w-full overflow-hidden rounded-full bg-secondary',
        props.class,
      )
    "
  >
    <ProgressIndicator
      class="h-full w-full flex-1 bg-primary transition-all duration-300 ease-in-out"
      :style="`transform: translateX(-${100 - (props.modelValue ?? 0)}%);`"
    />
  </ProgressRoot>
</template>
