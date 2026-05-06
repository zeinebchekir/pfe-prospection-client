<template>
  <header class="h-16 border-b border-border bg-white sticky top-0 z-40 px-6 flex items-center justify-between shadow-sm shrink-0">
    <div class="flex items-center gap-3">
      <div class="md:hidden w-10" />
      <div>
        <div class="flex items-center gap-2">
          <h2 class="text-sm font-semibold text-tacir-darkblue">{{ title }}</h2>
          <span v-if="badge" class="hidden sm:inline-flex items-center gap-1.5 bg-tacir-blue/8 text-tacir-blue border border-tacir-blue/15 text-[10px] font-semibold uppercase tracking-widest px-3 py-1 rounded-full">
            <span class="w-1.5 h-1.5 rounded-full bg-tacir-lightblue animate-pulse" />
            {{ badge.label }}
          </span>
        </div>
        <p v-if="subtitle" class="text-[11px] text-tacir-darkgray">{{ subtitle }}</p>
      </div>
    </div>

    <div class="flex items-center gap-3">
      <slot name="actions">
        <template v-for="(action, index) in actions" :key="index">
          <Button 
            v-if="action.variant === 'secondary'" 
            @click="action.onClick" 
            variant="outline" 
            size="sm" 
            class="hidden sm:flex items-center gap-2 border-border/60 text-tacir-darkblue bg-tacir-lightgray/20 hover:bg-tacir-lightgray/50"
          >
            <component :is="action.icon" v-if="action.icon" class="w-3.5 h-3.5 text-tacir-darkgray" />
            <span class="text-xs font-semibold">{{ action.label }}</span>
          </Button>
          
          <Button 
            v-else-if="action.variant === 'primary'" 
            @click="action.onClick" 
            class="h-9 px-4 bg-tacir-blue hover:bg-tacir-darkblue text-white rounded-lg gap-2 shadow-sm transition-all active:scale-95 text-xs font-bold"
          >
            <component :is="action.icon" v-if="action.icon" class="w-3.5 h-3.5" />
            {{ action.label }}
          </Button>
        </template>
      </slot>
      <NotificationBell />
    </div>
  </header>
</template>

<script setup>
import NotificationBell from '@/components/ui/notifications/notificationsBell.vue'
import { Button } from '@/components/ui/button'

defineProps({
  title: {
    type: String,
    required: true
  },
  subtitle: {
    type: String,
    default: ''
  },
  actions: {
    type: Array,
    default: () => []
  },
  badge: {
    type: Object,
    default: null
  }
})
</script>
