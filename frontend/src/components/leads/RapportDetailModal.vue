<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent class="max-w-2xl max-h-[85vh] flex flex-col p-0 overflow-hidden">

      <!-- Header -->
      <DialogHeader class="px-6 py-4 border-b flex-shrink-0">
        <DialogTitle class="flex items-center gap-2">
          <BarChart2 class="w-5 h-5 text-primary" />
          Rapport #{{ rapport?.identifiant }} — {{ leadNom }}
        </DialogTitle>
      </DialogHeader>

      <!-- Navigation manuelle (remplace Tabs) -->
      <div class="flex items-center gap-1 px-6 pt-3 pb-0 border-b bg-white flex-shrink-0">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          @click="activeTab = tab.key"
          :class="[
            'px-4 py-2 text-sm font-medium rounded-t-md transition-colors border-b-2 -mb-px',
            activeTab === tab.key
              ? 'border-blue-600 text-blue-600 bg-blue-50/60'
              : 'border-transparent text-muted-foreground hover:text-foreground hover:bg-muted/40'
          ]"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- Contenu scrollable -->
      <div class="flex-1 overflow-y-auto">

        <!-- Onglet Analyse -->
        <div v-show="activeTab === 'analyse'" class="p-6 space-y-4">
          <!-- Score -->
          <div class="flex items-center gap-4 p-4 bg-muted/30 rounded-xl border">
            <div
              class="w-14 h-14 rounded-full flex items-center justify-center text-white font-bold text-lg shrink-0"
              :class="getScoreBg(rapport?.potential_score)"
            >
              {{ rapport?.potential_score ?? '—' }}
            </div>
            <div>
              <p class="font-semibold">
                Potentiel :
                <span :class="getScoreTextColor(rapport?.potential_score)">
                  {{ rapport?.potential_score >= 70 ? 'Fort' : rapport?.potential_score >= 40 ? 'Moyen' : 'Faible' }}
                </span>
              </p>
              <p class="text-sm text-muted-foreground mt-0.5">{{ rapport?.recommandation?.slice(0, 120) }}...</p>
            </div>
          </div>

          <!-- Signaux -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div class="rounded-xl border p-4 bg-white">
              <p class="text-xs font-semibold text-emerald-700 uppercase mb-3 flex items-center gap-1">
                <ThumbsUp class="w-3.5 h-3.5" /> Signaux positifs
              </p>
              <ul class="space-y-2">
                <li v-for="(s, i) in rapport?.positive_signals" :key="i"
                  class="text-xs text-emerald-900 flex items-start gap-2">
                  <CheckCircle2 class="w-3.5 h-3.5 text-emerald-500 shrink-0 mt-0.5" /> {{ s }}
                </li>
              </ul>
              <p v-if="!rapport?.positive_signals?.length" class="text-xs text-muted-foreground italic">Aucun signal positif.</p>
            </div>
            <div class="rounded-xl border p-4 bg-white">
              <p class="text-xs font-semibold text-rose-700 uppercase mb-3 flex items-center gap-1">
                <ThumbsDown class="w-3.5 h-3.5" /> Signaux négatifs
              </p>
              <ul class="space-y-2">
                <li v-for="(s, i) in rapport?.negative_signals" :key="i"
                  class="text-xs text-rose-900 flex items-start gap-2">
                  <AlertTriangle class="w-3.5 h-3.5 text-rose-500 shrink-0 mt-0.5" /> {{ s }}
                </li>
              </ul>
              <p v-if="!rapport?.negative_signals?.length" class="text-xs text-muted-foreground italic">Aucun signal négatif.</p>
            </div>
          </div>

          <!-- Besoins -->
          <div v-if="rapport?.needs_it?.length" class="rounded-xl border p-4 bg-white space-y-3">
            <p class="text-xs font-semibold uppercase text-blue-700 flex items-center gap-1">
              <Target class="w-3.5 h-3.5" /> Besoins potentiels
            </p>
            <div v-for="(b, i) in rapport.needs_it" :key="i" class="text-xs p-3 bg-muted/30 rounded-lg border">
              <p class="font-semibold">{{ b.signal || b }}</p>
              <p v-if="b.besoin_it" class="text-muted-foreground mt-1">{{ b.besoin_it }}</p>
            </div>
          </div>
        </div>

        <!-- Onglet Posts -->
        <div v-show="activeTab === 'posts'" class="p-6 space-y-3">
          <div v-if="!rapport?.posts?.length" class="text-sm text-muted-foreground italic text-center py-8">
            Aucun post enregistré pour ce rapport.
          </div>
          <div
            v-else
            v-for="(post, i) in rapport.posts"
            :key="i"
            class="relative rounded-xl border bg-white p-4 overflow-hidden"
          >
            <div class="absolute left-0 top-0 bottom-0 w-1 bg-primary rounded-l-xl"></div>
            <p class="text-sm text-foreground whitespace-pre-wrap ml-3">{{ post }}</p>
          </div>
        </div>

        <!-- Onglet Emails -->
        <div v-show="activeTab === 'emails'" class="p-6 space-y-4">
          <div v-if="!rapport?.emailsgenerated?.length" class="text-sm text-muted-foreground italic text-center py-8">
            Aucun email généré pour ce rapport.
          </div>
          <div
            v-else
            v-for="(email, i) in rapport.emailsgenerated"
            :key="i"
            class="rounded-xl border bg-white p-4 space-y-2"
          >
            <!-- Header row: numéro + date + actions -->
            <div class="flex items-center justify-between">
              <p class="text-xs font-semibold text-muted-foreground uppercase">Email {{ i + 1 }}</p>
              <div class="flex items-center gap-2">
                <span class="text-[11px] text-muted-foreground">{{ formatDate(email.generatedAt) }}</span>
                <button
                  @click="copyEmail(email)"
                  :title="copiedIndex === i ? 'Copié !' : 'Copier'"
                  class="flex items-center gap-1 text-[11px] px-2 py-1 rounded-md border border-border hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                >
                  <Check v-if="copiedIndex === i" class="w-3 h-3 text-emerald-500" />
                  <Copy v-else class="w-3 h-3" />
                  {{ copiedIndex === i ? 'Copié !' : 'Copier' }}
                </button>
                <button
                  @click="openInOutlook(email)"
                  title="Ouvrir dans Outlook"
                  class="flex items-center gap-1 text-[11px] px-2 py-1 rounded-md bg-blue-600 hover:bg-blue-700 text-white transition-colors"
                >
                  <Mail class="w-3 h-3" />
                  Outlook
                </button>
              </div>
            </div>
            <p class="text-sm font-semibold text-foreground border-b pb-2">{{ email.objet }}</p>
            <p class="text-sm text-foreground whitespace-pre-wrap leading-relaxed">{{ email.corps }}</p>
          </div>
        </div>

      </div>

      <DialogFooter class="px-6 py-4 border-t bg-muted/20 flex justify-end gap-2 flex-shrink-0">
        <Button variant="outline" @click="$emit('update:open', false)">Fermer</Button>
        <Button @click="$emit('open-full-page')" class="gap-2 bg-blue-600 hover:bg-blue-700 text-white">
          <ExternalLink class="w-4 h-4" /> Voir rapport complet
        </Button>
      </DialogFooter>

    </DialogContent>
  </Dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import {
  BarChart2, ThumbsUp, ThumbsDown, CheckCircle2,
  AlertTriangle, Target, ExternalLink, Mail, Copy, Check
} from 'lucide-vue-next'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
  DialogFooter
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'

