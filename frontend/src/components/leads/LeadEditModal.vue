<template>
  <Dialog :open="open" @update:open="emit('close')">
    <DialogContent class="max-w-2xl max-h-[90vh] p-0 flex flex-col overflow-hidden">
      <template v-if="lead">
        <!-- Header -->
        <DialogHeader class="p-6 pb-0 flex-shrink-0">
          <DialogTitle class="text-lg font-semibold">
            Modifier le lead — {{ lead.nom }}
          </DialogTitle>
        </DialogHeader>

        <!-- Tabs nav -->
        <div class="px-6 pt-4 flex-shrink-0">
          <div class="flex border-b border-border gap-1">
            <button
              v-for="tab in tabs"
              :key="tab.key"
              @click="activeTab = tab.key"
              :class="[
                'px-4 py-2 text-xs font-medium border-b-2 -mb-px transition-colors',
                activeTab === tab.key
                  ? 'border-tacir-blue text-tacir-blue'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              ]"
            >
              {{ tab.label }}
              <span
                v-if="tab.key === 'dirigeants' && modalDirigeants.length"
                class="ml-1 text-[10px] font-semibold bg-muted text-muted-foreground px-1.5 py-0.5 rounded-full"
              >
                {{ modalDirigeants.length }}
              </span>
            </button>
          </div>
        </div>

        <!-- Tab content -->
        <div class="flex-1 overflow-y-auto px-6 py-4 relative">

          <!-- ── Informations ── -->
          <div v-if="activeTab === 'general'" class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-1.5">
                <label class="text-[11px] font-medium text-muted-foreground">Nom de l'entreprise</label>
                <input v-model="form.nom" type="text" v-bind="inputClass" />
              </div>
              <div class="space-y-1.5">
                <label class="text-[11px] font-medium text-muted-foreground">SIREN</label>
                <input v-model="form.siren" type="text" v-bind="inputClass" />
              </div>
              <div class="space-y-1.5">
                <label class="text-[11px] font-medium text-muted-foreground">SIRET</label>
                <input v-model="form.siret" type="text" v-bind="inputClass" />
              </div>
              <div class="space-y-1.5">
                <label class="text-[11px] font-medium text-muted-foreground">Identifiant</label>
                <input v-model="form.identifiant" type="text" v-bind="inputClass" />
              </div>
              <div class="space-y-1.5">
                <label class="text-[11px] font-medium text-muted-foreground">Taille entreprise</label>
                <input v-model="form.tailleEntreprise" type="text" v-bind="inputClass" disabled />
              </div>
              <div class="space-y-1.5">
                <label class="text-[11px] font-medium text-muted-foreground">Secteur d'activité</label>
                <input v-model="form.secteurActivite" type="text" v-bind="inputClass" />
              </div>
              <div class="space-y-1.5">
                <label class="text-[11px] font-medium text-muted-foreground">Forme juridique</label>
                <input v-model="form.formeJuridique" type="text" v-bind="inputClass" />
              </div>
              <div class="space-y-1.5">
                <label class="text-[11px] font-medium text-muted-foreground">CA (affiché)</label>
                <input v-model="form.caFormatted" type="text" v-bind="inputClass" disabled />
              </div>
            </div>

            <!-- Statut -->
            <div class="space-y-1.5">
              <label class="text-[11px] font-medium text-muted-foreground">Statut</label>
              <select v-model="form.status" class="w-full h-9 text-sm rounded-md border border-input bg-background px-3 focus:outline-none focus:ring-2 focus:ring-ring">
                <option value="Nouveau">Nouveau</option>
                <option value="Qualifié">Qualifié</option>
                <option value="Opportunité">Opportunité</option>
              </select>
            </div>
          </div>

          <!-- ── Contact ── -->
          <div v-if="activeTab === 'contact'" class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-1.5">
                <label class="text-[11px] font-medium text-muted-foreground">Ville</label>
                <input v-model="form.ville" type="text" v-bind="inputClass" />
              </div>
              <div class="space-y-1.5">
                <label class="text-[11px] font-medium text-muted-foreground">Code postal</label>
                <input v-model="form.codePostal" type="text" v-bind="inputClass" />
              </div>
              <div class="space-y-1.5">
                <label class="text-[11px] font-medium text-muted-foreground">Pays</label>
                <input v-model="form.pays" type="text" v-bind="inputClass" />
              </div>
              <div class="space-y-1.5">
                <label class="text-[11px] font-medium text-muted-foreground">Téléphone</label>
                <input v-model="form.telephone" type="tel" v-bind="inputClass" />
              </div>
              <div class="col-span-2 space-y-1.5">
                <label class="text-[11px] font-medium text-muted-foreground">Email</label>
                <input v-model="form.email" type="email" v-bind="inputClass" />
              </div>
            </div>
          </div>

          <!-- ── Dirigeants (editable) ── -->
          <div v-if="activeTab === 'dirigeants'" class="space-y-4">
            <!-- Header row -->
            <div class="flex items-center justify-between">
              <p class="text-xs text-muted-foreground flex items-center gap-1.5">
                <Users class="w-3.5 h-3.5" />
                <span>{{ modalDirigeants.length }} dirigeant{{ modalDirigeants.length > 1 ? 's' : '' }}</span>
                <span class="text-[10px] bg-amber-50 text-amber-700 border border-amber-200 rounded-full px-2 py-0.5 font-medium">Modifiable</span>
              </p>
              <button
                @click="addDirigeant"
                class="inline-flex items-center gap-1.5 h-7 px-3 text-xs font-medium rounded-md bg-tacir-blue/10 text-tacir-blue hover:bg-tacir-blue/20 transition-colors"
              >
                <Plus class="w-3 h-3" /> Ajouter
              </button>
            </div>

            <!-- Empty state -->
            <div v-if="modalDirigeants.length === 0" class="text-center py-8 text-sm text-muted-foreground italic border border-dashed border-border rounded-xl">
              Aucun dirigeant — cliquez sur "Ajouter" pour en créer un
            </div>

            <!-- Dirigeant cards -->
            <div class="space-y-3">
              <div
                v-for="(d, i) in modalDirigeants"
                :key="d._uid"
                class="group rounded-xl border border-border bg-card p-4 hover:border-tacir-blue/30 transition-colors"
              >
                <!-- Avatar + delete button -->
                <div class="flex items-center justify-between mb-3">
                  <div class="flex items-center gap-2">
                    <div :class="['w-9 h-9 rounded-full flex items-center justify-center text-[11px] font-bold flex-shrink-0', AVATAR_COLORS[i % AVATAR_COLORS.length]]">
                      {{ getInitials(d.prenoms, d.nom) }}
                    </div>
                    <span class="text-sm font-medium text-foreground">
                      {{ [d.prenoms, d.nom].filter(Boolean).join(' ') || 'Nouveau dirigeant' }}
                    </span>
                  </div>
                  <button
                    @click="removeDirigeant(i)"
                    class="opacity-0 group-hover:opacity-100 transition-opacity h-7 w-7 flex items-center justify-center rounded-md hover:bg-destructive/10 hover:text-destructive text-muted-foreground"
                    title="Supprimer"
                  >
                    <Trash2 class="w-3.5 h-3.5" />
                  </button>
                </div>

                <!-- Editable fields in 2-col grid -->
                <div class="grid grid-cols-2 gap-3">
                  <div class="space-y-1">
                    <label class="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">Prénom(s)</label>
                    <input
                      v-model="d.prenoms"
                      type="text"
                      placeholder="Jean-Pierre"
                      class="w-full h-8 text-sm rounded-md border border-input bg-background px-2.5 focus:outline-none focus:ring-1 focus:ring-tacir-blue"
                    />
                  </div>
                  <div class="space-y-1">
                    <label class="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">Nom</label>
                    <input
                      v-model="d.nom"
                      type="text"
                      placeholder="DUPONT"
                      class="w-full h-8 text-sm rounded-md border border-input bg-background px-2.5 focus:outline-none focus:ring-1 focus:ring-tacir-blue"
                    />
                  </div>
                  <div class="space-y-1">
                    <label class="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">Qualité / Rôle</label>
                    <input
                      v-model="d.qualite"
                      type="text"
                      placeholder="Président"
                      class="w-full h-8 text-sm rounded-md border border-input bg-background px-2.5 focus:outline-none focus:ring-1 focus:ring-tacir-blue"
                    />
                  </div>
                  <div class="space-y-1">
                    <label class="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">Nationalité</label>
                    <input
                      v-model="d.nationalite"
                      type="text"
                      placeholder="Française"
                      class="w-full h-8 text-sm rounded-md border border-input bg-background px-2.5 focus:outline-none focus:ring-1 focus:ring-tacir-blue"
                    />
                  </div>
                  <div class="col-span-2 space-y-1">
                    <label class="text-[10px] font-medium text-muted-foreground uppercase tracking-wide flex items-center gap-1">
                      <Linkedin class="w-3 h-3" /> LinkedIn URL
                    </label>
                    <input
                      v-model="d.linkedin_url"
                      type="url"
                      placeholder="https://www.linkedin.com/in/..."
                      class="w-full h-8 text-sm rounded-md border border-input bg-background px-2.5 focus:outline-none focus:ring-1 focus:ring-tacir-blue"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Loading overlay -->
          <Transition name="fade-overlay">
            <div v-if="isLoadingData" class="absolute inset-0 z-20 bg-background/60 flex items-center justify-center backdrop-blur-[2px] rounded-b-xl">
              <div class="flex flex-col items-center gap-2">
                <Loader2 class="h-7 w-7 animate-spin text-tacir-blue" />
                <span class="text-xs text-muted-foreground font-medium">Chargement...</span>
              </div>
            </div>
          </Transition>
        </div>

        <!-- Footer -->
        <div class="flex-shrink-0 border-t border-border px-6 py-4 flex justify-end gap-3 bg-background">
          <button
            @click="emit('close')"
            :disabled="isSaving"
            class="h-9 px-4 text-sm rounded-md border border-input hover:bg-accent transition-colors disabled:opacity-50"
          >
            Annuler
          </button>
          <button
            @click="handleSave"
            :disabled="isSaving || isLoadingData"
            class="h-9 px-4 text-sm font-medium rounded-md bg-tacir-blue text-white hover:opacity-90 transition-opacity flex items-center gap-2 disabled:opacity-50"
          >
            <Loader2 v-if="isSaving" class="h-4 w-4 animate-spin" />
            Enregistrer
          </button>
        </div>
      </template>
    </DialogContent>
  </Dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import axios from 'axios'
