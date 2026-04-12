<template>
  <section id="modules" class="py-20 px-6 bg-tacir-lightgray/30">
    <div class="container mx-auto max-w-6xl">

      <div class="text-center mb-12">
        <p class="section-label mb-3">Modules disponibles</p>
        <h2 class="text-3xl font-bold text-tacir-darkblue">
          Tout ce dont l'équipe a besoin, dans un seul outil
        </h2>
        <p class="text-tacir-darkgray mt-3 max-w-xl mx-auto text-sm leading-relaxed">
          Chaque module couvre un besoin précis de notre processus commercial — de la qualification initiale au closing.
        </p>
      </div>

      <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card
          v-for="s in modules"
          :key="s.title"
          class="card-hover bg-white border-border shadow-card rounded-2xl overflow-hidden group"
        >
          <CardContent class="p-6">
            <div :class="`w-11 h-11 rounded-xl ${s.bg} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-200`">
              <component :is="s.icon" :class="`w-5 h-5 ${s.color}`" />
            </div>
            <div class="flex items-start justify-between mb-2">
              <h3 class="font-semibold text-tacir-darkblue text-sm leading-snug flex-1 pr-2">{{ s.title }}</h3>
              <Badge class="bg-tacir-lightgray text-tacir-darkgray border-0 text-[10px] px-2 py-0.5 flex-shrink-0">
                {{ s.badge }}
              </Badge>
            </div>
            <p class="text-tacir-darkgray text-xs leading-relaxed">{{ s.desc }}</p>
            <div :class="`mt-4 flex items-center gap-1 text-xs font-medium ${s.color} opacity-0 group-hover:opacity-100 transition-opacity duration-200`">
              Explorer <ChevronRight class="w-3 h-3" />
            </div>
          </CardContent>
        </Card>
      </div>

    </div>
  </section>
</template>

<script setup>
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Database, Star, Activity, BarChart2, RefreshCw, LayoutDashboard, ChevronRight } from 'lucide-vue-next'

const modules = [
  { icon: Database,       title: 'Enrichissement automatique',   desc: 'Données juridiques, financières et sectorielles issues de multiples sources, centralisées dans votre CRM.',                              badge: 'Multi-sources',      color: 'text-tacir-blue',      bg: 'bg-tacir-blue/[0.08]'      },
  { icon: Star,           title: 'Scoring intelligent',           desc: "Algorithmes multi-critères dynamiques adaptés à votre historique de conversion et à vos segments cibles.",                               badge: 'IA prédictive',       color: 'text-tacir-green',     bg: 'bg-tacir-green/[0.08]'     },
  { icon: Activity,       title: 'Website tracking',              desc: "Détection en temps réel des signaux d'intérêt et comportements visiteurs sur vos propriétés digitales.",                                  badge: 'Temps réel',          color: 'text-tacir-lightblue', bg: 'bg-tacir-lightblue/[0.10]' },
  { icon: RefreshCw,      title: 'Sync bidirectionnelle CRM',     desc: 'Connexion native avec Boond Manager — données toujours à jour, dans les deux sens, sans intervention manuelle.',                         badge: 'Boond natif',         color: 'text-tacir-darkblue',  bg: 'bg-tacir-darkblue/[0.08]'  },
  { icon: LayoutDashboard,title: 'Dashboards décisionnels',       desc: "Visualisations claires et actionnables pour piloter la performance commerciale de l'équipe.",                                            badge: 'Interactif',          color: 'text-tacir-blue',      bg: 'bg-tacir-blue/[0.08]'      },
  { icon: BarChart2,      title: 'Analyse marché & segmentation', desc: 'Cartographiez votre marché, segmentez vos cibles et identifiez les niches à fort potentiel.',                                            badge: 'Intelligence marché', color: 'text-tacir-green',     bg: 'bg-tacir-green/[0.08]'     },
]
</script>

<style scoped>
.section-label {
  display: block;
  color: #303E8C;
  font-weight: 600;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}
.shadow-card { box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(48,62,140,0.06); }
.card-hover  { transition: transform 200ms ease, box-shadow 200ms ease; }
.card-hover:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(48,62,140,0.12);
}
</style>
