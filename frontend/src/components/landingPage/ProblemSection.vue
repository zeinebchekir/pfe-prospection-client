<template>
  <section class="py-20 px-6 bg-white">
    <div class="container mx-auto max-w-6xl">

      <div class="text-center mb-12">
        <p class="section-label mb-3">Ce qu'on cherche à résoudre</p>
        <h2 class="text-3xl font-bold text-tacir-darkblue">
          Les frictions commerciales qu'on adresse
        </h2>
      </div>

      <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <Card
          v-for="p in challenges"
          :key="p.title"
          class="card-hover border-border shadow-card rounded-xl"
        >
          <CardContent class="p-6">
            <div class="w-10 h-10 rounded-lg bg-tacir-lightgray flex items-center justify-center mb-4">
              <component :is="p.icon" class="w-5 h-5 text-tacir-blue" />
            </div>
            <h3 class="font-semibold text-tacir-darkblue mb-2 text-sm">{{ p.title }}</h3>
            <p class="text-tacir-darkgray text-xs leading-relaxed">{{ p.desc }}</p>
          </CardContent>
        </Card>
      </div>

    </div>
  </section>
</template>

<script setup>
import { Card, CardContent } from '@/components/ui/card'
import { Database, TrendingDown, UserX, Clock } from 'lucide-vue-next'

const challenges = [
  { icon: Database,     title: 'Données CRM incomplètes',    desc: 'Fiches leads vides ou obsolètes qui freinent la prise de décision commerciale interne.' },
  { icon: TrendingDown, title: 'Scoring manuel laborieux',   desc: 'Prioritisation chronophage, sujette aux biais, peu cohérente entre équipes.' },
  { icon: UserX,        title: 'Opportunités manquées',      desc: "Des signaux d'intérêt passent inaperçus, vos leads chauds refroidissent avant d'être traités." },
  { icon: Clock,        title: 'Temps commercial fragmenté', desc: "Les équipes sales consacrent 40% de leur temps à la qualification, pas à la vente." },
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
