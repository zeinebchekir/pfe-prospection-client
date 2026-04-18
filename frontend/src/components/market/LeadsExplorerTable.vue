<template>
  <div class="bg-white border border-border rounded-xl shadow-sm overflow-hidden">

    <!-- ── Toolbar ── -->
    <div class="px-4 sm:px-5 py-4 border-b border-border">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h3 class="font-semibold text-tacir-darkblue text-sm">Explorateur de leads clusterisés</h3>
          <p class="text-xs text-tacir-darkgray mt-0.5">
            {{ total }} résultat{{ total !== 1 ? 's' : '' }}
            <span v-if="selectedSegment !== null"> · filtre actif</span>
          </p>
        </div>
        <div class="flex items-center gap-2 flex-wrap">
          <!-- Segment filter -->
          <select
            v-model="selectedSegment"
            class="text-xs border border-border rounded-lg px-2.5 py-1.5 bg-white text-tacir-darkblue focus:outline-none focus:ring-1 focus:ring-tacir-blue"
          >
            <option :value="null">Tous les segments</option>
            <option v-for="s in segments" :key="s.cluster" :value="s.cluster">
              {{ s.label_short || s.label }}{{ s.label_sub ? ' · ' + s.label_sub : '' }}
            </option>
          </select>
          <!-- Search -->
          <div class="relative">
            <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-tacir-darkgray pointer-events-none" />
            <input
              v-model="search"
              type="text"
              placeholder="Rechercher..."
              class="text-xs pl-8 pr-3 py-1.5 border border-border rounded-lg bg-white text-tacir-darkblue placeholder:text-tacir-darkgray focus:outline-none focus:ring-1 focus:ring-tacir-blue w-40 sm:w-48"
            />
          </div>
          <!-- Per-page selector -->
          <select
            v-model="limit"
            @change="page = 0; fetchLeads()"
            class="text-xs border border-border rounded-lg px-2 py-1.5 bg-white text-tacir-darkblue focus:outline-none focus:ring-1 focus:ring-tacir-blue"
          >
            <option :value="10">10 / page</option>
            <option :value="20">20 / page</option>
            <option :value="50">50 / page</option>
          </select>
        </div>
      </div>
    </div>

    <!-- ── Table ── -->
    <div class="overflow-x-auto">
      <table class="w-full text-xs">
        <thead class="bg-gray-50 border-b border-border">
          <tr>
            <th class="px-4 py-3 text-left font-semibold text-tacir-darkgray uppercase tracking-wider">#</th>
            <th class="px-4 py-3 text-left font-semibold text-tacir-darkgray uppercase tracking-wider">Entreprise</th>
            <th class="px-4 py-3 text-left font-semibold text-tacir-darkgray uppercase tracking-wider">Segment</th>
            <th class="px-4 py-3 text-left font-semibold text-tacir-darkgray uppercase tracking-wider hidden md:table-cell">Secteur</th>
            <th class="px-4 py-3 text-left font-semibold text-tacir-darkgray uppercase tracking-wider hidden lg:table-cell">Ville</th>
            <th class="px-4 py-3 text-right font-semibold text-tacir-darkgray uppercase tracking-wider">CA</th>
            <th class="px-4 py-3 text-left font-semibold text-tacir-darkgray uppercase tracking-wider hidden xl:table-cell">Région</th>
          </tr>
        </thead>
        <tbody>
          <!-- Loading state -->
          <tr v-if="loading">
            <td colspan="7" class="px-4 py-10 text-center">
              <div class="flex items-center justify-center gap-2 text-tacir-darkgray">
                <svg class="animate-spin w-4 h-4 text-tacir-blue" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
                </svg>
                Chargement des leads…
              </div>
            </td>
          </tr>
          <!-- Data rows -->
          <tr
            v-else
            v-for="(lead, idx) in leads"
            :key="lead.siren || idx"
            class="border-b border-border/50 hover:bg-tacir-lightgray/30 transition-colors"
          >
            <!-- Row number -->
            <td class="px-4 py-3 text-tacir-darkgray font-mono">
              {{ page * limit + idx + 1 }}
            </td>
            <!-- Company -->
            <td class="px-4 py-3 max-w-[160px]">
              <div class="font-medium text-tacir-darkblue truncate">{{ lead.nom_entreprise || "—" }}</div>
              <div class="text-tacir-darkgray font-mono text-[10px] mt-0.5">{{ lead.siren || "—" }}</div>
            </td>
            <!-- Segment badge -->
            <td class="px-4 py-3">
              <div class="flex flex-col gap-0.5">
                <span
                  class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium border whitespace-nowrap"
                  :style="segmentStyle(lead.cluster)"
                >
                  {{ segmentShortLabel(lead.cluster) || lead.cluster_label }}
                </span>
                <span
                  v-if="segmentSubLabel(lead.cluster)"
                  class="text-[9px] text-gray-400 pl-1"
                >
                  {{ segmentSubLabel(lead.cluster) }}
                </span>
              </div>
            </td>
            <!-- Secteur (md+) -->
            <td class="px-4 py-3 hidden md:table-cell text-tacir-darkgray max-w-[140px]">
              <div class="truncate">{{ lead.secteur_activite || "—" }}</div>
            </td>
            <!-- Ville (lg+) -->
            <td class="px-4 py-3 hidden lg:table-cell text-tacir-darkgray">{{ lead.ville || "—" }}</td>
            <!-- CA -->
            <td class="px-4 py-3 text-right font-medium text-tacir-darkblue whitespace-nowrap">
              {{ formatRevenue(lead.chiffre_affaires) }}
            </td>
            <!-- Région (xl+) -->
            <td class="px-4 py-3 hidden xl:table-cell text-tacir-darkgray">{{ lead.region || "—" }}</td>
          </tr>
          <!-- Empty -->
          <tr v-if="!loading && !leads.length">
            <td colspan="7" class="px-4 py-10 text-center text-tacir-darkgray">
              Aucun résultat pour cette recherche.
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ── Pagination ── -->
    <div class="flex flex-col sm:flex-row items-center justify-between gap-3 px-5 py-3 border-t border-border">
      <!-- Stats -->
      <div class="text-xs text-tacir-darkgray order-2 sm:order-1">
        <span v-if="total > 0">
          Affichage
          <span class="font-semibold text-tacir-darkblue">{{ page * limit + 1 }}</span>–
          <span class="font-semibold text-tacir-darkblue">{{ Math.min((page + 1) * limit, total) }}</span>
          sur
          <span class="font-semibold text-tacir-darkblue">{{ total }}</span>
          résultats
        </span>
      </div>

      <!-- Page buttons -->
      <div class="flex items-center gap-1 order-1 sm:order-2">
        <!-- First page -->
        <button
          @click="goToPage(0)"
          :disabled="page === 0"
          class="w-7 h-7 flex items-center justify-center rounded-lg border border-border text-tacir-darkgray disabled:opacity-30 hover:bg-gray-50 text-xs"
          title="Première page"
        >
          «
        </button>
        <!-- Previous -->
        <button
          @click="goToPage(page - 1)"
          :disabled="page === 0"
          class="w-7 h-7 flex items-center justify-center rounded-lg border border-border text-tacir-darkgray disabled:opacity-30 hover:bg-gray-50"
          title="Page précédente"
        >
          <ChevronLeft class="w-3.5 h-3.5" />
        </button>

        <!-- Numbered page buttons (up to 7 visible) -->
        <template v-for="p in visiblePages" :key="p">
          <span v-if="p === '...'" class="w-7 h-7 flex items-center justify-center text-xs text-tacir-darkgray">…</span>
          <button
            v-else
            @click="goToPage(p)"
            :class="[
              'w-7 h-7 flex items-center justify-center rounded-lg border text-xs font-medium transition-colors',
              p === page
                ? 'bg-tacir-blue text-white border-tacir-blue shadow-sm'
                : 'border-border text-tacir-darkblue hover:bg-gray-50'
            ]"
          >
            {{ p + 1 }}
          </button>
        </template>

        <!-- Next -->
        <button
          @click="goToPage(page + 1)"
          :disabled="page >= totalPages - 1"
          class="w-7 h-7 flex items-center justify-center rounded-lg border border-border text-tacir-darkgray disabled:opacity-30 hover:bg-gray-50"
          title="Page suivante"
        >
          <ChevronRight class="w-3.5 h-3.5" />
        </button>
        <!-- Last page -->
        <button
          @click="goToPage(totalPages - 1)"
          :disabled="page >= totalPages - 1"
          class="w-7 h-7 flex items-center justify-center rounded-lg border border-border text-tacir-darkgray disabled:opacity-30 hover:bg-gray-50 text-xs"
          title="Dernière page"
        >
          »
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from "vue";
import { Search, ChevronLeft, ChevronRight } from "lucide-vue-next";
import { getLeads, formatRevenue, SEGMENT_META } from "@/services/segmentation.js";

