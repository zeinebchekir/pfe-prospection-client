<template>
  <div class="w-full max-w-md animate-fade-in">
    <AppLogo />

    <div class="text-center">
      <div v-if="!isFinal">
        <div class="w-16 h-16 rounded-full bg-tacir-lightblue/10 flex items-center justify-center mx-auto mb-5">
          <Mail class="w-8 h-8 text-tacir-lightblue" />
        </div>
        <h2 class="text-2xl font-bold text-tacir-darkblue mb-2">Email envoyé !</h2>
        <p class="text-tacir-darkgray text-sm mb-2">
          Un lien de réinitialisation a été envoyé à 
        </p>
        <p class="font-semibold text-tacir-blue text-sm mb-6">{{ email }}</p>
        <p class="text-tacir-darkgray/70 text-xs mb-8">
          Vérifiez votre boîte de réception (et vos spams). Le lien est valable 24 heures. 
        </p>
        <div class="flex flex-col gap-3 items-center">
          <Button 
            class="bg-tacir-blue hover:bg-tacir-darkblue text-white w-full max-w-xs h-11"
            @click="$emit('retry')"
          >
            Renvoyer l'email
          </Button>
        </div>
      </div>

      <div v-else>
        <div class="w-16 h-16 rounded-full bg-tacir-green/10 flex items-center justify-center mx-auto mb-5">
          <ShieldCheck class="w-8 h-8 text-tacir-green" />
        </div>
        <h2 class="text-2xl font-bold text-tacir-darkblue mb-2">Mot de passe mis à jour !</h2>
        <p class="text-tacir-darkgray text-sm mb-6">
          Votre mot de passe a été réinitialisé avec succès. Vous pouvez maintenant vous connecter. 
        </p>
        <RouterLink to="/login">
          <Button class="bg-tacir-blue hover:bg-tacir-darkblue text-white h-11 px-8">
            Se connecter
            <ArrowRight class="w-4 h-4 ml-2" />
          </Button>
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import AppLogo from './AppLogo.vue'
import { Mail, ShieldCheck, ArrowRight } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'

defineProps<{
  email?: string
  isFinal?: boolean
}>()

defineEmits<{
  (e: 'retry'): void
}>()
</script>