import { Users, Loader2, Plus, Trash2, Linkedin } from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
} from '@/components/ui/dialog'

const props = defineProps({
  lead: { type: Object, default: null },
  open: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'save'])

const tabs = [
  { key: 'general',    label: 'Informations' },
  { key: 'contact',    label: 'Contact'      },
  { key: 'dirigeants', label: 'Dirigeants'   },
]
const activeTab = ref('general')

const inputClass = {
  class: 'w-full h-9 text-sm rounded-md border border-input bg-background px-3 focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50 disabled:cursor-not-allowed',
}

const AVATAR_COLORS = [
  'bg-purple-100 text-purple-700',
  'bg-emerald-100 text-emerald-700',
  'bg-orange-100 text-orange-700',
  'bg-blue-100 text-blue-700',
  'bg-rose-100 text-rose-700',
  'bg-teal-100 text-teal-700',
]

let _uidCounter = 0
function nextUid() { return ++_uidCounter }

function getInitials(prenoms, nom) {
  const p = prenoms?.[0]?.toUpperCase() || ''
  const n = nom?.[0]?.toUpperCase() || ''
  return (p + n) || '?'
}

const emptyForm = () => ({
  nom: '', siren: '', siret: '', identifiant: '',
  tailleEntreprise: '', secteurActivite: '',
  formeJuridique: '', ville: '', codePostal: '', pays: '',
  caFormatted: '', telephone: '', email: '',
  status: 'Nouveau',
})

