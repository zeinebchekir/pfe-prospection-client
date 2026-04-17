<template>
  <div class="bg-white border border-border rounded-xl p-5 shadow-sm">
    <h3 class="font-semibold text-tacir-darkblue text-sm mb-4">
      <Lightbulb class="inline w-4 h-4 mr-1 text-yellow-500" />
      Insights stratégiques
    </h3>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
      <div
        v-for="insight in insights"
        :key="insight.title"
        class="flex gap-3 p-3 rounded-lg border border-border bg-gray-50"
      >
        <component :is="insight.icon" class="w-4 h-4 shrink-0 mt-0.5" :class="insight.iconClass" />
        <div>
          <p class="text-xs font-semibold text-tacir-darkblue">{{ insight.title }}</p>
          <p class="text-xs text-tacir-darkgray mt-0.5 leading-relaxed">{{ insight.body }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Lightbulb, TrendingUp, Target, Zap, AlertTriangle, Users } from "lucide-vue-next";

const insights = [
  {
    icon: TrendingUp, iconClass: "text-blue-500",
    title: "Grands groupes — levier principal",
    body:  "395 leads représentent ~37% du portefeuille avec un CA moyen de 2.9 Md€. Prioriser les RDV stratégiques et cycles longs.",
  },
  {
    icon: Target, iconClass: "text-cyan-500",
    title: "ETI établies — meilleur ROI volume/valeur",
    body:  "378 leads à 292 M€ CA moyen. Approche account-based et relationship selling pour maximiser le taux de conversion.",
  },
  {
    icon: Zap, iconClass: "text-green-500",
    title: "Petites structures — scalabilité self-serve",
    body:  "204 leads avec faible CA. Automatiser l'onboarding et proposer des offres freemium pour capturer ce volume efficacement.",
  },
  {
    icon: AlertTriangle, iconClass: "text-yellow-500",
    title: "PME énergie & retail — niche à fort potentiel",
    body:  "Seulement 46 leads mais CA moyen de 183 M€. Développer une offre sectorielle verticale dédiée énergie/retail.",
  },
  {
    icon: Users, iconClass: "text-purple-500",
    title: "ETI historiques — vente conseil premium",
    body:  "31 leads à 1.3 Md€ CA moyen. Profils anciens (59 ans) dans le commerce de gros — approche consultative longue durée.",
  },
  {
    icon: TrendingUp, iconClass: "text-tacir-blue",
    title: "Ile-de-France — concentration dominante",
    body:  "3 segments sur 5 ont l'Île-de-France comme région dominante. Renforcer la présence commerciale locale et les événements sectoriels parisiens.",
  },
];
</script>
