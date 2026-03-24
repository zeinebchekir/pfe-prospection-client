<template>
  <header
    :class="[
      'fixed top-0 left-0 right-0 z-50 transition-all duration-200',
      scrolled
        ? 'bg-white/95 backdrop-blur-sm shadow-sm border-b border-border'
        : 'bg-transparent',
    ]"
  >
    <div class="container mx-auto flex items-center justify-between h-16 px-6">

      <!-- Logo -->
      <div class="flex items-center">
        <img
          src="@/assets/logo.png"
          alt="Qualifix"
          class="h-30 w-auto object-contain"
        />
      </div>

      <!-- Nav links -->
      <nav class="hidden md:flex items-center gap-6">
        <a href="#modules"  class="nav-link">Modules</a>
        <a href="#impact"   class="nav-link">Indicateurs</a>
        <a href="#securite" class="nav-link">Sécurité</a>
      </nav>

      <!-- CTA -->
      <div class="flex items-center gap-3">
        <RouterLink to="/signin">
          <Button variant="ghost" class="text-tacir-blue hover:text-tacir-darkblue font-medium text-sm">
            Se connecter
          </Button>
        </RouterLink>
        <RouterLink to="/signup">
          <Button class="bg-tacir-blue hover:bg-tacir-darkblue text-white text-sm font-semibold rounded-lg inline-flex items-center gap-1.5 px-4 py-2 transition-colors">
            Créer un compte
            <ArrowRight class="w-4 h-4" />
          </Button>
        </RouterLink>
      </div>

    </div>
  </header>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { RouterLink } from 'vue-router'
import { Button } from '@/components/ui/button'
import { ArrowRight } from 'lucide-vue-next'

const scrolled = ref(false)
const onScroll = () => { scrolled.value = window.scrollY > 10 }

onMounted(()  => window.addEventListener('scroll', onScroll))
onUnmounted(() => window.removeEventListener('scroll', onScroll))
</script>

<style scoped>
.nav-link {
  font-size: 0.875rem;
  font-weight: 500;
  color: #7B797A;
  text-decoration: none;
  transition: color 150ms ease;
}
.nav-link:hover { color: #303E8C; }
</style>
