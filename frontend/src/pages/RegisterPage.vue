<template>
  <div class="min-h-screen flex font-sans">

    <!-- ── LEFT PANEL ── -->
    <div class="hidden lg:flex lg:w-1/2 relative flex-col justify-between p-12 overflow-hidden left-panel">
      <!-- Background decorations -->
      <div class="absolute inset-0 overflow-hidden pointer-events-none">
        <div class="absolute -top-20 -right-20 w-80 h-80 rounded-full bg-white/5" />
        <div class="absolute -bottom-32 -left-16 w-96 h-96 rounded-full bg-white/5" />
        <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 rounded-full bg-white/[0.03]" />
      </div>

      <!-- Logo -->
      <div class="relative flex items-center gap-2.5">
        <img src="@/assets/logo.png" alt="crmPfe Logo" class="h-35 w-auto object-contain" />
      </div>

      <!-- Main message -->
      <div class="relative">
        <p class="text-white/60 text-sm font-medium uppercase tracking-widest mb-4">
          Rejoignez crmPfe
        </p>
        <h2 class="text-4xl font-extrabold text-white leading-[1.15] mb-6">
          Créez votre espace<br />
          <span class="text-tacir-lightblue">commercial intelligent</span>
        </h2>
        <p class="text-white/70 text-sm leading-relaxed mb-10 max-w-sm">
          Enrichissement automatique, scoring IA et synchronisation native Boond.
          Opérationnel en moins de 5 minutes.
        </p>

        <div class="space-y-4">
          <div v-for="f in features" :key="f.text" class="flex items-start gap-3">
            <div class="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center flex-shrink-0 mt-0.5">
              <component :is="f.icon" class="w-4 h-4 text-white" />
            </div>
            <p class="text-white/80 text-sm leading-relaxed">{{ f.text }}</p>
          </div>
        </div>
      </div>

      <!-- Bottom trust -->
      <div class="relative flex items-center gap-2">
        <div class="w-2 h-2 rounded-full bg-tacir-green animate-pulse" />
        <span class="text-white/50 text-xs">Sans carte bancaire · Setup en 5 min · RGPD Compliant</span>
      </div>
    </div>

    <!-- ── RIGHT PANEL ── -->
    <div class="flex-1 flex items-center justify-center p-6 bg-white overflow-y-auto">
      <div class="w-full max-w-md animate-fade-in py-8">

        <!-- Mobile logo -->
        <div class="lg:hidden flex items-center gap-2 mb-8">
          <img src="@/assets/logo.png" alt="crmPfe Logo" class="h-35 w-auto object-contain" />
        </div>

        <!-- Header -->
        <div class="mb-8">
          <h1 class="text-2xl font-bold text-tacir-darkblue mb-2">Créer un compte</h1>
          <p class="text-tacir-darkgray text-sm">Rejoignez votre espace commercial crmPfe</p>
        </div>

        <!-- Global error -->
        <div v-if="error" class="mb-5">
          <Alert variant="destructive" class="rounded-xl border-red-200 bg-red-50">
            <AlertTitle class="font-semibold text-xs uppercase tracking-widest">Erreur</AlertTitle>
            <AlertDescription class="text-sm">{{ error }}</AlertDescription>
          </Alert>
        </div>

        <!-- Form -->
        <form @submit.prevent="handleRegister" class="space-y-5">

          <!-- First name + Last name -->
          <div class="grid grid-cols-2 gap-3">
            <div class="space-y-1.5">
              <Label for="prenom" class="text-tacir-darkblue text-sm font-medium">
                Prénom
              </Label>
              <Input
                id="prenom"
                v-model="form.prenom"
                type="text"
                placeholder="Jean"
                autocomplete="given-name"
                class="h-11 rounded-lg border-border focus:border-tacir-blue focus:ring-1 focus:ring-tacir-blue/20 transition-all"
              />
            </div>
            <div class="space-y-1.5">
              <Label for="nom" class="text-tacir-darkblue text-sm font-medium">
                Nom
              </Label>
              <Input
                id="nom"
                v-model="form.nom"
                type="text"
                placeholder="Dupont"
                autocomplete="family-name"
                class="h-11 rounded-lg border-border focus:border-tacir-blue focus:ring-1 focus:ring-tacir-blue/20 transition-all"
              />
            </div>
          </div>

          <!-- Email -->
          <div class="space-y-1.5">
            <Label for="email" class="text-tacir-darkblue text-sm font-medium">
              Adresse email
            </Label>
            <div class="relative">
              <Mail class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-tacir-darkgray" />
              <Input
                id="email"
                v-model="form.email"
                type="email"
                placeholder="vous@entreprise.com"
                required
                class="pl-10 h-11 rounded-lg border-border focus:border-tacir-blue focus:ring-1 focus:ring-tacir-blue/20 transition-all"
                :class="{ 'border-red-400 bg-red-50': fieldErrors.email }"
              />
            </div>
            <p v-if="fieldErrors.email" class="text-[11px] text-red-500 font-medium ml-1">
              {{ fieldErrors.email }}
            </p>
          </div>

          <!-- Password + Confirm -->
          <div class="grid grid-cols-2 gap-3">
            <div class="space-y-1.5">
              <Label for="password" class="text-tacir-darkblue text-sm font-medium">
                Mot de passe
              </Label>
              <div class="relative">
                <Lock class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-tacir-darkgray" />
                <Input
                  id="password"
                  v-model="form.password"
                  :type="showPassword ? 'text' : 'password'"
                  placeholder="8 caractères min."
                  required
                  class="pl-10 pr-10 h-11 rounded-lg border-border focus:border-tacir-blue focus:ring-1 focus:ring-tacir-blue/20 transition-all"
                  :class="{ 'border-red-400 bg-red-50': fieldErrors.password }"
                />
                <button 
                  type="button"
                  @click="showPassword = !showPassword"
                  class="absolute right-3 top-1/2 -translate-y-1/2 text-tacir-darkgray hover:text-tacir-blue transition-colors"
                >
                  <Eye v-if="!showPassword" class="w-4 h-4" />
                  <EyeOff v-else class="w-4 h-4" />
                </button>
              </div>
            </div>
            <div class="space-y-1.5">
              <Label for="password2" class="text-tacir-darkblue text-sm font-medium">
                Confirmer
              </Label>
              <div class="relative">
                <Lock class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-tacir-darkgray" />
                <Input
                  id="password2"
                  v-model="form.password2"
                  :type="showPassword2 ? 'text' : 'password'"
                  placeholder="Répéter"
                  required
                  class="pl-10 pr-10 h-11 rounded-lg border-border focus:border-tacir-blue focus:ring-1 focus:ring-tacir-blue/20 transition-all"
                  :class="{ 'border-red-400 bg-red-50': fieldErrors.password2 }"
                />
                <button 
                  type="button"
                  @click="showPassword2 = !showPassword2"
                  class="absolute right-3 top-1/2 -translate-y-1/2 text-tacir-darkgray hover:text-tacir-blue transition-colors"
                >
                  <Eye v-if="!showPassword2" class="w-4 h-4" />
                  <EyeOff v-else class="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>

          <!-- Password errors -->
          <div v-if="fieldErrors.password || fieldErrors.password2" class="space-y-1">
            <p v-if="fieldErrors.password" class="text-[11px] text-red-500 font-medium ml-1">
              {{ fieldErrors.password }}
            </p>
            <p v-if="fieldErrors.password2" class="text-[11px] text-red-500 font-medium ml-1">
              {{ fieldErrors.password2 }}
            </p>
          </div>

          <!-- Password strength indicator -->
          <div v-if="form.password" class="space-y-1.5">
            <div class="flex gap-1">
              <div
                v-for="i in 4" :key="i"
                class="h-1 flex-1 rounded-full transition-all duration-300"
                :class="passwordStrength >= i ? strengthColor : 'bg-tacir-lightgray'"
              />
            </div>
            <p class="text-[11px] font-medium" :class="strengthTextColor">{{ strengthLabel }}</p>
          </div>

          <!-- Submit -->
          <Button
            type="submit"
            class="w-full h-11 text-sm font-semibold bg-tacir-blue hover:bg-tacir-darkblue text-white rounded-lg transition-colors inline-flex items-center justify-center gap-2"
            :disabled="isLoading"
          >
            <span v-if="isLoading" class="flex items-center gap-2">
              <Loader2 class="w-4 h-4 animate-spin" />
              Création du compte…
            </span>
            <span v-else class="flex items-center gap-2">
              Créer mon compte
              <ArrowRight class="w-4 h-4" />
            </span>
          </Button>

        </form>

        <!-- Sign in link -->
        <p class="text-center mt-6 text-tacir-darkgray text-sm">
          Déjà un compte ?
          <RouterLink to="/login" class="text-tacir-blue hover:text-tacir-darkblue font-semibold transition-colors ml-1">
            Se connecter
          </RouterLink>
        </p>

      </div>
    </div>

  </div>
