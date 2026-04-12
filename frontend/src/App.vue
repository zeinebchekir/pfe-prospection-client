<template>
  <!-- Global loading screen while restoring session on first load -->
  <div v-if="initializing" class="fixed inset-0 z-[100] flex items-center justify-center bg-background">
    <div class="flex flex-col items-center gap-4 text-center">
      <Loader2 class="h-10 w-10 animate-spin text-primary" />
      <p class="text-lg font-medium text-muted-foreground animate-pulse">
        Restoring your session...
      </p>
    </div>
  </div>

  <!-- Router view with page transitions -->
  <RouterView v-else v-slot="{ Component }">
    <Transition name="fade" mode="out-in">
      <component :is="Component" />
    </Transition>
  </RouterView>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuth } from '@/composables/useAuth'
import { Loader2 } from 'lucide-vue-next'

const { fetchUser } = useAuth()

// Show a loading screen while we check for an existing session.
// The router guard also calls fetchUser, but we do it here too
// so the UI doesn't flash the login page on refresh.
const initializing = ref(true)

onMounted(async () => {
  await fetchUser()
  initializing.value = false
})
</script>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
