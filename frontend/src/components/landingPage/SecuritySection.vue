<template>
  <section id="securite" class="py-20 px-6 bg-white">
    <div class="container mx-auto max-w-6xl">
      <div class="grid lg:grid-cols-2 gap-12 items-center">

        <!-- Left: text -->
        <div>
          <p class="section-label mb-3">Sécurité & conformité</p>
          <h2 class="text-3xl font-bold text-tacir-darkblue mb-4">
            Vos données internes méritent une protection de niveau enterprise
          </h2>
          <p class="text-tacir-darkgray text-sm leading-relaxed mb-6">
            TacirIQ est conçu pour les environnements B2B exigeants. Infrastructure sécurisée,
            accès contrôlés par rôle, et conformité RGPD — vos données commerciales restent sous votre contrôle.
          </p>

          <!-- Access restriction banner -->
          <div class="flex items-center gap-3 p-4 bg-tacir-lightgray/60 rounded-xl border border-border">
            <Lock class="w-5 h-5 text-tacir-blue flex-shrink-0" />
            <div>
              <p class="text-tacir-darkblue font-semibold text-sm">Accès restreint à l'équipe interne</p>
              <p class="text-tacir-darkgray text-xs mt-0.5">
                Seuls les comptes autorisés par l'administrateur peuvent accéder à la plateforme.
              </p>
            </div>
          </div>
        </div>

        <!-- Right: cards -->
        <div class="grid sm:grid-cols-2 gap-4">
          <Card
            v-for="s in security"
            :key="s.title"
            class="card-hover border-border shadow-card rounded-xl"
          >
            <CardContent class="p-5">
              <div class="w-9 h-9 rounded-lg bg-tacir-blue/[0.08] flex items-center justify-center mb-3">
                <component :is="s.icon" class="w-4 h-4 text-tacir-blue" />
              </div>
              <h3 class="font-semibold text-tacir-darkblue text-sm mb-1.5">{{ s.title }}</h3>
              <p class="text-tacir-darkgray text-xs leading-relaxed">{{ s.desc }}</p>
            </CardContent>
          </Card>
        </div>

      </div>
    </div>
  </section>
</template>

<script setup>
import { Card, CardContent } from '@/components/ui/card'
import { Server, RefreshCw, ShieldCheck, Users, Lock } from 'lucide-vue-next'

const security = [
  { icon: Server,      title: 'Hébergement cloud sécurisé', desc: 'Infrastructure ISO 27001, redondance multi-zone, disponibilité 99.9%.' },
  { icon: RefreshCw,   title: 'Sauvegardes automatiques',   desc: 'Snapshots quotidiens chiffrés avec rétention 30 jours et restauration en 1 clic.' },
  { icon: ShieldCheck, title: 'RGPD compliant',             desc: 'Traitement des données conforme au RGPD, DPA disponible, données hébergées en Europe.' },
  { icon: Users,       title: 'Gestion des droits',         desc: 'Contrôle granulaire des accès par rôle, authentification SSO et MFA.' },
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
