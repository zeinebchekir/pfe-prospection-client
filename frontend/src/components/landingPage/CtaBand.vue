<template>
  <section class="py-16 px-6 bg-tacir-lightgray/40">
    <div class="container mx-auto max-w-3xl text-center">

      <Badge class="mb-5 bg-tacir-blue/10 text-tacir-blue border border-tacir-blue/20 font-semibold text-xs px-3 py-1 rounded-full inline-flex items-center gap-1">
        <Globe class="w-3 h-3" /> Outil interne Tacir
      </Badge>

      <h2 class="text-3xl font-bold text-tacir-darkblue mb-4">
        Prêt à centraliser votre intelligence commerciale ?
      </h2>
      <p class="text-tacir-darkgray mb-8 text-sm leading-relaxed">
        Connectez-vous avec votre compte équipe ou demandez un accès à votre administrateur TacirIQ.
      </p>

      <div class="flex items-center justify-center gap-4 flex-wrap">
        <template v-if="!isAuthenticated">
          <RouterLink to="/login">
            <Button class="bg-tacir-blue hover:bg-tacir-darkblue text-white h-12 px-8 text-base font-semibold rounded-lg inline-flex items-center gap-2 transition-colors">
              Accéder à la plateforme
              <ArrowRight class="w-4 h-4" />
            </Button>
          </RouterLink>
          <RouterLink to="/register">
            <Button variant="outline" class="border-tacir-blue text-tacir-blue hover:bg-tacir-blue hover:text-white h-12 px-8 text-base font-semibold rounded-lg transition-colors">
              Créer un compte
            </Button>
          </RouterLink>
        </template>
        <template v-else>
          <RouterLink :to="dashboardUrl">
            <Button class="bg-tacir-blue hover:bg-tacir-darkblue text-white h-12 px-8 text-base font-semibold rounded-lg inline-flex items-center gap-2 transition-colors">
              <LayoutDashboard class="w-5 h-5" />
              Aller au Dashboard
              <ArrowRight class="w-4 h-4" />
            </Button>
          </RouterLink>
        </template>
      </div>

    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import { Button } from '@/components/ui/button'
import { Badge }  from '@/components/ui/badge'
import { ArrowRight, Globe, LayoutDashboard } from 'lucide-vue-next'

const { isAuthenticated, user } = useAuth()

const dashboardUrl = computed(() => {
  const role = user.value?.role
  if (role === 'ADMIN') return '/admin'
  if (role === 'CEO') return '/manager'
  if (role === 'COMMERCIAL') return '/commercial'
  return '/dashboard'
})
</script>
