<template>
  <section class="pt-24 pb-20 px-6 overflow-hidden hero-gradient">
    <div class="container mx-auto max-w-6xl">
      <div class="grid lg:grid-cols-2 gap-12 items-center">

        <!-- Left: copy -->
        <div class="animate-fade-in">
          <Badge class="mb-5 bg-tacir-lightblue/10 text-tacir-lightblue border border-tacir-lightblue/20 font-semibold text-xs px-3 py-1 rounded-full inline-flex items-center gap-1">
            <Zap class="w-3 h-3" /> Outil interne · Connecté à Boond Manager
          </Badge>

          <h1 class="text-4xl lg:text-5xl font-extrabold text-tacir-darkblue leading-[1.12] mb-5">
            Votre intelligence commerciale,
            <span class="text-gradient"> centralisée et actionnable</span>
          </h1>

          <p class="text-tacir-darkgray text-lg leading-relaxed mb-8 max-w-lg">
            Plateforme interne d'enrichissement, scoring et synchronisation CRM. Donnez à vos équipes
            les bons outils pour qualifier plus vite et mieux décider.
          </p>

          <div class="flex items-center gap-4 flex-wrap">
            <RouterLink to="/signup">
              <Button class="bg-tacir-blue hover:bg-tacir-darkblue text-white h-12 px-7 text-base font-semibold rounded-lg inline-flex items-center gap-2 transition-colors">
                Accéder à la plateforme
                <ArrowRight class="w-4 h-4" />
              </Button>
            </RouterLink>
            <RouterLink to="/signin">
              <Button variant="outline" class="border-tacir-blue text-tacir-blue hover:bg-tacir-blue hover:text-white h-12 px-7 text-base font-semibold rounded-lg transition-colors">
                Se connecter
              </Button>
            </RouterLink>
          </div>

          <div class="flex items-center gap-6 mt-8 flex-wrap">
            <div
              v-for="item in trustItems"
              :key="item"
              class="flex items-center gap-1.5 text-sm text-tacir-darkgray"
            >
              <CheckCircle class="w-4 h-4 text-tacir-green flex-shrink-0" />
              <span>{{ item }}</span>
            </div>
          </div>
        </div>

        <!-- Right: dashboard preview -->
        <div class="animate-fade-in" style="animation-delay: 0.15s">
          <DashboardMock />
        </div>

      </div>
    </div>
  </section>
</template>

<script setup>
import { RouterLink } from 'vue-router'
import { Button } from '@/components/ui/button'
import { Badge }  from '@/components/ui/badge'
import { Zap, ArrowRight, CheckCircle } from 'lucide-vue-next'
import DashboardMock from './DashboardMock.vue'

const trustItems = ['Accès équipe restreint', 'Données internes sécurisées', 'Connecté à Boond']
</script>

<style scoped>
.hero-gradient { background: linear-gradient(180deg, #f2f6ff 0%, #ffffff 100%); }
.text-gradient {
  background: linear-gradient(135deg, #303e8c, #04adbf);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.animate-fade-in { animation: fadeIn 0.5s ease-out both; }
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(16px); }
  to   { opacity: 1; transform: translateY(0); }
}
</style>
