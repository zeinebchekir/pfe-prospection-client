<template>
  <Teleport to="body">
    <div
      v-if="open && segment"
      class="fixed inset-0 z-[9999] flex items-start justify-end"
    >
      <div
        class="absolute inset-0 bg-black/40"
        @click="$emit('close')"
      />

      <div
        class="relative z-10 h-full w-full max-w-2xl bg-white shadow-2xl flex flex-col"
        style="border-left: 4px solid v-bind(accentColor)"
      >
        <div
          class="flex items-start justify-between px-6 py-4 border-b border-gray-200 flex-shrink-0"
          :style="{ borderTop: `4px solid ${segment.color}` }"
        >
          <div class="min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <span class="text-[10px] font-mono border border-gray-300 rounded px-1.5 py-0.5 text-gray-500">
                C{{ segment.cluster }}
              </span>
              <h2 class="font-bold text-gray-900 text-base leading-tight">
                {{ segment.label_short || segment.label }}
              </h2>
              <span
                v-if="segment.label_sub"
                class="text-[11px] font-medium px-2 py-0.5 rounded-full"
                :style="{ backgroundColor: segment.color + '20', color: segment.color }"
              >{{ segment.label_sub }}</span>
            </div>
            <p class="text-xs text-gray-500 mt-1">
              <span class="font-bold" :style="{ color: segment.color }">{{ drilldown?.summary_stats?.count || segment.n }}</span>
              entreprises · {{ share }}% du portefeuille
            </p>
          </div>
          <button
            class="ml-4 flex-shrink-0 p-2 rounded-lg hover:bg-gray-100 text-gray-500 hover:text-gray-800 transition-colors"
            @click="$emit('close')"
          >
            ✕
          </button>
        </div>

        <div class="flex-1 overflow-y-auto p-6 space-y-6">
          <div
            v-if="drilldown?.homogeneity?.warning"
            class="flex items-start gap-2 bg-amber-50 border border-amber-200 text-amber-800 text-xs rounded-lg px-4 py-3"
          >
            ⚠ {{ drilldown.homogeneity.warning }}
          </div>

          <div>
            <h3 class="text-xs font-bold text-gray-700 uppercase tracking-wider mb-3 pb-1 border-b border-gray-200">
              Aperçu statistique
            </h3>
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div
                v-for="kpi in kpiBlocks"
                :key="kpi.label"
                class="bg-gray-50 rounded-xl p-3 border border-gray-100"
              >
                <div class="text-[10px] text-gray-500 uppercase tracking-wide mb-1">{{ kpi.label }}</div>
                <div class="text-lg font-bold" :style="{ color: segment.color }">{{ kpi.stats.mean }}</div>
                <div class="text-[10px] text-gray-400 mt-1">
                  <div>Méd : {{ kpi.stats.median }}</div>
                  <div>Min / Max : {{ kpi.stats.min }} / {{ kpi.stats.max }}</div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="drilldown?.global_comparison">
            <h3 class="text-xs font-bold text-gray-700 uppercase tracking-wider mb-3 pb-1 border-b border-gray-200">
              Comparaison vs portefeuille global
            </h3>
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div
                v-for="d in deltaBlocks"
                :key="d.label"
                class="rounded-xl p-3 border text-center"
                :class="d.value == null ? 'bg-gray-50 border-gray-200 text-gray-400'
                       : d.value >= 0  ? 'bg-green-50 border-green-200 text-green-700'
                                       : 'bg-red-50 border-red-200 text-red-600'"
              >
                <div class="text-[10px] uppercase tracking-wide opacity-70 mb-1">{{ d.label }}</div>
                <div class="text-base font-bold">{{ d.value == null ? '—' : (d.value >= 0 ? '+' : '') + d.value.toFixed(1) + '%' }}</div>
                <div class="text-[10px] opacity-60">vs moy. globale</div>
              </div>
            </div>
          </div>

          <div>
            <h3 class="text-xs font-bold text-gray-700 uppercase tracking-wider mb-3 pb-1 border-b border-gray-200">
              Dimensions dominantes
            </h3>
            <div class="flex flex-wrap gap-2">
              <span class="text-[11px] px-3 py-1.5 rounded-full bg-gray-100 text-gray-700 font-medium">
                Catégorie : {{ drilldown?.dominant_dimensions?.categorie_entreprise || '—' }}
              </span>
              <span class="text-[11px] px-3 py-1.5 rounded-full bg-gray-100 text-gray-700 font-medium">
                Secteur : {{ drilldown?.dominant_dimensions?.secteur_activite || '—' }}
              </span>
              <span class="text-[11px] px-3 py-1.5 rounded-full bg-gray-100 text-gray-700 font-medium">
                Région : {{ drilldown?.dominant_dimensions?.region || '—' }}
              </span>
            </div>
          </div>

          <div v-if="drilldown?.representative_companies?.length">
            <h3 class="text-xs font-bold text-gray-700 uppercase tracking-wider mb-1 pb-1 border-b border-gray-200">
              Entreprises représentatives
            </h3>
            <p class="text-[11px] text-gray-400 italic mb-3">
              Les 5 entreprises les plus représentatives du segment.
            </p>
            <div class="space-y-2">
              <div
                v-for="(c, i) in drilldown.representative_companies"
                :key="c.siren || i"
                class="flex items-center gap-3 px-3 py-2.5 rounded-lg border border-gray-200 bg-gray-50 text-sm"
              >
                <span
                  class="w-1 h-8 rounded-full flex-shrink-0"
                  :style="{ backgroundColor: segment.color }"
                />
                <div class="flex-1 min-w-0">
                  <div class="font-semibold text-gray-800 truncate">{{ c.nom_entreprise || '—' }}</div>
                  <div class="text-xs text-gray-500 truncate">
                    {{ c.ville }}{{ c.secteur_activite ? ' · ' + c.secteur_activite : '' }}
                  </div>
                </div>
                <div class="text-right flex-shrink-0 text-xs text-gray-500">
                  <div v-if="c.chiffre_affaires != null" class="font-mono font-semibold" :style="{ color: segment.color }">
                    {{ formatRevenue(c.chiffre_affaires) }}
                  </div>
                  <div v-if="c.age_entreprise != null">{{ Number(c.age_entreprise).toFixed(0) }} ans</div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="drilldown?.extremes">
            <h3 class="text-xs font-bold text-gray-700 uppercase tracking-wider mb-3 pb-1 border-b border-gray-200">
              Cas extrêmes
            </h3>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <template v-for="ext in extremeBlocks" :key="ext.label">
                <div v-if="ext.company" class="rounded-xl border border-gray-200 bg-gray-50 p-3">
                  <div class="text-[10px] text-gray-500 uppercase tracking-wide mb-1">{{ ext.label }}</div>
                  <div class="font-semibold text-gray-800 truncate text-sm">{{ ext.company.nom_entreprise || '—' }}</div>
                  <div class="text-xs text-gray-500 truncate mb-1">{{ ext.company.ville || '' }}</div>
                  <div class="text-sm font-bold" :style="{ color: segment.color }">{{ ext.display }}</div>
                </div>
              </template>
            </div>
          </div>

          <div v-if="drilldown?.top_lists">
            <h3 class="text-xs font-bold text-gray-700 uppercase tracking-wider mb-3 pb-1 border-b border-gray-200">
              Classements
            </h3>
            <div class="space-y-4">
              <div v-for="table in rankingTables" :key="table.title">
                <div class="text-xs font-semibold text-gray-700 mb-2">{{ table.title }}</div>
                <div class="rounded-lg border border-gray-200 overflow-hidden">
                  <div
                    v-if="!table.rows?.length"
                    class="text-xs text-gray-400 px-3 py-2 italic"
                  >Aucune donnée</div>
                  <div
                    v-for="(row, i) in (table.rows || []).slice(0, 5)"
                    :key="row.siren || i"
                    class="flex items-center gap-3 px-3 py-2 text-xs border-b border-gray-100 last:border-0"
                    :style="i === 0 ? { backgroundColor: segment.color + '12' } : {}"
                  >
                    <span class="font-mono text-gray-400 w-4 text-right flex-shrink-0">{{ i + 1 }}</span>
                    <span class="flex-1 truncate text-gray-800">{{ row.nom_entreprise || '—' }}</span>
                    <span class="font-bold flex-shrink-0" :style="{ color: segment.color }">{{ table.fmt(row) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="drilldown?.homogeneity">
            <h3 class="text-xs font-bold text-gray-700 uppercase tracking-wider mb-3 pb-1 border-b border-gray-200">
              Homogénéité du segment
            </h3>
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div
                v-for="cv in cvBlocks"
                :key="cv.label"
                class="rounded-xl p-3 border text-center"
                :class="cv.value == null ? 'bg-gray-50 border-gray-200 text-gray-400'
                       : cv.value <= 0.5 ? 'bg-green-50 border-green-200 text-green-700'
                       : cv.value <= 1.0 ? 'bg-amber-50 border-amber-200 text-amber-700'
                                         : 'bg-red-50 border-red-200 text-red-600'"
              >
                <div class="text-[10px] uppercase tracking-wide opacity-70 mb-1">{{ cv.label }}</div>
                <div class="text-base font-bold">{{ cv.value != null ? cv.value.toFixed(2) : '—' }}</div>
                <div class="text-[10px] opacity-80">
                  {{ cv.value == null ? '—' : cv.value <= 0.5 ? 'Homogène' : cv.value <= 1.0 ? 'Modéré' : 'Hétérogène' }}
                </div>
              </div>
            </div>
            <p class="text-[10px] text-gray-400 mt-2 italic">
              CV = std / moyenne. Plus il est bas, plus le segment est homogène.
            </p>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed } from "vue";
import { formatRevenue } from "@/services/segmentation.js";

const props = defineProps({
  open: { type: Boolean, required: true },
  segment: { type: Object, default: null },
  totalLeads: { type: Number, default: 1 },
});

defineEmits(["close"]);

const accentColor = computed(() => props.segment?.color ?? "#3b82f6");
const drilldown = computed(() => props.segment?.drilldown ?? {});
const share = computed(() =>
  props.segment ? Math.round((props.segment.n / props.totalLeads) * 100) : 0
);

function formatMetricValue(value) {
  if (value == null) return "—";
  return Number(value).toFixed(1);
}

function formatStatBlock(stats, kind = "number") {
  const empty = {
    mean: "—",
    median: "—",
    min: "—",
    max: "—",
  };

  if (!stats) return empty;

  const formatter = kind === "revenue" ? formatRevenue : formatMetricValue;
  return {
    mean: formatter(stats.mean),
    median: formatter(stats.median),
    min: formatter(stats.min),
    max: formatter(stats.max),
  };
}

const kpiBlocks = computed(() => [
  { label: "CA", stats: formatStatBlock(drilldown.value.summary_stats?.ca, "revenue") },
  { label: "Effectif", stats: formatStatBlock(drilldown.value.summary_stats?.effectif) },
  { label: "Âge (ans)", stats: formatStatBlock(drilldown.value.summary_stats?.age) },
  { label: "Nb locaux", stats: formatStatBlock(drilldown.value.summary_stats?.nb_locaux) },
]);

const deltaBlocks = computed(() => {
  const gc = drilldown.value.global_comparison ?? {};
  return [
    { label: "CA", value: gc.ca_mean_delta_pct },
    { label: "Effectif", value: gc.effectif_mean_delta_pct },
    { label: "Âge", value: gc.age_mean_delta_pct },
    { label: "Nb locaux", value: gc.nb_locaux_mean_delta_pct },
  ];
});

const extremeBlocks = computed(() => {
  const ex = drilldown.value.extremes ?? {};
  return [
    { label: "CA le plus élevé", company: ex.highest_ca, display: ex.highest_ca ? formatRevenue(ex.highest_ca.chiffre_affaires) : "—" },
    { label: "CA le plus faible", company: ex.lowest_ca, display: ex.lowest_ca ? formatRevenue(ex.lowest_ca.chiffre_affaires) : "—" },
    { label: "Effectif le plus grand", company: ex.highest_effectif, display: ex.highest_effectif ? `${ex.highest_effectif.nb_employes_mid} pers.` : "—" },
    { label: "Effectif le plus petit", company: ex.lowest_effectif, display: ex.lowest_effectif ? `${ex.lowest_effectif.nb_employes_mid} pers.` : "—" },
    { label: "La plus ancienne", company: ex.oldest_company, display: ex.oldest_company ? `${Number(ex.oldest_company.age_entreprise).toFixed(0)} ans` : "—" },
    { label: "La plus récente", company: ex.youngest_company, display: ex.youngest_company ? `${Number(ex.youngest_company.age_entreprise).toFixed(0)} ans` : "—" },
  ];
});

const rankingTables = computed(() => {
  const tl = drilldown.value.top_lists ?? {};
  return [
    { title: "Top CA", rows: tl.top_ca, fmt: (row) => row.chiffre_affaires != null ? formatRevenue(row.chiffre_affaires) : "—" },
    { title: "Top Effectif", rows: tl.top_effectif, fmt: (row) => row.nb_employes_mid != null ? `${Number(row.nb_employes_mid).toLocaleString("fr-FR")} p.` : "—" },
    { title: "Plus anciens", rows: tl.oldest, fmt: (row) => row.age_entreprise != null ? `${Number(row.age_entreprise).toFixed(0)} ans` : "—" },
  ];
});

const cvBlocks = computed(() => {
  const h = drilldown.value.homogeneity ?? {};
  return [
    { label: "CA", value: h.ca_cv },
    { label: "Effectif", value: h.effectif_cv },
    { label: "Âge", value: h.age_cv },
    { label: "Nb locaux", value: h.nb_locaux_cv },
  ];
});
</script>
