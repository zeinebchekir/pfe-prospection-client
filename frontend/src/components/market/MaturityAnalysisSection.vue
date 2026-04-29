<template>
  <section>
    <!-- ── Section header ───────────────────────────────────────────── -->
    <div class="mb-4 flex items-center gap-2.5">
      <div class="w-8 h-8 rounded-lg bg-tacir-blue/10 flex items-center justify-center flex-shrink-0">
        <Sparkles class="w-4 h-4 text-tacir-blue" />
      </div>
      <div>
        <h2 class="font-semibold text-tacir-darkblue text-sm">Analyse de maturité numérique</h2>
        <p class="text-[11px] text-tacir-darkgray">
          Niveau d'adoption digitale par segment · potentiel de transformation
          <span v-if="portfolioAvg !== null" class="font-semibold text-tacir-darkblue ml-1">
            · Portefeuille : {{ portfolioAvg }}/10
          </span>
        </p>
      </div>
    </div>

    <!-- No data state -->
    <div
      v-if="!validSegments.length"
      class="bg-white border border-border rounded-xl p-6 text-center text-tacir-darkgray text-xs"
    >
      Données de maturité non disponibles. Relancez l'analyse pour les calculer.
    </div>

    <!-- ── Main grid: distribution (5 cols) + opportunities (3 cols) ── -->
    <div v-else class="grid grid-cols-1 lg:grid-cols-8 gap-4">

      <!-- ══ Panel A — Distribution stacked bars ════════════════════════ -->
      <div class="lg:col-span-5 bg-white border border-border rounded-xl p-5 shadow-sm">
        <!-- Panel header -->
        <div class="mb-4 flex items-start justify-between flex-wrap gap-2">
          <div>
            <h3 class="font-semibold text-tacir-darkblue text-sm">Répartition de la maturité par segment</h3>
            <p class="text-[11px] text-tacir-darkgray">% de leads par niveau dans chaque segment</p>
          </div>
          <!-- Legend -->
          <div class="flex items-center gap-3 text-[11px] flex-shrink-0">
            <span v-for="lvl in LEVELS" :key="lvl.key" class="flex items-center gap-1.5">
              <span class="w-2.5 h-2.5 rounded-sm flex-shrink-0" :style="{ backgroundColor: lvl.color }" />
              <span class="text-tacir-darkgray">{{ lvl.label }}</span>
            </span>
          </div>
        </div>

        <!-- Stacked bars -->
        <div class="space-y-3.5">
          <div v-for="seg in validSegments" :key="seg.cluster" class="space-y-1.5">
            <!-- Row label -->
            <div class="flex items-center justify-between text-xs gap-2">
              <div class="flex items-center gap-2 min-w-0 flex-1">
                <span
                  class="w-2 h-2 rounded-full flex-shrink-0"
                  :style="{ backgroundColor: seg.color }"
                />
                <span class="font-medium text-tacir-darkblue truncate">
                  {{ seg.label_short || seg.label }}
                </span>
                <span
                  class="text-[10px] font-semibold px-1.5 py-0.5 rounded-full border flex-shrink-0"
                  :class="levelBadgeClass(seg.digital_maturity_level)"
                >
                  {{ seg.digital_maturity_level || '—' }}
                </span>
              </div>
              <span class="font-mono text-[11px] text-tacir-darkgray flex-shrink-0">
                {{ seg.digital_maturity_score?.toFixed(1) ?? '—' }}/10
              </span>
            </div>

            <!-- Stacked bar -->
            <div class="flex h-5 w-full overflow-hidden rounded-md bg-gray-100">
              <div
                class="flex items-center justify-center text-[9px] font-semibold text-white/95 transition-all"
                :style="{ width: dist(seg).faible + '%', backgroundColor: LEVELS[0].color }"
                :title="`Faible: ${dist(seg).faible}%`"
              >{{ dist(seg).faible >= 10 ? dist(seg).faible + '%' : '' }}</div>
              <div
                class="flex items-center justify-center text-[9px] font-semibold text-white/95 transition-all"
                :style="{ width: dist(seg).moyen + '%', backgroundColor: LEVELS[1].color }"
                :title="`Moyen: ${dist(seg).moyen}%`"
              >{{ dist(seg).moyen >= 10 ? dist(seg).moyen + '%' : '' }}</div>
              <div
                class="flex items-center justify-center text-[9px] font-semibold text-white/95 transition-all"
                :style="{ width: dist(seg).eleve + '%', backgroundColor: LEVELS[2].color }"
                :title="`Élevé: ${dist(seg).eleve}%`"
              >{{ dist(seg).eleve >= 10 ? dist(seg).eleve + '%' : '' }}</div>
            </div>
          </div>
        </div>

        <!-- Insight strip — segments à fort potentiel -->
        <div
          v-if="highestGapSeg"
          class="mt-5 p-3 rounded-lg bg-amber-50 border border-amber-200 flex items-start gap-2.5"
        >
          <TrendingUp class="w-3.5 h-3.5 text-amber-600 flex-shrink-0 mt-0.5" />
          <p class="text-[11px] text-amber-800 leading-relaxed">
            <span class="font-semibold">Segment à fort potentiel :</span>
            « {{ highestGapSeg.label_short || highestGapSeg.label }} »
            présente le plus grand écart de transformation
            (<span class="font-bold">{{ highestGapSeg.digital_gap?.toFixed(1) }}/10</span>)
            — priorité haute pour les actions commerciales digitales.
          </p>
        </div>
      </div>

      <!-- ══ Panel B — Top 3 transformation opportunities ══════════════ -->
      <div class="lg:col-span-3 bg-white border border-border rounded-xl p-5 shadow-sm">
        <!-- Panel header -->
        <div class="mb-4 flex items-center gap-2">
          <div class="w-7 h-7 rounded-lg bg-amber-50 flex items-center justify-center flex-shrink-0">
            <TrendingUp class="w-3.5 h-3.5 text-amber-500" />
          </div>
          <div>
            <h3 class="font-semibold text-tacir-darkblue text-sm">Fort potentiel de transformation</h3>
            <p class="text-[11px] text-tacir-darkgray">Volume × valeur × écart digital</p>
          </div>
        </div>

        <!-- Top 3 cards -->
        <div class="space-y-2.5">
          <div
            v-for="(seg, idx) in topPotential"
            :key="seg.cluster"
            class="group relative p-3 rounded-lg border border-border bg-gray-50/50 hover:bg-gray-50 hover:border-gray-200 transition-colors"
          >
            <div class="flex items-start gap-3">
              <!-- Rank badge -->
              <div
                class="w-7 h-7 rounded-md flex items-center justify-center text-[11px] font-bold text-white flex-shrink-0"
                :style="{ backgroundColor: seg.color }"
              >{{ idx + 1 }}</div>

              <!-- Content -->
              <div class="min-w-0 flex-1">
                <div class="flex items-center justify-between gap-2 mb-1">
                  <h4 class="text-xs font-semibold text-tacir-darkblue truncate">
                    {{ seg.label_short || seg.label }}
                  </h4>
                  <span
                    class="text-[10px] font-semibold px-1.5 py-0.5 rounded-full border flex-shrink-0"
                    :class="levelBadgeClass(seg.digital_maturity_level)"
                  >{{ seg.digital_maturity_level }}</span>
                </div>

                <div class="flex items-center gap-3 text-[11px] text-tacir-darkgray mb-2">
                  <span>{{ seg.n }} leads</span>
                  <span>·</span>
                  <span>{{ formatRevenue(seg.ca_moyen) }}</span>
                </div>

                <!-- Gap progress bar -->
                <div class="flex items-center gap-2">
                  <span class="text-[10px] uppercase tracking-wide text-tacir-darkgray flex-shrink-0">Écart</span>
                  <div class="flex h-1.5 flex-1 max-w-[80px] overflow-hidden rounded-full bg-gray-200">
                    <div
                      class="rounded-full transition-all"
                      :style="{
                        width: Math.min(100, (seg.digital_gap / 10) * 100) + '%',
                        backgroundColor: gapColor(seg.digital_gap)
                      }"
                    />
                  </div>
                  <span class="text-[10px] font-semibold flex-shrink-0"
                        :style="{ color: gapColor(seg.digital_gap) }">
                    {{ gapLabel(seg.digital_gap) }}
                  </span>
                  <span class="text-[10px] font-mono text-tacir-darkgray ml-auto flex-shrink-0">
                    {{ seg.digital_gap?.toFixed(1) }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <p class="text-[10px] text-tacir-darkgray/70 mt-3 leading-relaxed">
          Classement combinant l'écart digital, le volume de leads et la valeur économique du segment.
        </p>
      </div>

    </div>
  </section>
</template>

<script setup>
import { computed } from "vue";
import { Sparkles, TrendingUp } from "lucide-vue-next";
import { formatRevenue } from "@/services/segmentation.js";

const props = defineProps({
  segments: { type: Array, default: () => [] },
});

// ── Level system ─────────────────────────────────────────────────────────────
const LEVELS = [
  { key: "faible", label: "Faible", color: "#F29F05" },
  { key: "moyen",  label: "Moyen",  color: "#04ADBF" },
  { key: "eleve",  label: "Élevé",  color: "#56A632" },
];

const LEVEL_BADGE = {
  "Faible": "bg-amber-50 text-amber-700 border-amber-200",
  "Moyen":  "bg-tacir-lightblue/10 text-tacir-lightblue border-tacir-lightblue/25",
  "Élevé":  "bg-green-50 text-green-700 border-green-200",
};

function levelBadgeClass(level) {
  return LEVEL_BADGE[level] || "bg-gray-100 text-gray-500 border-gray-200";
}

// ── Filtered segments (only those with maturity data) ────────────────────────
const validSegments = computed(() =>
  (props.segments || []).filter(
    (s) => s.digital_maturity_score != null
  )
);

// ── Portfolio average ─────────────────────────────────────────────────────────
const portfolioAvg = computed(() => {
  if (!validSegments.value.length) return null;
  const totalLeads = validSegments.value.reduce((s, x) => s + (x.n || 0), 0);
  if (!totalLeads) return null;
  const weightedSum = validSegments.value.reduce(
    (s, x) => s + (x.digital_maturity_score ?? 5) * (x.n || 0),
    0
  );
  return (weightedSum / totalLeads).toFixed(1);
});

// ── Maturity distribution accessor ───────────────────────────────────────────
function dist(seg) {
  const d = seg.maturity_details?.maturity_distribution;
  if (d) return { faible: d.faible ?? 33, moyen: d.moyen ?? 34, eleve: d.eleve ?? 33 };
  // Derive from score if distribution missing
  const score = seg.digital_maturity_score ?? 5;
  if (score >= 8) return { faible: 5,  moyen: 30, eleve: 65 };
  if (score >= 5) return { faible: 20, moyen: 55, eleve: 25 };
  return { faible: 65, moyen: 28, eleve: 7 };
}

// ── Gap helpers ───────────────────────────────────────────────────────────────
function gapLabel(gap) {
  if (gap == null) return "—";
  if (gap >= 7) return "Fort";
  if (gap >= 4) return "Modéré";
  return "Faible";
}
function gapColor(gap) {
  if (gap == null) return "#9ca3af";
  if (gap >= 7) return "#F29F05";
  if (gap >= 4) return "#04ADBF";
  return "#56A632";
}

// ── Segment with highest gap ──────────────────────────────────────────────────
const highestGapSeg = computed(() => {
  if (!validSegments.value.length) return null;
  return [...validSegments.value].sort(
    (a, b) => (b.digital_gap ?? 0) - (a.digital_gap ?? 0)
  )[0];
});

// ── Top 3 transformation potential ───────────────────────────────────────────
// Score = (gap / 10) × (n / totalLeads) × (ca_moyen / maxCA)
const topPotential = computed(() => {
  const segs = validSegments.value;
  if (!segs.length) return [];

  const totalLeads = segs.reduce((s, x) => s + (x.n || 0), 0) || 1;
  const maxCA      = Math.max(...segs.map((s) => s.ca_moyen || 0), 1);

  return [...segs]
    .map((s) => ({
      s,
      score:
        ((s.digital_gap ?? 0) / 10) *
        ((s.n || 0) / totalLeads) *
        ((s.ca_moyen || 0) / maxCA),
    }))
    .sort((a, b) => b.score - a.score)
    .slice(0, 3)
    .map((x) => x.s);
});
</script>