const props = defineProps({ open: Boolean, rapport: Object, leadNom: String })
defineEmits(['update:open', 'open-full-page'])

const copiedIndex = ref(null)

const copyEmail = async (email) => {
  const text = `Objet : ${email.objet}\n\n${email.corps}`
  try {
    await navigator.clipboard.writeText(text)
    const idx = props.rapport?.emailsgenerated?.indexOf(email)
    copiedIndex.value = idx
    setTimeout(() => { copiedIndex.value = null }, 2000)
  } catch (e) {
    console.error('Erreur copie:', e)
  }
}

const openInOutlook = (email) => {
  const subject = encodeURIComponent(email.objet || '')
  const body = encodeURIComponent(email.corps || '')
  const url = `https://outlook.office.com/mail/deeplink/compose?subject=${subject}&body=${body}`
  window.open(url, '_blank')
}

const activeTab = ref('analyse')

// Réinitialise l'onglet actif à chaque ouverture de la modal
watch(() => props.open, (val) => {
  if (val) activeTab.value = 'analyse'
})

const tabs = computed(() => [
  { key: 'analyse', label: 'Analyse' },
  { key: 'posts',   label: `Posts (${props.rapport?.posts?.length || 0})` },
  { key: 'emails',  label: `Emails (${props.rapport?.emailsgenerated?.length || 0})` },
])

const getScoreBg = (s) => {
  if (!s) return 'bg-gray-400'
  if (s >= 70) return 'bg-emerald-500'
  if (s >= 40) return 'bg-orange-500'
  return 'bg-rose-500'
}

const getScoreTextColor = (s) => {
  if (!s) return 'text-gray-500'
  if (s >= 70) return 'text-emerald-600'
  if (s >= 40) return 'text-orange-600'
  return 'text-rose-600'
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('fr-FR', {
    day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'
  })
}
</script>