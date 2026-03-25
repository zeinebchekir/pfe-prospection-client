<template>
  <div class="min-h-screen flex items-center justify-center bg-tacir-lightgray/30 px-6">
    <div class="max-w-md w-full text-center animate-fade-in">
      
      <!-- Icon / Illustration -->
      <div class="mb-8 flex justify-center">
        <div class="relative">
          <div class="absolute -inset-4 bg-tacir-blue/10 rounded-full blur-xl animate-pulse" />
          <div class="relative w-24 h-24 bg-white rounded-3xl shadow-xl border border-border flex items-center justify-center">
            <SearchX class="w-12 h-12 text-tacir-blue" />
          </div>
        </div>
      </div>

      <!-- Content -->
      <h1 class="text-6xl font-black text-tacir-darkblue mb-2 tracking-tighter">404</h1>
      <h2 class="text-2xl font-bold text-tacir-darkblue mb-4">Page introuvable</h2>
      <p class="text-tacir-darkgray mb-10 text-sm leading-relaxed max-w-[280px] mx-auto">
        Désolé, la page que vous recherchez n'existe pas ou a été déplacée.
      </p>

      <!-- Actions -->
      <div class="flex flex-col gap-3">
        <Button 
          @click="handleGoBack"
          class="h-12 bg-tacir-blue hover:bg-tacir-darkblue text-white rounded-xl font-semibold transition-all active:scale-95 flex items-center justify-center gap-2"
        >
          <ArrowLeft class="w-4 h-4" />
          Retourner à l'accueil
        </Button>
        
        <Button 
          variant="ghost"
          @click="router.push('/login')"
          v-if="!isAuthenticated"
          class="text-tacir-darkgray hover:text-tacir-blue font-medium"
        >
          Se connecter
        </Button>
      </div>

      <!-- Support link -->
      <p class="mt-12 text-[11px] text-tacir-darkgray font-medium uppercase tracking-widest">
        Besoin d'aide ? <a href="mailto:support@qualifix.fr" class="text-tacir-blue hover:underline">Contactez le support</a>
      </p>

    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import { Button } from '@/components/ui/button'
import { SearchX, ArrowLeft } from 'lucide-vue-next'

const router = useRouter()
const { isAuthenticated, user } = useAuth()

function handleGoBack() {
  if (isAuthenticated.value) {
    // Redirect based on role
    const role = user.value?.role
    if (role === 'ADMIN') router.push('/admin')
    else if (role === 'CEO') router.push('/manager')
    else if (role === 'COMMERCIAL') router.push('/commercial')
    else router.push('/')
  } else {
    router.push('/')
  }
}
</script>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.5s ease-out both;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
