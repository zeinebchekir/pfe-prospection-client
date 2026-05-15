<template>
  <div
    class="bg-white border border-border rounded-xl shadow-sm border-l-4 hover:shadow-lg transition-all overflow-hidden cursor-pointer group focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2"
    :style="{ borderLeftColor: segment.color }"
    role="button"
    tabindex="0"
    :aria-label="`Voir le détail du segment ${segment.label}`"
    @click="$emit('select', segment)"
    @keydown.enter.prevent="$emit('select', segment)"
    @keydown.space.prevent="$emit('select', segment)"
  >
    <!-- ── Card body ────────────────────────────────────────── -->
    <div class="p-5">

      <!-- Header -->
      <div class="flex items-start justify-between mb-4">
        <div class="flex-1 min-w-0">
          <h3 class="font-semibold text-tacir-darkblue text-sm leading-tight">
            {{ segment.label_short || segment.label }}
          </h3>
          <span
            v-if="segment.label_sub"
            class="inline-block mt-1 text-[10px] font-medium px-2 py-0.5 rounded-full border"
            :style="{ backgroundColor: segment.color + '15', color: segment.color, borderColor: segment.color + '35' }"
          >
            {{ segment.label_sub }}
          </span>
          <div class="flex items-center gap-2 mt-1.5">
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
          <div class="text-sm font-bold text-tacir-darkblue mt-0.5">{{ segment.employes_moyen?.toLocaleString("fr-FR") }}</div>
        </div>
        <div class="bg-gray-50 rounded-lg p-2">
          <div class="text-[10px] text-tacir-darkgray uppercase tracking-wide">Ancienneté moy.</div>
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
          <span class="text-tacir-darkblue font-medium ml-auto truncate">{{ formatSector(segment.secteur_dominant) }}</span>
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

      <!-- Drill-down hint (visible on hover) -->
      <div class="mt-3 flex items-center justify-end gap-1 text-[10px] text-tacir-darkgray/50 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
        <ExternalLink class="w-3 h-3" />
        <span>Voir le détail</span>
      </div>

      <!-- ── Digital Maturity block ──────────────────────────────────── -->
      <div
        v-if="segment.digital_maturity_score != null"
        class="mt-3 pt-2 border-t border-border"
      >
        <button
          @click="maturityOpen = !maturityOpen"
          class="w-full flex items-center justify-between py-1 mb-1 focus:outline-none"
          :class="maturityReasons.length ? 'hover:opacity-80 cursor-pointer' : 'cursor-default'"
          :disabled="!maturityReasons.length"
        >
          <!-- Level badge -->
          <div class="flex items-center gap-2">
            <BarChart2 class="w-3 h-3 text-tacir-darkgray flex-shrink-0" />
            <span class="text-[10px] text-tacir-darkgray">Maturité</span>
            <span
              class="text-[10px] font-semibold px-1.5 py-0.5 rounded-full border"
              :class="maturityBadgeClass"
            >{{ segment.digital_maturity_level }}</span>
          </div>
          <!-- Score + Gap -->
          <div class="flex items-center gap-2 text-[11px]">
            <span class="font-mono font-semibold" :style="{ color: segment.color }">
              {{ segment.digital_maturity_score?.toFixed(1) }}/10
            </span>
            <span class="text-tacir-darkgray">· Écart</span>
            <span class="font-semibold" :class="gapTextClass">
              {{ segment.digital_gap?.toFixed(1) }}
            </span>
            <ChevronDown
              v-if="maturityReasons.length"
              class="w-3.5 h-3.5 text-tacir-darkgray transition-transform duration-200 ml-0.5"
              :class="maturityOpen ? 'rotate-180' : ''"
            />
          </div>
        </button>

        <!-- Adjustment reasons (top 3) -->
        <Transition name="expand">
          <div v-if="maturityOpen && maturityReasons.length" class="space-y-1 mt-1 pb-1">
            <div
              v-for="reason in maturityReasons"
              :key="reason"
              class="flex items-start gap-1.5 text-[10px] text-tacir-darkgray/80"
            >
              <span
                class="w-3 h-3 rounded-full flex items-center justify-center flex-shrink-0 text-[8px] font-bold mt-0.5"
                :style="{ backgroundColor: segment.color + '20', color: segment.color }"
              >→</span>
              <span class="leading-snug">{{ reason }}</span>
            </div>
          </div>
        </Transition>
      </div>
    </div>

    <!-- ── Explainability section ───────────────────────────── -->
    <div
      v-if="topFeatures.length"
      class="border-t border-border"
    >
      <!-- Expand toggle -->
      <button
        @click="explainOpen = !explainOpen"
        class="w-full flex items-center justify-between px-5 py-2.5 text-[11px] font-medium text-tacir-darkgray hover:text-tacir-darkblue hover:bg-gray-50 transition-colors"
      >
        <span class="flex items-center gap-1.5">
          <Lightbulb class="w-3 h-3" :style="{ color: segment.color }" />
          Pourquoi ce segment ?
        </span>
        <ChevronDown
          class="w-3.5 h-3.5 transition-transform duration-200"
          :class="explainOpen ? 'rotate-180' : ''"
        />
      </button>

      <!-- Content -->
      <Transition name="expand">
        <div v-if="explainOpen" class="px-5 pb-4 space-y-2">
          <div
            v-for="feat in topFeatures"
            :key="feat.feature"
            class="flex items-center gap-2 text-[11px]"
          >
            <!-- Direction arrow icon -->
            <span
              class="w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0 text-[9px] font-bold"
              :style="{
                backgroundColor: feat.direction === 'above' ? segment.color + '20' : '#f5f5f5',
                color: feat.direction === 'above' ? segment.color : '#9ca3af'
              }"
            >{{ feat.direction === 'above' ? '↑' : '↓' }}</span>
            <!-- Human-readable text -->
            <span class="text-tacir-darkgray leading-tight">{{ feat.ui_text }}</span>
          </div>
          <p class="text-[10px] text-tacir-darkgray/60 mt-1 italic">
            Comparaison vs la moyenne de {{ totalLeads }} entreprises en base
          </p>
        </div>
      </Transition>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { Building2, Briefcase, MapPin, Lightbulb, ChevronDown, BarChart2, ExternalLink } from "lucide-vue-next";
