<template>
  <div>
    <div class="flex min-h-screen bg-tacir-lightgray/30">

    <!-- Sidebar -->
    <TheSidebar />

    <!-- Main content -->
    <div class="flex-1 flex flex-col min-w-0">

      <!-- Header -->
      <header class="h-14 sm:h-16 border-b border-border bg-white sticky top-0 z-40 px-3 sm:px-6 flex items-center justify-between shadow-sm">
        <div class="flex items-center gap-2 sm:gap-3 min-w-0">
          <button
            @click="router.push('/commercial/leads')"
            class="w-8 h-8 flex-shrink-0 flex items-center justify-center rounded-lg hover:bg-tacir-lightgray text-tacir-darkgray transition-colors"
          >
            <ArrowLeft class="h-4 w-4" />
          </button>
          <span class="text-xs sm:text-sm text-muted-foreground truncate hidden xs:block sm:block">Mes leads / Fiche entreprise</span>
        </div>
        <div class="flex items-center gap-1.5 sm:gap-2 flex-shrink-0">
          <button
            @click="editOpen = true"
            class="inline-flex items-center gap-1.5 h-8 px-2 sm:px-3 text-sm rounded-md border border-input hover:bg-accent transition-colors"
          >
            <Pencil class="w-3.5 h-3.5" />
            <span class="hidden sm:inline">Modifier</span>
          </button>
          <button
            class="inline-flex items-center gap-1.5 h-8 px-2 sm:px-3 text-sm rounded-md border border-input hover:bg-destructive/10 hover:text-destructive transition-colors"
          >
            <Trash2 class="w-3.5 h-3.5" />
            <span class="hidden sm:inline">Supprimer</span>
          </button>
        </div>
      </header>

      <!-- Loading / Lead not found -->
      <div v-if="!displayLead" class="flex-1 flex items-center justify-center">
        <div v-if="isLoading" class="text-center space-y-3 flex flex-col items-center">
          <Loader2 class="h-8 w-8 animate-spin text-tacir-blue" />
          <p class="text-sm font-medium text-muted-foreground">Chargement...</p>
        </div>
        <div v-else class="text-center space-y-3">
          <p class="text-lg font-medium text-foreground">Lead introuvable</p>
          <button
            @click="router.push('/commercial/leads')"
            class="inline-flex items-center gap-2 h-9 px-4 text-sm rounded-md border border-input hover:bg-accent transition-colors"
          >
            <ArrowLeft class="w-4 h-4" /> Retour à la liste
          </button>
        </div>
      </div>

      <!-- Lead detail -->
      <main v-else class="flex-1 p-6 md:p-8 overflow-y-auto">
        <div class="max-w-[1100px] mx-auto space-y-6">

          <!-- Hero card -->
          <div class="bg-white rounded-xl border border-border shadow-card p-4 sm:p-6">
            <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
              <div class="flex items-center gap-3 sm:gap-4">
                <div class="w-12 h-12 sm:w-14 sm:h-14 rounded-xl bg-blue-50 flex items-center justify-center text-tacir-blue font-semibold text-lg sm:text-xl flex-shrink-0">
                  {{ initials }}
                </div>
                <div class="min-w-0">
                  <h1 class="text-lg sm:text-xl font-semibold text-foreground truncate">{{ displayLead.nom }}</h1>
                  <p class="text-xs sm:text-sm text-muted-foreground mt-0.5">
                    SIREN {{ displayLead.siren }} · {{ displayLead.ville }}, {{ displayLead.pays }}
                  </p>
                  <div class="flex flex-wrap gap-1.5 mt-2">
                    <SegmentBadge :segment="displayLead.segment" />
                    <StatusBadge  :status="displayLead.status"  />
                    <span
                      v-if="displayLead.hasBoamp"
                      class="text-[10px] font-semibold px-2 py-0.5 rounded-sm bg-blue-50 text-tacir-blue border border-blue-200"
                    >
                      BOAMP
                    </span>
                  </div>
                </div>
              </div>
              <!-- Metric chips — wrap naturally on mobile -->
              <div class="flex items-center gap-2 sm:gap-4 flex-wrap">
                <div class="text-center p-2.5 sm:p-3 rounded-xl bg-muted/50 min-w-[64px] sm:min-w-[70px]">
                  <ScoreRing :score="displayLead.score" size="md" />
                  <p class="text-[10px] text-muted-foreground mt-1">Score</p>
                </div>
                <div class="text-center p-2.5 sm:p-3 rounded-xl bg-muted/50 min-w-[64px] sm:min-w-[70px]">
                  <p class="text-base sm:text-lg font-semibold text-foreground">{{ displayLead.probaConversion }}%</p>
                  <p class="text-[10px] text-muted-foreground">Proba.</p>
                </div>
                <div class="text-center p-2.5 sm:p-3 rounded-xl bg-muted/50 min-w-[64px] sm:min-w-[70px]">
                  <p class="text-base sm:text-lg font-semibold text-foreground">{{ displayLead.completude }}%</p>
                  <p class="text-[10px] text-muted-foreground">Complétude</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Two-column detail -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Identité -->
            <div class="bg-white rounded-xl border border-border shadow-card p-5">
              <div class="flex items-center gap-2 mb-4">
                <div class="w-7 h-7 rounded-lg bg-blue-50 flex items-center justify-center">
                  <FileText class="w-3.5 h-3.5 text-tacir-blue" />
                </div>
                <h2 class="text-sm font-semibold">Identité</h2>
              </div>
              <InfoRow label="SIREN"              :value="displayLead.siren" />
              <InfoRow label="SIRET"              :value="displayLead.siret" />
              <InfoRow label="Identifiant"        :value="displayLead.identifiant" />
              <InfoRow label="Taille"             :value="displayLead.tailleEntreprise" badge />
              <InfoRow label="Forme juridique"    :value="displayLead.formeJuridique" />
              <InfoRow label="Date de création"   :value="displayLead.dateCreationFormatted" />
              <InfoRow label="Secteur d'activité" :value="displayLead.secteurActivite" />
              <InfoRow label="Chiffre d'affaires" :value="displayLead.caFormatted" highlight />
              <InfoRow label="Nb locaux"          :value="displayLead.nbLocaux?.toString() ?? '—'" />
            </div>

            <!-- Adresse & Contact -->
            <div class="bg-white rounded-xl border border-border shadow-card p-5">
              <div class="flex items-center gap-2 mb-4">
                <div class="w-7 h-7 rounded-lg bg-emerald-50 flex items-center justify-center">
                  <MapPin class="w-3.5 h-3.5 text-emerald-600" />
                </div>
                <h2 class="text-sm font-semibold">Adresse & contact</h2>
              </div>
              <InfoRow label="Adresse"     value="Non renseigné" muted />
              <InfoRow label="Code postal" :value="displayLead.codePostal" />
              <InfoRow label="Ville"       :value="displayLead.ville" />
              <InfoRow label="Région"      value="Non renseigné" muted />
              <InfoRow label="Pays"        :value="displayLead.pays" />
              <InfoRow label="Email"       :value="displayLead.email" link />
              <InfoRow label="Téléphone"   :value="displayLead.telephone" link />
              <InfoRow label="Site web"    value="Non renseigné" muted />
            </div>
          </div>

          <!-- Dirigeants -->
          <div class="bg-white rounded-xl border border-border shadow-card p-5">
            <div class="flex items-center gap-2 mb-4">
              <div class="w-7 h-7 rounded-lg bg-purple-50 flex items-center justify-center">
                <Users class="w-3.5 h-3.5 text-purple-600" />
              </div>
              <h2 class="text-sm font-semibold">
                Dirigeants & contacts ({{ displayLead.nbDirigeants }})
              </h2>
            </div>
            <p v-if="displayLead.dirigeants.length === 0" class="text-sm text-muted-foreground italic">
              Aucun dirigeant renseigné
            </p>
            <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div
                v-for="(d, i) in displayLead.dirigeants"
                :key="d.id"
                class="flex items-start gap-3 p-3 rounded-xl bg-muted/40 hover:bg-muted/60 transition-colors"
              >
                <div
                  :class="['w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold flex-shrink-0', AVATAR_COLORS[i % AVATAR_COLORS.length]]"
                >
                  {{ d.initials }}
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium text-foreground truncate">{{ d.fullName }}</p>
                  <p class="text-[11px] text-muted-foreground">{{ d.qualite }}</p>
                  <div class="flex items-center gap-3 mt-1.5 flex-wrap">
                    <a
                      v-if="d.email"
                      :href="`mailto:${d.email}`"
                      class="flex items-center gap-1 text-[11px] text-tacir-blue hover:underline"
                    >
                      <Mail class="w-3 h-3" />{{ d.email }}
                    </a>
                    <span v-else class="text-[11px] text-muted-foreground italic">Email non renseigné</span>

                    <a
                      v-if="d.telephone"
                      :href="`tel:${d.telephone}`"
                      class="flex items-center gap-1 text-[11px] text-tacir-blue hover:underline"
                    >
                      <Phone class="w-3 h-3" />{{ d.telephone }}
                    </a>
                    <span v-else class="text-[11px] text-muted-foreground italic">Tél. non renseigné</span>
                  </div>
                </div>
                <div class="flex flex-col items-end gap-1 flex-shrink-0">
                  <div v-if="d.age" class="text-center">
                    <span class="text-base font-semibold text-foreground">{{ d.age }}</span>
                    <span class="text-[10px] text-muted-foreground block">ans</span>
                  </div>
                  <a
                    v-if="d.linkedinUrl"
                    :href="d.linkedinUrl"
                    target="_blank"
                    rel="noreferrer"
                    class="text-blue-600 hover:text-blue-800"
                  >
                    <Linkedin class="w-4 h-4" />
                  </a>
                </div>
              </div>
            </div>
            <!-- Contact completeness -->
            <div class="flex items-center gap-3 mt-4 pt-4 border-t border-border">
              <span class="text-[11px] text-muted-foreground">Complétude contacts</span>
              <div class="flex-1 h-1.5 rounded-full bg-muted overflow-hidden">
                <div
                  class="h-full rounded-full bg-emerald-500 transition-all"
                  :style="{ width: `${contactCompleteness}%` }"
                />
              </div>
              <span class="text-xs font-medium text-emerald-600">{{ contactCompleteness }}%</span>
            </div>
          </div>

          <!-- Indicateurs métier -->
          <div class="bg-white rounded-xl border border-border shadow-card p-5">
            <div class="flex items-center gap-2 mb-4">
              <div class="w-7 h-7 rounded-lg bg-amber-50 flex items-center justify-center">
                <BarChart3 class="w-3.5 h-3.5 text-amber-600" />
              </div>
              <h2 class="text-sm font-semibold">Indicateurs métier</h2>
            </div>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <MetricCard :icon="Target"     label="Score"             :value="`${displayLead.score}/100`" />
              <MetricCard :icon="TrendingUp" label="Proba. conversion" :value="`${displayLead.probaConversion}%`" />
              <MetricCard :icon="Activity"   label="Complétude"        :value="`${displayLead.completude}%`" />
              <MetricCard :icon="Users"      label="Nb dirigeants"     :value="`${displayLead.nbDirigeants}`" />
              <MetricCard :icon="Linkedin"   label="LinkedIn"          :value="displayLead.hasLinkedinDirigeant ? 'Oui' : 'Non'" />
              <MetricCard :icon="Mail"       label="Email"             :value="displayLead.hasEmail ? 'Oui' : 'Non'" />
              <MetricCard :icon="Phone"      label="Téléphone"         :value="displayLead.hasTelephone ? 'Oui' : 'Non'" />
              <MetricCard :icon="Clock"      label="Fraîcheur"         :value="displayLead.dateScrapingFormatted" />
            </div>
          </div>

          <!-- Métadonnées -->
          <div class="bg-white rounded-xl border border-border shadow-card p-5">
            <div class="flex items-center gap-2 mb-4">
              <div class="w-7 h-7 rounded-lg bg-muted flex items-center justify-center">
                <Database class="w-3.5 h-3.5 text-muted-foreground" />
              </div>
              <h2 class="text-sm font-semibold text-muted-foreground">Métadonnées & source</h2>
            </div>
            <div class="grid grid-cols-2 md:grid-cols-3 gap-x-6">
              <InfoRow label="Date création entreprise" :value="displayLead.dateCreationFormatted" />
              <InfoRow label="Dernière modif. site"     :value="displayLead.dateDerniereModifFormatted" />
              <InfoRow label="Date scraping"            :value="displayLead.dateScrapingFormatted" />
              <InfoRow label="Créé le"                  :value="displayLead.createdAt ? formatDateFR(displayLead.createdAt) : '—'" />
              <InfoRow label="Mis à jour le"            :value="displayLead.updatedAt ? formatDateFR(displayLead.updatedAt) : '—'" />
              <InfoRow label="Raw Lead ID"              :value="displayLead.rawLeadId ?? '—'" />
            </div>
            <div v-if="displayLead.sources" class="mt-3 pt-3 border-t border-border">
              <p class="text-[11px] text-muted-foreground mb-1">Sources</p>
              <p class="text-xs font-mono text-muted-foreground bg-muted/50 rounded-lg p-2 overflow-x-auto">
                {{ JSON.stringify(displayLead.sources, null, 0).slice(0, 200) }}…
              </p>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex justify-end gap-3 pb-8">
            <button class="inline-flex items-center gap-2 h-9 px-4 text-sm rounded-md border border-input hover:bg-accent transition-colors">
              <RefreshCw class="w-3.5 h-3.5" /> Prospects similaires
            </button>
            <Button 
              @click="showAnalysis = true"
              class="gap-2 bg-tacir-blue text-white hover:opacity-90"
            >
              <Sparkles class="w-4 h-4" />
              Analyser le potentiel
            </Button>
          </div>

  <LinkedInAnalysisFlow 
    v-if="showAnalysis"
    :is-open="showAnalysis"
    :company-name="displayLead.nom" 
    :company-id="displayLead.id"
    @update:is-open="showAnalysis = $event"
    @analysis-complete="onAnalysisComplete"
  />

        </div>
      </main>
    </div>
  </div>

  <!-- Edit modal -->
  <LeadEditModal
    v-if="displayLead"
    :lead="editOpen ? displayLead : null"
    :open="editOpen"
    @close="editOpen = false"
    @save="handleSave"
  />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowLeft, Pencil, Trash2, MapPin, Phone, Mail, Linkedin,
  Users, FileText, BarChart3, Target, TrendingUp, Activity,
  Clock, Database, RefreshCw, Loader2, Sparkles
} from 'lucide-vue-next'
import { Button } from '@/components/ui/button'

