<template>
  <!--
    EmailSentScreen.vue
    Step 2 — Confirmation that the reset link was sent.

    Props:
      email (string) — the address the link was sent to

    Emits:
      proceed () — user clicks "Définir un nouveau mot de passe"
      resend  () — user wants to re-enter their email
  -->
  <div class="text-center max-w-md w-full animate-[fadeIn_0.35s_ease_both]">

    <!-- Icon -->
    <div class="w-16 h-16 rounded-full bg-blue-400/10 flex items-center justify-center mx-auto mb-5 text-blue-400">
      <MailIcon />
    </div>

    <h2 class="text-2xl font-bold text-blue-900 mb-2">Email envoyé !</h2>
    <p class="text-sm text-slate-500 mb-1">Un lien de réinitialisation a été envoyé à</p>
    <p class="text-sm font-semibold text-blue-500 mb-4">{{ email }}</p>
    <p class="text-xs text-slate-400 mb-8">
      Vérifiez votre boîte de réception (et vos spams). Le lien est valable 24 heures.
    </p>

    <div class="flex flex-col items-center gap-3">
      <button
        class="flex items-center justify-center gap-2 px-6 h-11 w-full max-w-xs bg-gradient-to-br from-blue-500 to-blue-900 text-white text-sm font-semibold rounded-lg hover:opacity-90 active:scale-[0.98] transition-all"
        @click="emit('proceed')"
      >
        Définir un nouveau mot de passe
        <ArrowRightIcon />
      </button>
      <button
        class="text-xs text-slate-400 hover:text-blue-500 transition-colors bg-transparent border-none cursor-pointer"
        @click="emit('resend')"
      >
        Renvoyer l'email
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { MailIcon, ArrowRightIcon } from './icons'

defineProps<{ email: string }>()

const emit = defineEmits<{
  (e: 'proceed'): void
  (e: 'resend'):  void
}>()
</script>