const form = ref(emptyForm())
const modalDirigeants = ref([])
const isLoadingData = ref(false)
const isSaving = ref(false)

// Add / remove dirigeant helpers
function addDirigeant() {
  modalDirigeants.value.push({
    _uid: nextUid(),
    nom: '', prenoms: '', qualite: '',
    nationalite: '', linkedin_url: '',
  })
}

function removeDirigeant(index) {
  modalDirigeants.value.splice(index, 1)
}

// Watch open → fetch from /modal endpoint
watch(() => props.open, async (isOpen) => {
  if (!isOpen || !props.lead) {
    form.value = emptyForm()
    modalDirigeants.value = []
    return
  }

  const lead = props.lead
  const clean = (v) => (v === '—' ? '' : v ?? '')

  // Immediate population from local data (instant UX)
  form.value = {
    nom:             clean(lead.nom),
    siren:           clean(lead.siren),
    siret:           clean(lead.siret),
    identifiant:     clean(lead.identifiant),
    tailleEntreprise: clean(lead.tailleEntreprise),
    secteurActivite: clean(lead.secteurActivite),
    formeJuridique:  clean(lead.formeJuridique),
    ville:           clean(lead.ville),
    codePostal:      clean(lead.codePostal),
    pays:            clean(lead.pays),
    caFormatted:     clean(lead.caFormatted),
    telephone:       clean(lead.telephone),
    email:           clean(lead.email),
    status:          lead.status ?? 'Nouveau',
  }
  modalDirigeants.value = (lead.dirigeants || []).map((d) => ({
    _uid: nextUid(),
    nom:          d.nom || '',
    prenoms:      d.prenoms || '',
    qualite:      d.qualite || '',
    nationalite:  d.nationalite || '',
    linkedin_url: d.linkedinUrl || d.linkedin_url || '',
  }))
  activeTab.value = 'general'

  // Fetch authoritative data from API
  isLoadingData.value = true
  try {
    const baseUrl = import.meta.env.VITE_FASTAPI_URL || 'http://localhost:8001'
    const leadId = lead.identifiant || lead.siren || lead.id
    const res = await axios.get(`${baseUrl}/entreprises/${leadId}/modal`)
    const data = res.data

    const info    = data.Informations || {}
    const contact = data.Contact || {}

    form.value = {
      nom:             clean(info.nom_entreprise),
      siren:           clean(info.siren),
      siret:           clean(info.siret),
      identifiant:     clean(info.identifiant),
      tailleEntreprise: clean(info.taille_entreprise),
      secteurActivite: clean(info.secteur_activite),
      formeJuridique:  clean(info.forme_juridique),
      caFormatted:     clean(info.ca_affiche),
      ville:           clean(contact.ville),
      codePostal:      clean(contact.code_postal),
      pays:            clean(contact.pays),
      telephone:       clean(contact.telephone),
      email:           clean(contact.email),
      status:          clean(info.statut) || 'Nouveau',
    }

    if (Array.isArray(data.Dirigeants)) {
      modalDirigeants.value = data.Dirigeants.map((d) => ({
        _uid:         nextUid(),
        nom:          d.nom || '',
        prenoms:      d.prenoms || '',
        qualite:      d.qualite || d.role || '',
        nationalite:  d.nationalite || '',
        linkedin_url: d.linkedin_url || '',
      }))
    }
  } catch (err) {
    console.error('[Modal] Fetch error:', err)
  } finally {
    isLoadingData.value = false
  }
}, { immediate: true })