import { formatRevenue, formatSector } from "@/services/segmentation.js";

const props = defineProps({
  segment:    { type: Object, required: true },
  totalLeads: { type: Number, default: 1 },
});
const emit = defineEmits(["select"]);

const explainOpen = ref(false);
const maturityOpen = ref(false);
const share = computed(() => Math.round((props.segment.n / props.totalLeads) * 100));

// ── Feature name → CEO-friendly French label ─────────────────────────────────
const FEATURE_LABELS_FR = {
  "nb_employes_mid":  "Effectif",
  "chiffre_affaires": "Chiffre d'affaires",
  "nb_locaux":        "Présence multi-sites",
  "age_entreprise":   "Ancienneté",
};

/**
 * Converts raw explainability data into readable French sentences.
 *
 * ratio >= 5  → "largement supérieur(e) à la moyenne (×N)"
 * ratio 2–5   → "supérieur(e) à la moyenne (×N)"
 * ratio 1–2   → "légèrement supérieur(e) à la moyenne"
 * direction=below → same logic but "inférieur(e)"
 */
function toReadableText(feat) {
  const name  = FEATURE_LABELS_FR[feat.feature] || feat.feature;
  const ratio = Math.abs(feat.ratio ?? 1);
  const dir   = feat.direction;
  const gendr = feat.feature === "age_entreprise" || feat.feature === "nb_locaux"
    ? "e" : "";  // feminine suffix for ancienneté / présence

  if (dir === "above") {
    if (ratio >= 5)  return `${name} largement supérieur${gendr} à la moyenne (×${ratio.toFixed(1)})`;
    if (ratio >= 2)  return `${name} supérieur${gendr} à la moyenne (×${ratio.toFixed(1)})`;
    return `${name} légèrement supérieur${gendr} à la moyenne`;
  } else {
    if (ratio <= 0.3) return `${name} très inférieur${gendr} à la moyenne (×${ratio.toFixed(1)})`;
    if (ratio <= 0.7) return `${name} inférieur${gendr} à la moyenne`;
    return `${name} légèrement inférieur${gendr} à la moyenne`;
  }
}

// ── Pull top_features from API response  ─────────────────────────────────────
const topFeatures = computed(() => {
  const raw = props.segment.explainability?.top_features ?? [];
  return raw.slice(0, 3).map((feat) => ({
    ...feat,
    ui_text: toReadableText(feat),
  }));
});

// ── Digital Maturity helpers ──────────────────────────────────────────────────
const MATURITY_BADGE = {
  "Faible": "bg-amber-50 text-amber-700 border-amber-200",
  "Moyen":  "bg-blue-50 text-blue-600 border-blue-200",
  "Élevé":  "bg-green-50 text-green-700 border-green-200",
};

const maturityBadgeClass = computed(() =>
  MATURITY_BADGE[props.segment.digital_maturity_level] || "bg-gray-100 text-gray-500 border-gray-200"
);

const gapTextClass = computed(() => {
  const gap = props.segment.digital_gap ?? 5;
  if (gap >= 7) return "text-amber-600";
  if (gap >= 4) return "text-tacir-lightblue";
  return "text-green-600";
});

// Top 3 adjustment reasons (truncated for card readability)
const maturityReasons = computed(() => {
  const reasons = props.segment.maturity_details?.adjustment_reasons ?? [];
  return reasons.slice(0, 3);
});
</script>

<style scoped>
.expand-enter-active,
.expand-leave-active {
  transition: all 0.22s ease;
  overflow: hidden;
}
.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
}
.expand-enter-to,
.expand-leave-from {
  opacity: 1;
  max-height: 200px;
}
</style>
