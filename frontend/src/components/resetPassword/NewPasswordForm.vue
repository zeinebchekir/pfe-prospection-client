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
            Nouveau mot de passe
          </h1>
          <p class="text-sm text-tacir-darkgray font-medium">
            Choisissez un mot de passe fort et sécurisé
          </p>
        </div>

        <!-- Error Feedback -->
        <div v-if="error" class="mb-6 p-3 rounded-xl bg-red-50 border border-red-100 flex gap-3 items-center animate-in fade-in slide-in-from-top-1">
          <div class="w-2 h-2 rounded-full bg-red-500 animate-pulse"></div>
          <p class="text-[11px] font-bold text-red-600 uppercase tracking-wider">{{ error }}</p>
        </div>

        <form @submit.prevent="handleSubmit" class="space-y-4">
          <!-- New password -->
          <div class="space-y-1.5">
            <Label for="password" class="text-tacir-darkblue text-sm font-medium">
              Nouveau mot de passe
            </Label>
            <div class="relative">
              <Lock class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-tacir-darkgray" />
              <Input
                id="password"
                :type="showPwd ? 'text' : 'password'"
                placeholder="Minimum 8 caractères"
                v-model="password"
                class="pl-10 pr-10 h-11 rounded-lg border-border focus:border-tacir-blue focus:ring-1 focus:ring-tacir-blue/20 transition-all"
                required
              />
              <button
                type="button"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-tacir-darkgray hover:text-tacir-blue transition-colors"
                @click="showPwd = !showPwd"
              >
                <EyeOff v-if="showPwd" class="w-4 h-4" />
                <Eye v-else class="w-4 h-4" />
              </button>
            </div>
            <PasswordStrength :password="password" />
          </div>

          <!-- Confirm password -->
          <div class="space-y-1.5">
            <Label for="confirmPassword" class="text-tacir-darkblue text-sm font-medium">
              Confirmer le mot de passe
            </Label>
            <div class="relative">
              <Lock class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-tacir-darkgray" />
              <Input
                id="confirmPassword"
                :type="showConfirm ? 'text' : 'password'"
                placeholder="Répétez le mot de passe"
                v-model="confirmPassword"
                class="pl-10 pr-10 h-11 rounded-lg border-border focus:border-tacir-blue focus:ring-1 focus:ring-tacir-blue/20 transition-all"
                :class="{ 
                  'border-tacir-green/20 bg-tacir-green/5': passwordMatch,
                  'border-red-400 bg-red-50': passwordMismatch
                }"
                required
              />
              <button
                type="button"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-tacir-darkgray hover:text-tacir-blue transition-colors"
                @click="showConfirm = !showConfirm"
              >
                <EyeOff v-if="showConfirm" class="w-4 h-4" />
                <Eye v-else class="w-4 h-4" />
              </button>
            </div>
            <p v-if="passwordMatch" class="flex items-center gap-1.5 text-[10px] font-bold text-tacir-green mt-1 uppercase tracking-tight">
              <CheckCircle2 class="w-3 h-3" /> Les mots de passe correspondent
            </p>
            <p v-if="passwordMismatch" class="text-[10px] font-bold text-red-500 mt-1 uppercase tracking-tight">
              Les mots de passe ne correspondent pas
            </p>
          </div>

          <Button
            type="submit"
            :disabled="loading || !password || !confirmPassword || !!passwordMismatch"
            class="w-full h-11 text-sm font-semibold bg-tacir-blue hover:bg-tacir-darkblue text-white rounded-lg transition-colors inline-flex items-center justify-center gap-2 shadow-lg shadow-tacir-blue/20 mt-2"
          >
            <span v-if="loading" class="flex items-center gap-2">
              <Loader2 class="w-4 h-4 animate-spin" />
              Mise à jour…
            </span>
            <span v-else class="flex items-center gap-2">
              Réinitialiser le mot de passe
              <ArrowRight class="w-4 h-4" />
            </span>
          </Button>
        </form>
      </CardContent>
    </Card>

  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import AppLogo from './AppLogo.vue'
import PasswordStrength from './PasswordStrength.vue'
import {
  KeyRound, Lock, Eye, EyeOff,
  CheckCircle2, ArrowRight, Loader2
} from 'lucide-vue-next'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'
import { Label } from '../../components/ui/label'
import { Card, CardContent } from '../../components/ui/card'
import api from '../../api/axios'

const props = defineProps<{
  token: string
}>()

const emit = defineEmits<{
  (e: 'submitted'): void
}>()

const password        = ref('')
const confirmPassword = ref('')
const showPwd         = ref(false)
const showConfirm     = ref(false)
const loading         = ref(false)
const error           = ref<string | null>(null)

const passwordMatch = computed(() =>
  password.value && confirmPassword.value && password.value === confirmPassword.value
)
const passwordMismatch = computed(() =>
  confirmPassword.value && password.value !== confirmPassword.value
)

async function handleSubmit() {
  if (passwordMismatch.value) return
  loading.value = true
  error.value = null
  try {
    await api.post('/auth/password-reset/confirm/', {
      token: props.token,
      password: password.value,
      password2: confirmPassword.value
    })
    emit('submitted')
  } catch (err: any) {
    error.value = err.response?.data?.error || "Une erreur est survenue."
  } finally {
    loading.value = false
  }
}
</script>
