<template>
  <div class="p-3 rounded-xl bg-muted/40 text-center">
    <component :is="icon" class="w-4 h-4 text-muted-foreground mx-auto mb-1" />
    <p class="text-sm font-semibold text-foreground">{{ value }}</p>
    <p class="text-[10px] text-muted-foreground">{{ label }}</p>
  </div>
</template>

<script setup>
defineProps({
  icon:  { required: true },
  label: { type: String, required: true },
  value: { type: String, required: true },
})
</script>
