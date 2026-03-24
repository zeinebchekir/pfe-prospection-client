<script setup>
import { AvatarFallback } from "reka-ui";
import { cn } from "@/lib/utils";

const props = defineProps({
  delayMs: { type: Number, required: false },
  asChild: { type: Boolean, required: false },
  as: { type: null, required: false },
  class: { type: [String, Object, Array], required: false },
});
</script>

<template>
  <AvatarFallback v-bind="props" :class="cn('flex h-full w-full items-center justify-center rounded-full bg-muted', props.class)">
    <slot />
  </AvatarFallback>
</template>