</template>

<script setup>
import { reactive, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { RouterLink } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

import { Button } from '@/components/ui/button'
import { Input }  from '@/components/ui/input'
import { Label }  from '@/components/ui/label'
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert'

import {
  Zap, Mail, Lock, User, ArrowRight, Loader2,
  CheckCircle2, Shield, Database, Eye, EyeOff
} from 'lucide-vue-next'

// ── Router & auth ────────────────────────────────────────────────
const router = useRouter()
const { register, isLoading, error } = useAuth()

// ── Form state ───────────────────────────────────────────────────
const form = reactive({
  email:      '',
  prenom:     '',
  nom:        '',
  password:   '',
  password2:  '',
})

const showPassword = ref(false)
const showPassword2 = ref(false)
const fieldErrors = ref({})

// ── Features list (left panel) ───────────────────────────────────
const features = [
  { icon: CheckCircle2, text: 'Enrichissement automatique des fiches leads' },
  { icon: Database,     text: 'Synchronisation bidirectionnelle avec Boond Manager' },
  { icon: Shield,       text: 'Données hébergées en Europe, conformes RGPD' },
]

// ── Password strength ────────────────────────────────────────────
const passwordStrength = computed(() => {
  const p = form.password
  if (!p) return 0
  let score = 0
  if (p.length >= 8)              score++
  if (/[A-Z]/.test(p))            score++
  if (/[0-9]/.test(p))            score++
  if (/[^A-Za-z0-9]/.test(p))     score++
  return score
})

const strengthColor = computed(() => {
  if (passwordStrength.value <= 1) return 'bg-red-400'
  if (passwordStrength.value === 2) return 'bg-tacir-yellow'
  if (passwordStrength.value === 3) return 'bg-tacir-lightblue'
  return 'bg-tacir-green'
})

const strengthTextColor = computed(() => {
  if (passwordStrength.value <= 1) return 'text-red-500'
  if (passwordStrength.value === 2) return 'text-tacir-yellow'
  if (passwordStrength.value === 3) return 'text-tacir-lightblue'
  return 'text-tacir-green'
})

const strengthLabel = computed(() => {
  if (passwordStrength.value <= 1) return 'Mot de passe faible'
  if (passwordStrength.value === 2) return 'Mot de passe moyen'
  if (passwordStrength.value === 3) return 'Mot de passe bon'
  return 'Mot de passe fort'
})

// ── Validation ───────────────────────────────────────────────────
function validate() {
  const errors = {}
  if (!form.email)
    errors.email = "L'adresse email est requise."
  else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email))
    errors.email = 'Entrez une adresse email valide.'
  if (!form.password)
    errors.password = 'Le mot de passe est requis.'
  else if (form.password.length < 8)
    errors.password = 'Le mot de passe doit contenir au moins 8 caractères.'
  if (form.password !== form.password2)
    errors.password2 = 'Les mots de passe ne correspondent pas.'
  fieldErrors.value = errors
  return Object.keys(errors).length === 0
}

// ── Submit ───────────────────────────────────────────────────────
async function handleRegister() {
  const result = await register(form)
  if (result.success) {
    router.push("/dashboard")
  }
}
</script>

<style scoped>
.left-panel {
  background: linear-gradient(145deg, #2D3773 0%, #303E8C 60%, #04ADBF 100%);
}
.gradient-brand {
  background: linear-gradient(135deg, #303e8c, #04adbf);
}
.animate-fade-in {
  animation: fadeIn 0.45s ease-out both;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(14px); }
  to   { opacity: 1; transform: translateY(0); }
}
</style>