async function handleSave() {
  if (!props.lead) return
  const leadId = props.lead.identifiant || props.lead.siren || props.lead.id

  isSaving.value = true
  try {
    const baseUrl = import.meta.env.VITE_FASTAPI_URL || 'http://localhost:8001'

    // Build clean dirigeants array (strip internal _uid)
    const dirigeants = modalDirigeants.value.map(({ _uid, ...d }) => d)

    const payload = {
      nom_entreprise:    form.value.nom,
      siren:             form.value.siren,
      siret:             form.value.siret,
      identifiant:       form.value.identifiant,
      taille_entreprise: form.value.tailleEntreprise,
      secteur_activite:  form.value.secteurActivite,
      forme_juridique:   form.value.formeJuridique,
      ca_affiche:        form.value.caFormatted,
      statut:            form.value.status,
      ville:             form.value.ville,
      code_postal:       form.value.codePostal,
      pays:              form.value.pays,
      telephone:         form.value.telephone,
      email:             form.value.email,
      dirigeants,
    }

    await axios.patch(`${baseUrl}/entreprises/${leadId}`, payload)

    const dash = (v) => v?.trim() || '—'
    emit('save', props.lead.id, {
      nom:             dash(form.value.nom),
      siren:           dash(form.value.siren),
      siret:           dash(form.value.siret),
      identifiant:     dash(form.value.identifiant),
      tailleEntreprise: dash(form.value.tailleEntreprise),
      secteurActivite: dash(form.value.secteurActivite),
      formeJuridique:  dash(form.value.formeJuridique),
      caFormatted:     dash(form.value.caFormatted),
      ville:           dash(form.value.ville),
      codePostal:      dash(form.value.codePostal),
      pays:            dash(form.value.pays),
      telephone:       dash(form.value.telephone),
      email:           dash(form.value.email),
      status:          form.value.status,
    })

    toast.success('Lead mis à jour avec succès', {
      description: `${form.value.nom || 'Entreprise'} — ${form.value.ville || ''}`,
    })
    emit('close')
  } catch (err) {
    console.error('[Modal] Save error:', err)
    toast.error('Erreur lors de la sauvegarde', {
      description: err?.response?.data?.detail || 'Veuillez réessayer.',
    })
  } finally {
    isSaving.value = false
  }
}
</script>

<style scoped>
.fade-overlay-enter-active,
.fade-overlay-leave-active { transition: opacity 0.15s ease; }
.fade-overlay-enter-from,
.fade-overlay-leave-to    { opacity: 0; }
</style>