import TheSidebar    from '@/components/AppSidebar.vue'
import SegmentBadge  from '@/components/leads/SegmentBadge.vue'
import StatusBadge   from '@/components/leads/StatusBadge.vue'
import ScoreRing     from '@/components/leads/ScoreRing.vue'
import InfoRow       from '@/components/leads/InfoRow.vue'
import MetricCard    from '@/components/leads/MetricCard.vue'
import LeadEditModal from '@/components/leads/LeadEditModal.vue'
import LinkedInAnalysisFlow from '@/components/leads/LinkedInAnalysisFlow.vue'

import axios from 'axios'
import { adaptLead, formatDateFR } from '@/lib/leadAdapter'

const route  = useRoute()
const router = useRouter()

const leadFromApi = ref(null)
const isLoading = ref(true)

// Local overrides for optimistic edits
const localLead  = ref(null)
const displayLead = computed(() => localLead.value ?? leadFromApi.value)

const editOpen = ref(false)

async function fetchLeadDetails() {
  isLoading.value = true
  try {
    const baseUrl = import.meta.env.VITE_FASTAPI_URL || 'http://localhost:8001'
    const res = await axios.get(`${baseUrl}/entreprises/${route.params.id}`)
    leadFromApi.value = adaptLead(res.data, 0)
  } catch (err) {
    console.error('[LeadDetail] Fetch error:', err)
  } finally {
    isLoading.value = false
  }
}