const props = defineProps({ segments: { type: Array, default: () => [] } });

// ── State ─────────────────────────────────────────────────────────────────────
const leads           = ref([]);
const total           = ref(0);
const loading         = ref(false);
const page            = ref(0);
const limit           = ref(20);
const selectedSegment = ref(null);
const search          = ref("");

// ── Derived ──────────────────────────────────────────────────────────────────
const totalPages = computed(() => Math.ceil(total.value / limit.value) || 1);

/** Smart page number list with ellipsis, always shows first/last/current ±1 */
const visiblePages = computed(() => {
  const tp = totalPages.value;
  if (tp <= 7) return Array.from({ length: tp }, (_, i) => i);

  const current = page.value;
  const pages = new Set([0, tp - 1, current]);
  if (current > 0)       pages.add(current - 1);
  if (current < tp - 1)  pages.add(current + 1);

  const sorted = [...pages].sort((a, b) => a - b);
  const result = [];
  let prev = -1;
  for (const p of sorted) {
    if (prev !== -1 && p - prev > 1) result.push("...");
    result.push(p);
    prev = p;
  }
  return result;
});

// ── Helpers ───────────────────────────────────────────────────────────────────

// Build a fast lookup map from cluster → segment object (from props.segments)
const segmentMap = computed(() =>
  Object.fromEntries(props.segments.map((s) => [s.cluster, s]))
);

