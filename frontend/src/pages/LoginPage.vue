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
      <div class="relative">
        <img src="@/assets/logo-blanc.png" alt="Qualifix Logo" class="h-30 w-auto object-contain" />
      </div>

      <!-- Main message -->
      <div class="relative">
        <p class="text-white/60 text-sm font-medium uppercase tracking-widest mb-4">
          Intelligence commerciale
        </p>
        <h2 class="text-4xl font-extrabold text-white leading-[1.15] mb-6">
          Accédez à votre<br />
          <span class="text-tacir-lightblue">intelligence commerciale</span>
        </h2>
        <p class="text-white/70 text-sm leading-relaxed mb-10 max-w-sm">
          Pilotez votre pipeline avec des données enrichies, un scoring précis
          et une synchronisation native Boond.
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

      <!-- Bottom trust badge -->
      <div class="relative flex items-center gap-2">
        <div class="w-2 h-2 rounded-full bg-tacir-green animate-pulse" />
        <span class="text-white/50 text-xs">Connecté · Chiffré · RGPD Compliant</span>
      </div>
    </div>

    <!-- ── RIGHT PANEL ── -->
    <div class="flex-1 flex items-center justify-center p-6 bg-white">
      <div class="w-full max-w-md animate-fade-in">

        <!-- Mobile logo -->
        <div class="lg:hidden flex items-center gap-2 mb-8">
          <img src="@/assets/logo.png" alt="crmPfe Logo" class="h-35 w-auto object-contain" />
        </div>

        <!-- Header -->
        <div class="mb-8">
          <h1 class="text-2xl font-bold text-tacir-darkblue mb-2">Bon retour </h1>
          <p class="text-tacir-darkgray text-sm">Connectez-vous à votre espace commercial</p>
        </div>

        <!-- Global error -->
        <div v-if="error" class="mb-5">
          <Alert variant="destructive" class="rounded-xl border-red-200 bg-red-50">
            <AlertTitle class="font-semibold text-xs uppercase tracking-widest">Erreur</AlertTitle>
            <AlertDescription class="text-sm">{{ error }}</AlertDescription>
          </Alert>
        </div>

        <!-- Form -->
        <form @submit.prevent="handleLogin" class="space-y-5">

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
                class="pl-10 h-11 rounded-lg border-border focus:border-tacir-blue focus:ring-1 focus:ring-tacir-blue/20 transition-all"
                :class="{ 'border-red-400 bg-red-50': fieldErrors.email }"
                required
              />
            </div>
            <p v-if="fieldErrors.email" class="text-[11px] text-red-500 font-medium ml-1">
              {{ fieldErrors.email }}
            </p>
          </div>

          <!-- Password -->
          <div class="space-y-1.5">
            <div class="flex items-center justify-between">
              <Label for="password" class="text-tacir-darkblue text-sm font-medium">
                Mot de passe
              </Label>
              <RouterLink to="/reset-password" class="text-tacir-blue hover:text-tacir-darkblue text-xs font-medium transition-colors">
                Mot de passe oublié ?
              </RouterLink>
            </div>
            <div class="relative">
              <Lock class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-tacir-darkgray" />
              <Input
                id="password"
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="••••••••"
                class="pl-10 pr-10 h-11 rounded-lg border-border focus:border-tacir-blue focus:ring-1 focus:ring-tacir-blue/20 transition-all"
                :class="{ 'border-red-400 bg-red-50': fieldErrors.password }"
                required
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
            <p v-if="fieldErrors.password" class="text-[11px] text-red-500 font-medium ml-1">
              {{ fieldErrors.password }}
            </p>
          </div>

          <!-- Remember me -->
          <div class="flex items-center gap-2.5">
          <!-- Remember me -->
          <div class="flex items-center gap-2.5">
            <input
              id="remember"
              v-model="remember"
              type="checkbox"
              class="w-4 h-4 rounded border-border cursor-pointer accent-[#303E8C]"
            />
            <Label for="remember" class="text-tacir-darkgray text-sm cursor-pointer">
              Se souvenir de moi
            </Label>
          </div>
          </div>

          <!-- Submit -->
          <Button
            type="submit"
            class="w-full h-11 text-sm font-semibold bg-tacir-blue hover:bg-tacir-darkblue text-white rounded-lg transition-colors inline-flex items-center justify-center gap-2"
            :disabled="isLoading"
          >
            <span v-if="isLoading" class="flex items-center gap-2">
              <Loader2 class="w-4 h-4 animate-spin" />
              Connexion…
            </span>
            <span v-else class="flex items-center gap-2">
              Se connecter
              <ArrowRight class="w-4 h-4" />
            </span>
          </Button>
        </form>

        <!-- Divider -->
        <div class="relative my-6">
          <Separator />
          <span class="absolute left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white px-3 text-xs text-tacir-darkgray">
            ou
          </span>
        </div>

        <!-- Google SSO -->
        <Button
          variant="outline"
          class="w-full h-11 text-sm font-medium border-border rounded-lg hover:bg-tacir-lightgray/50 transition-colors inline-flex items-center justify-center gap-2"
          type="button"
        >
          <svg class="w-4 h-4" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          Continuer avec Google
        </Button>

        <!-- Sign up link -->
        <p class="text-center mt-6 text-tacir-darkgray text-sm">
          Pas encore de compte ?
          <RouterLink to="/register" class="text-tacir-blue hover:text-tacir-darkblue font-semibold transition-colors ml-1">
            Créer un compte
          </RouterLink>
        </p>

      </div>
    </div>

  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { RouterLink } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

import { Button }   from '@/components/ui/button'
import { Input }    from '@/components/ui/input'
import { Label }    from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert'

import {
  Zap, Mail, Lock, ArrowRight, Loader2,
  TrendingUp, Shield, BarChart2, Eye, EyeOff
} from 'lucide-vue-next'

// ── Router & auth (logic from old login.vue) ─────────────────────
const router = useRouter()
const route  = useRoute()
const { login, isLoading, error } = useAuth()

// ── Form state ───────────────────────────────────────────────────
const form          = reactive({ email: '', password: '' })
const remember      = ref(false)
const showPassword  = ref(false)
const fieldErrors   = ref({})

// ── Features list (left panel) ───────────────────────────────────
const features = [
  { icon: TrendingUp, text: 'Scoring intelligent de vos leads en temps réel' },
  { icon: BarChart2,  text: 'Dashboards décisionnels connectés à Boond' },
  { icon: Shield,     text: 'Données sécurisées & conformes RGPD' },
]

// ── Validation ───────────────────────────────────────────────────
function validate() {
  const errors = {}
  if (!form.email)
    errors.email = 'L\'adresse email est requise.'
  else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email))
    errors.email = 'Entrez une adresse email valide.'
  if (!form.password)
    errors.password = 'Le mot de passe est requis.'
  fieldErrors.value = errors
  return Object.keys(errors).length === 0
}

// ── Submit (redirect logic from old login.vue) ───────────────────
async function handleLogin() {
  if (!validate()) return
  const result = await login({ email: form.email, password: form.password })
  if (result.success) {
    const redirect = route.query.redirect || '/dashboard'
    router.push(redirect)
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