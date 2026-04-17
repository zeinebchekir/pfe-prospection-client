<template>
  <div
    class="p-5 bg-white border border-border rounded-xl shadow-sm border-l-4 hover:shadow-md transition-all"
    :style="{ borderLeftColor: segment.color }"
  >
    <!-- Header -->
    <div class="flex items-start justify-between mb-4">
      <div class="flex-1 min-w-0">
        <h3 class="font-semibold text-tacir-darkblue text-sm leading-tight">{{ segment.label }}</h3>
        <div class="flex items-center gap-2 mt-1">
          <span class="text-2xl font-bold" :style="{ color: segment.color }">{{ segment.n }}</span>
          <span class="text-xs text-tacir-darkgray">leads · {{ share }}% du portefeuille</span>
        </div>
      </div>
      <span class="text-[10px] font-mono border border-border rounded px-1.5 py-0.5 text-tacir-darkgray shrink-0">
        C{{ segment.cluster }}
      </span>
    </div>

    <!-- Stats row -->
    <div class="grid grid-cols-3 gap-2 mb-4">
      <div class="bg-gray-50 rounded-lg p-2">
        <div class="text-[10px] text-tacir-darkgray uppercase tracking-wide">CA moyen</div>
        <div class="text-sm font-bold text-tacir-darkblue mt-0.5">{{ formatRevenue(segment.ca_moyen) }}</div>
      </div>
      <div class="bg-gray-50 rounded-lg p-2">
        <div class="text-[10px] text-tacir-darkgray uppercase tracking-wide">Effectif</div>
        <div class="text-sm font-bold text-tacir-darkblue mt-0.5">{{ segment.employes_moyen.toLocaleString("fr-FR") }}</div>
      </div>
      <div class="bg-gray-50 rounded-lg p-2">
        <div class="text-[10px] text-tacir-darkgray uppercase tracking-wide">Âge moy.</div>
        <div class="text-sm font-bold text-tacir-darkblue mt-0.5">{{ segment.age_moyen }} ans</div>
      </div>
    </div>

    <!-- Details -->
    <div class="space-y-1.5 mb-4">
      <div class="flex items-center gap-2 text-xs">
        <Building2 class="w-3 h-3 text-tacir-darkgray shrink-0" />
        <span class="text-tacir-darkgray">Catégorie</span>
        <span class="text-tacir-darkblue font-medium ml-auto truncate">{{ segment.categorie_dominante }}</span>
      </div>
      <div class="flex items-center gap-2 text-xs">
        <Briefcase class="w-3 h-3 text-tacir-darkgray shrink-0" />
        <span class="text-tacir-darkgray">Secteur</span>
        <span class="text-tacir-darkblue font-medium ml-auto truncate">{{ segment.secteur_dominant }}</span>
      </div>
      <div class="flex items-center gap-2 text-xs">
        <MapPin class="w-3 h-3 text-tacir-darkgray shrink-0" />
        <span class="text-tacir-darkgray">Région</span>
        <span class="text-tacir-darkblue font-medium ml-auto">{{ segment.region_dominante }}</span>
      </div>
    </div>

    <!-- Recommendation badge -->
    <span
      class="inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-medium border"
      :style="{ backgroundColor: segment.color + '18', color: segment.color, borderColor: segment.color + '33' }"
    >
      {{ segment.recommendation }}
    </span>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { Building2, Briefcase, MapPin } from "lucide-vue-next";
import { formatRevenue } from "@/services/segmentation.js";

const props = defineProps({
  segment:    { type: Object, required: true },
  totalLeads: { type: Number, default: 1 },
});

const share = computed(() => Math.round((props.segment.n / props.totalLeads) * 100));
</script>