function segmentStyle(cluster) {
  const seg   = segmentMap.value[cluster];
  const color = seg?.color ?? SEGMENT_META[cluster]?.color ?? "#888";
  return {
    backgroundColor: color + "18",
    color:           color,
    borderColor:     color + "33",
  };
}

function segmentShortLabel(cluster) {
  const seg = segmentMap.value[cluster];
  return seg?.label_short || seg?.label || null;
}

function segmentSubLabel(cluster) {
  return segmentMap.value[cluster]?.label_sub || null;
}

function goToPage(p) {
  const clamped = Math.max(0, Math.min(p, totalPages.value - 1));
  if (clamped !== page.value) page.value = clamped;
}

// ── Data fetch ────────────────────────────────────────────────────────────────
async function fetchLeads() {
  loading.value = true;
  try {
    const params = { skip: page.value * limit.value, limit: limit.value };
    if (selectedSegment.value !== null) params.segment = selectedSegment.value;
    if (search.value.trim())             params.search  = search.value.trim();
    const res     = await getLeads(params);
    leads.value   = res.data.leads ?? [];
    total.value   = res.data.total ?? 0;
  } catch {
    leads.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
  }
}

// ── Watchers ──────────────────────────────────────────────────────────────────
watch(page, fetchLeads);
watch(selectedSegment, () => { page.value = 0; fetchLeads(); });
watch(search, () => { page.value = 0; fetchLeads(); });

onMounted(fetchLeads);
</script>