onMounted(() => {
  fetchLeadDetails()
})

// ---- Computed ----
const initials = computed(() => {
  if (!displayLead.value) return ''
  return displayLead.value.nom
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0] ?? '')
    .join('')
    .toUpperCase()
})

const contactCompleteness = computed(() => {
  if (!displayLead.value || displayLead.value.nbDirigeants === 0) return 0
  const dirs = displayLead.value.dirigeants
  // 3 contact fields per dirigeant: email, telephone, LinkedIn
  const totalFields = dirs.length * 3
  const filledFields = dirs.reduce((sum, d) => {
    return sum
      + (d.email      ? 1 : 0)
      + (d.telephone  ? 1 : 0)
      + (d.linkedinUrl ? 1 : 0)
  }, 0)
  return Math.round((filledFields / totalFields) * 100)
})

// ---- Constants ----
const AVATAR_COLORS = [
  'bg-purple-50 text-purple-700',
  'bg-emerald-50 text-emerald-700',
  'bg-orange-50 text-orange-700',
  'bg-blue-50 text-blue-700',
  'bg-rose-50 text-rose-700',
]

// ---- Analysis Handlers ----
const showAnalysis = ref(false)

const onAnalysisComplete = (data) => {
  showAnalysis.value = false
  // TODO: send data to backend or update local lead implicitly
  console.log('Analysis result:', data)
}

function onAnalysisSkip() {
  console.log('Analyse ignorée')
  showAnalysis.value = false
}

// ---- Handlers ----
function handleSave(id, updates) {
  localLead.value = { ...(displayLead.value ?? {}), ...updates }
  editOpen.value = false
}
</script>

<style scoped>
.shadow-card {
  box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(48,62,140,0.06);
}
</style>
