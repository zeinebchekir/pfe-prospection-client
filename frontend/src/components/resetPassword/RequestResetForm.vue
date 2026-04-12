<template>
  <div class="w-full max-w-md animate-fade-in">
    <AppLogo />

    <Card class="shadow-card border-border rounded-2xl">
      <CardContent class="p-8">
        <div class="flex items-center justify-center w-12 h-12 rounded-xl bg-tacir-blue/10 mx-auto mb-5">
          <KeyRound class="w-6 h-6 text-tacir-blue" />
        </div>

        <div class="mb-7 text-center">
          <h1 class="text-2xl font-bold text-tacir-darkblue mb-1.5">
            Mot de passe oublié ?
          </h1>
          <p class="text-sm text-tacir-darkgray font-medium">
            Entrez votre adresse email pour recevoir un lien de réinitialisation
          </p>
        </div>

        <!-- Error Feedback -->
        <div v-if="error" class="mb-6 p-3 rounded-xl bg-red-50 border border-red-100 flex gap-3 items-center animate-in fade-in slide-in-from-top-1">
          <div class="w-2 h-2 rounded-full bg-red-500 animate-pulse"></div>
          <p class="text-[11px] font-bold text-red-600 uppercase tracking-wider">{{ error }}</p>
        </div>

        <form @submit.prevent="handleSubmit" class="space-y-4">
          <div class="space-y-1.5">
            <Label for="email" class="text-tacir-darkblue text-sm font-medium">
              Adresse email
            </Label>
            <div class="relative">
              <Mail class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-tacir-darkgray" />
              <Input
                id="email"
                type="email"
                placeholder="vous@entreprise.com"
                v-model="email"
                class="pl-10 h-11 rounded-lg border-border focus:border-tacir-blue focus:ring-1 focus:ring-tacir-blue/20 transition-all"
                :class="{ 'border-tacir-green/20 bg-tacir-green/5': emailValid }"
                required
              />
              <CheckCircle2 v-if="emailValid" class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-tacir-green" />
            </div>
          </div>

          <Button
            type="submit"
            class="w-full h-11 text-sm font-semibold bg-tacir-blue hover:bg-tacir-darkblue text-white rounded-lg transition-colors inline-flex items-center justify-center gap-2 shadow-lg shadow-tacir-blue/20"
            :disabled="loading"
          >
            <span v-if="loading" class="flex items-center gap-2">
              <Loader2 class="w-4 h-4 animate-spin" />
              Envoi en cours…
            </span>
            <span v-else class="flex items-center gap-2">
              Envoyer le lien
              <ArrowRight class="w-4 h-4" />
            </span>
          </Button>
        </form>

        <p class="text-center mt-6 text-tacir-darkgray text-sm font-medium">
          <RouterLink
            to="/login"
            class="text-tacir-blue hover:text-tacir-darkblue font-semibold transition-colors"
          >
            ← Retour à la connexion
          </RouterLink>
        </p>
      </CardContent>
    </Card>

  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import AppLogo from './AppLogo.vue'
import { KeyRound, Mail, CheckCircle2, ArrowRight, Loader2 } from 'lucide-vue-next'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'
import { Label } from '../../components/ui/label'
import { Card, CardContent } from '../../components/ui/card'
import api from '../../api/axios'

const emit = defineEmits<{
  (e: 'submitted', email: string): void
}>()

const email   = ref('')
const loading = ref(false)
const error   = ref<string | null>(null)

const emailValid = computed(() =>
  email.value.includes('@') && email.value.includes('.')
)

async function handleSubmit() {
  loading.value = true
  error.value = null
  try {
    await api.post('/auth/password-reset/', { email: email.value })
    emit('submitted', email.value)
  } catch (err: any) {
    error.value = err.response?.data?.error || "Une erreur est survenue."
  } finally {
    loading.value = false
  }
}
</script>
