<template>
  <!--
    PasswordStrength.vue
    Shows live password requirement checks below a password input.

    Props:
      password (string) — the current password value to validate

    Usage:
      <PasswordStrength :password="password" />
  -->
  <div v-if="password" class="flex gap-3 mt-2">
    <div v-for="check in checks" :key="check.label" class="flex items-center gap-1">
      <CheckCircle2
        class="w-3 h-3 transition-colors"
        :class="check.valid ? 'text-tacir-green' : 'text-tacir-darkgray/40'"
      />
      <span
        class="text-[10px]"
        :class="check.valid ? 'text-tacir-green' : 'text-tacir-darkgray/50'"
      >
        {{ check.label }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { CheckCircle2 } from 'lucide-vue-next'

const props = defineProps<{ password: string }>()

const checks = computed(() => [
  { label: "8 caractères min.", valid: props.password.length >= 8 },
  { label: "Majuscule", valid: /[A-Z]/.test(props.password) },
  { label: "Chiffre", valid: /\d/.test(props.password) },
])
</script>
