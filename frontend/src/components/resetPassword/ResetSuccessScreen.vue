<template>
  <!--
    ResetSuccessScreen.vue
    Step 4 — Password was updated successfully.
    No props or emits needed — just a static confirmation with a link to sign in.
  -->
  <div class="text-center max-w-md w-full animate-[fadeIn_0.35s_ease_both]">

    <!-- Icon -->
    <div class="w-16 h-16 rounded-full bg-green-500/10 flex items-center justify-center mx-auto mb-5 text-green-500">
      <ShieldCheckIcon />
    </div>

    <h2 class="text-2xl font-bold text-blue-900 mb-2">Mot de passe mis à jour !</h2>
    <p class="text-sm text-slate-500 mb-6">
      Votre mot de passe a été réinitialisé avec succès. Vous pouvez maintenant vous connecter.
    </p>

    <a
      href="/signin"
      class="inline-flex items-center justify-center gap-2 px-6 h-11 bg-gradient-to-br from-blue-500 to-blue-900 text-white text-sm font-semibold rounded-lg hover:opacity-90 active:scale-[0.98] transition-all no-underline"
    >
      Se connecter
      <ArrowRightIcon />
    </a>
  </div>
</template>

<script setup lang="ts">
import { ShieldCheckIcon, ArrowRightIcon } from './icons'
</script>
