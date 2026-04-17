<template>
  <div class="bg-white border border-border rounded-xl shadow-sm overflow-hidden">
    <!-- Toolbar -->
    <div class="flex items-center justify-between gap-3 px-5 py-4 border-b border-border flex-wrap">
      <div>
        <h3 class="font-semibold text-tacir-darkblue text-sm">Explorateur de leads clusterisés</h3>
        <p class="text-xs text-tacir-darkgray">{{ total }} résultats</p>
      </div>
      <div class="flex items-center gap-2 flex-wrap">
        <!-- Segment filter -->
        <select
          v-model="selectedSegment"
          class="text-xs border border-border rounded-lg px-2.5 py-1.5 bg-white text-tacir-darkblue focus:outline-none focus:ring-1 focus:ring-tacir-blue"
        >
          <option :value="null">Tous les segments</option>
          <option v-for="s in segmentOptions" :key="s.cluster" :value="s.cluster">{{ s.label }}</option>
        </select>
        <!-- Search -->
        <div class="relative">
          <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-tacir-darkgray" />
          <input
            v-model="search"
            type="text"
            placeholder="Rechercher..."
            class="text-xs pl-8 pr-3 py-1.5 border border-border rounded-lg bg-white text-tacir-darkblue placeholder:text-tacir-darkgray focus:outline-none focus:ring-1 focus:ring-tacir-blue w-44"
          />
        </div>
      </div>
    </div>

    <!-- Table -->
    <div class="overflow-x-auto">
      <table class="w-full text-xs">
        <thead class="bg-gray-50 border-b border-border">
          <tr>
            <th class="px-4 py-3 text-left font-semibold text-tacir-darkgray uppercase tracking-wider">Entreprise</th>
            <th class="px-4 py-3 text-left font-semibold text-tacir-darkgray uppercase tracking-wider">Segment</th>
            <th class="px-4 py-3 text-left font-semibold text-tacir-darkgray uppercase tracking-wider hidden md:table-cell">Secteur</th>
            <th class="px-4 py-3 text-left font-semibold text-tacir-darkgray uppercase tracking-wider hidden lg:table-cell">Ville</th>
            <th class="px-4 py-3 text-right font-semibold text-tacir-darkgray uppercase tracking-wider">CA</th>
            <th class="px-4 py-3 text-left font-semibold text-tacir-darkgray uppercase tracking-wider hidden xl:table-cell">Région</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="6" class="px-4 py-8 text-center text-tacir-darkgray">Chargement…</td>
          </tr>
          <tr
            v-else
            v-for="lead in leads"
            :key="lead.siren"
            class="border-b border-border/50 hover:bg-gray-50 transition-colors"
          >
            <td class="px-4 py-3">
              <div class="font-medium text-tacir-darkblue truncate max-w-[180px]">{{ lead.nom_entreprise || "—" }}</div>
              <div class="text-tacir-darkgray font-mono">{{ lead.siren }}</div>
            </td>
            <td class="px-4 py-3">
              <span
                class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium border"
                :style="segmentStyle(lead.cluster)"
              >
                {{ lead.cluster_label }}
              </span>
            </td>
            <td class="px-4 py-3 hidden md:table-cell text-tacir-darkgray truncate max-w-[140px]">{{ lead.secteur_activite || "—" }}</td>
            <td class="px-4 py-3 hidden lg:table-cell text-tacir-darkgray">{{ lead.ville || "—" }}</td>
            <td class="px-4 py-3 text-right font-medium text-tacir-darkblue">{{ formatRevenue(lead.chiffre_affaires) }}</td>
            <td class="px-4 py-3 hidden xl:table-cell text-tacir-darkgray">{{ lead.region || "—" }}</td>
          </tr>
          <tr v-if="!loading && !leads.length">
            <td colspan="6" class="px-4 py-8 text-center text-tacir-darkgray">Aucun résultat.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div class="flex items-center justify-between px-5 py-3 border-t border-border">
      <span class="text-xs text-tacir-darkgray">Page {{ page + 1 }}</span>
      <div class="flex gap-2">
        <button
          @click="page--"
          :disabled="page === 0"
          class="text-xs px-3 py-1.5 border border-border rounded-lg disabled:opacity-40 hover:bg-gray-50 text-tacir-darkblue"
        >
          Précédent
        </button>
        <button
          @click="page++"
          :disabled="(page + 1) * limit >= total"
          class="text-xs px-3 py-1.5 border border-border rounded-lg disabled:opacity-40 hover:bg-gray-50 text-tacir-darkblue"
        >
          Suivant
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from "vue";
import { Search } from "lucide-vue-next";
import { getLeads, formatRevenue, SEGMENT_META } from "@/services/segmentation.js";

const props = defineProps({ segments: { type: Array, default: () => [] } });

const leads          = ref([]);
const total          = ref(0);
const loading        = ref(false);
const page           = ref(0);
const limit          = 20;
const selectedSegment = ref(null);
const search         = ref("");

const segmentOptions = props.segments;

function segmentStyle(cluster) {
  const meta = SEGMENT_META[cluster] || { color: "#888" };
  return { backgroundColor: meta.color + "18", color: meta.color, borderColor: meta.color + "33" };
}

async function fetchLeads() {
  loading.value = true;
  try {
    const params = { skip: page.value * limit, limit };
    if (selectedSegment.value !== null) params.segment = selectedSegment.value;
    if (search.value)                    params.search  = search.value;
    const res  = await getLeads(params);
    leads.value = res.data.leads || [];
    total.value = res.data.total || 0;
  } catch (e) {
    leads.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
  }
}

watch([page, selectedSegment], fetchLeads);
watch(search, () => { page.value = 0; fetchLeads(); });
onMounted(fetchLeads);
</script>
