<template>
  <Sheet :open="isOpen" @update:open="$emit('update:isOpen', $event)">
    <SheetContent class="w-full sm:max-w-2xl flex flex-col p-0 overflow-hidden">
      
      <!-- Header -->
      <SheetHeader class="px-6 py-4 border-b flex-shrink-0">
        <SheetTitle class="flex items-center gap-2">
          <BarChart2 class="w-5 h-5 text-primary" />
          Rapports LinkedIn — {{ leadNom }}
        </SheetTitle>
        <SheetDescription>
          Historique des analyses générées pour ce lead.
        </SheetDescription>
      </SheetHeader>

      <!-- Actions -->
      <div class="px-6 py-3 border-b bg-muted/30 flex items-center justify-between flex-shrink-0">
        <span class="text-sm text-muted-foreground">
          {{ rapports.length }} rapport{{ rapports.length > 1 ? 's' : '' }}
        </span>
        <Button size="sm" @click="confirmNewRapport" class="gap-2 bg-blue-600 hover:bg-blue-700 text-white">
          <Plus class="w-4 h-4" />
          Nouveau rapport
        </Button>
      </div>

      <!-- Liste rapports -->
      <div class="flex-1 overflow-y-auto px-6 py-4 space-y-3">
        
        <div v-if="isLoading" class="flex items-center justify-center py-16">
          <Loader2 class="w-6 h-6 animate-spin text-primary" />
        </div>

        <div v-else-if="rapports.length === 0" class="flex flex-col items-center justify-center py-16 text-center">
          <FileSearch class="w-10 h-10 text-muted-foreground mb-3" />
          <p class="text-sm font-medium text-foreground">Aucun rapport généré</p>
          <p class="text-xs text-muted-foreground mt-1">Lancez une analyse LinkedIn pour créer le premier rapport.</p>
        </div>

        <div
          v-else
          v-for="rapport in rapports"
          :key="rapport.identifiant"
          class="bg-white rounded-xl border border-border shadow-sm p-4 hover:border-blue-200 transition-colors cursor-pointer group"
          @click="openDetail(rapport)"
        >
          <div class="flex items-start justify-between gap-4">
            <!-- Score badge -->
            <div class="flex items-center gap-3">
              <div
                class="w-12 h-12 rounded-full flex flex-col items-center justify-center text-white font-bold text-sm shrink-0"
                :class="getScoreBg(rapport.potential_score)"
              >
                {{ rapport.potential_score ?? '—' }}
              </div>
              <div>
                <p class="text-sm font-semibold text-foreground">
                  Rapport #{{ rapport.identifiant }}
                </p>
                <p v-if="rapport.created_at" class="text-[11px] text-muted-foreground mt-0.5 flex items-center gap-1">
                  <Calendar class="w-3 h-3" />
                  {{ formatDate(rapport.created_at) }}
                </p>
                <p class="text-xs text-muted-foreground mt-0.5 line-clamp-2">
                  {{ rapport.recommandation?.slice(0, 90) || 'Aucune recommandation' }}...
                </p>
              </div>
            </div>

            <!-- Actions -->
            <div class="flex items-center gap-1 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                @click.stop="openDetail(rapport)"
                class="p-1.5 rounded-md hover:bg-muted text-muted-foreground hover:text-foreground"
                title="Aperçu"
              >
                <Eye class="w-4 h-4" />
              </button>
              <button
                @click.stop="openFullPage(rapport)"
                class="p-1.5 rounded-md hover:bg-muted text-muted-foreground hover:text-foreground"
                title="Page complète"
              >
                <ExternalLink class="w-4 h-4" />
              </button>
              <button
                @click.stop="deleteRapport(rapport.identifiant)"
                class="p-1.5 rounded-md hover:bg-red-50 text-muted-foreground hover:text-red-600"
                title="Supprimer"
              >
                <Trash2 class="w-4 h-4" />
              </button>
            </div>
          </div>

          <!-- Signaux pills -->
          <div class="flex flex-wrap gap-2 mt-3 pt-3 border-t border-border/60">
            <span
              v-for="(s, i) in (rapport.positive_signals || []).slice(0, 2)"
              :key="'pos-'+i"
              class="text-[11px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200"
            >
              ✓ {{ s }}
            </span>
            <span
              v-for="(s, i) in (rapport.negative_signals || []).slice(0, 1)"
              :key="'neg-'+i"
              class="text-[11px] px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200"
            >
              ✗ {{ s }}
            </span>
            <span
              v-if="rapport.emailsgenerated?.length"
              class="text-[11px] px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200"
            >
              ✉ {{ rapport.emailsgenerated.length }} email{{ rapport.emailsgenerated.length > 1 ? 's' : '' }}
            </span>
          </div>
        </div>
      </div>
    </SheetContent>
  </Sheet>

  <!-- Modal détail rapport -->
  <RapportDetailModal
    v-if="selectedRapport"
    :open="showDetailModal"
    :rapport="selectedRapport"
    :lead-nom="leadNom"
    @update:open="showDetailModal = $event"
    @open-full-page="openFullPage(selectedRapport)"
  />

  <!-- ⚠️ Modal de confirmation nouvelle analyse -->
  <Dialog :open="showConfirmModal" @update:open="showConfirmModal = $event">
    <DialogContent class="max-w-md">
      <DialogHeader>
        <DialogTitle class="flex items-center gap-2 text-amber-700">
          <AlertTriangle class="w-5 h-5 text-amber-500" />
          Lancer une nouvelle analyse ?
        </DialogTitle>
        <DialogDescription class="pt-2 space-y-2">
          <p class="text-sm text-foreground">
            Cette action va consommer des crédits API pour générer un nouveau rapport d'analyse LinkedIn.
          </p>
          <div v-if="lastRapportDate" class="flex items-center gap-2 p-3 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-sm">
            <Calendar class="w-4 h-4 shrink-0" />
            <span>
              Dernier rapport généré le <strong>{{ lastRapportDate }}</strong>
            </span>
          </div>
          <p v-else class="text-sm text-muted-foreground italic">
            Aucun rapport précédent pour ce lead.
          </p>
          <p class="text-sm text-muted-foreground pt-1">
            Confirmez-vous le lancement de l'analyse ?
          </p>
        </DialogDescription>
      </DialogHeader>
      <DialogFooter class="gap-2 pt-2">
        <Button variant="outline" @click="showConfirmModal = false">Annuler</Button>
        <Button @click="confirmAndLaunch" class="bg-blue-600 hover:bg-blue-700 text-white gap-2">
          <Plus class="w-4 h-4" />
          Confirmer et lancer
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { toast } from 'vue-sonner'
import {
  BarChart2, Plus, Loader2, FileSearch,
  Eye, ExternalLink, Trash2, Calendar, AlertTriangle
} from 'lucide-vue-next'
import {
  Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription
} from '@/components/ui/sheet'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import RapportDetailModal from './RapportDetailModal.vue'

