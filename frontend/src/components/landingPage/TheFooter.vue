<template>
  <footer class="bg-tacir-darkblue py-12 px-6">
    <div class="container mx-auto max-w-6xl">
      <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-8 mb-10">
        <!-- Brand -->
        <div class="lg:col-span-2">
          <div class="flex items-center gap-2 mb-4">
            <div
              class="w-7 h-7 rounded-lg bg-white/10 flex items-center justify-center"
            >
              <Zap class="w-3.5 h-3.5 text-tacir-lightblue" />
            </div>
            <div class="flex items-center">
              <img
                src="@/assets/logo-blanc.png"
                alt="Qualifix"
                class="h-30 w-auto object-contain"
              />
            </div>
            <span
              class="ml-2 bg-white/10 text-white/60 text-[10px] px-2 py-0.5 rounded-full"
            >
              Interne
            </span>
          </div>
          <p class="text-white/60 text-xs leading-relaxed max-w-xs">
            Outil interne d'intelligence commerciale connecté à Boond Manager.
            Réservé aux équipes Numeryx.
          </p>
        </div>

        <!-- Link columns -->
        <div v-for="col in footerCols" :key="col.title">
          <h4 class="text-white font-semibold text-sm mb-3">{{ col.title }}</h4>
          <ul class="space-y-2">
            <li v-for="link in col.links" :key="link">
              <a
                href="#"
                class="text-white/50 hover:text-white text-xs transition-colors duration-150"
              >
                {{ link }}
              </a>
            </li>
          </ul>
        </div>
      </div>

      <Separator class="bg-white/10 mb-6" />

      <div class="flex flex-col sm:flex-row items-center justify-between gap-3">
        <p class="text-white/40 text-xs">
          © 2026 Numeryx — Usage interne uniquement.
        </p>
        <div class="flex items-center gap-1.5">
          <div class="w-1.5 h-1.5 rounded-full bg-tacir-green animate-pulse" />
          <span class="text-white/40 text-xs"
            >Tous les systèmes opérationnels</span
          >
        </div>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { Separator } from "@/components/ui/separator";
import { Zap } from "lucide-vue-next";

const footerCols = [
  {
    title: "Modules",
    links: [
      "Enrichissement",
      "Scoring IA",
      "Website Tracking",
      "Synchronisation CRM",
      "Dashboards",
    ],
  },
  {
    title: "Accès & Support",
    links: [
      "Documentation interne",
      "Demander un accès",
      "Signaler un bug",
      "Contact admin",
    ],
  },
];
</script>