const props = defineProps({
  isOpen: Boolean,
  leadId: [String, Number],
  leadNom: String,
  lead: Object,
})

const emit = defineEmits(['update:isOpen', 'nouveau-rapport'])

const router = useRouter()
const rapports = ref([])
const isLoading = ref(false)
const selectedRapport = ref(null)
const showDetailModal = ref(false)
const showConfirmModal = ref(false)

// Date du dernier rapport (le plus récent = index 0 car trié desc)
const lastRapportDate = computed(() => {
  if (!rapports.value.length) return null
  const last = rapports.value[0]
  return last.created_at ? formatDate(last.created_at) : null
})

const confirmNewRapport = () => {
  showConfirmModal.value = true
}

const confirmAndLaunch = () => {
  showConfirmModal.value = false
  emit('nouveau-rapport')
}

watch(() => props.isOpen, (val) => {
  if (val && props.leadId) fetchRapports()
})

const fetchRapports = async () => {
  isLoading.value = true
  try {
    const { data } = await axios.get(`/potential-linkedin/entreprise/${props.leadId}/all`)
    rapports.value = data
  } catch (err) {
    toast.error('Erreur lors du chargement des rapports')
  } finally {
    isLoading.value = false
  }
}

const getScoreBg = (score) => {
  if (!score) return 'bg-gray-400'
  if (score >= 70) return 'bg-emerald-500'
  if (score >= 40) return 'bg-orange-500'
  return 'bg-rose-500'
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('fr-FR', {
    day: '2-digit', month: 'short', year: 'numeric'
  })
}

const openDetail = (rapport) => {
  selectedRapport.value = rapport
  showDetailModal.value = true
}

const openFullPage = (rapport) => {
  // Reconstruit le format attendu par AnalyseResultsPage
  const result = {
    score: rapport.potential_score,
    signaux_positifs: rapport.positive_signals,
    signaux_negatifs: rapport.negative_signals,
    besoins_potentiels: rapport.needs_it,
    recommandation: rapport.recommandation,
    posts: rapport.posts,
    resume_strategique: rapport.recommandation,
  }
  sessionStorage.setItem('analysisResult', JSON.stringify(result))
  sessionStorage.setItem('analysisLead', JSON.stringify(props.lead))
  router.push({ name: 'AnalyseResults' })
}

const deleteRapport = async (id) => {
  try {
    await axios.delete(`/potential-linkedin/${id}`)
    rapports.value = rapports.value.filter(r => r.identifiant !== id)
    toast.success('Rapport supprimé')
  } catch {
    toast.error('Erreur lors de la suppression')
  }
}
</script>