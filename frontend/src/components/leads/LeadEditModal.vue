<template>
  <Dialog :open="open" @update:open="emit('close')">
    <DialogContent class="max-w-2xl max-h-[85vh] p-0 flex flex-col">
      <template v-if="lead">
        <!-- Header -->
        <DialogHeader class="p-6 pb-0 flex-shrink-0">
          <DialogTitle class="text-lg font-semibold">Modifier le lead — {{ lead.nom }}</DialogTitle>
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
            </button>
          </div>
        </div>

        <!-- Tab content -->
        <div class="flex-1 overflow-y-auto px-6 py-4">

          <!-- Général -->
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

            <!-- Notes -->
            <div class="space-y-1.5">
              <label class="text-[11px] font-medium text-muted-foreground">Notes internes</label>
              <textarea
                v-model="form.notes"
                placeholder="Ajouter des notes…"
                rows="3"
                class="w-full text-sm rounded-md border border-input bg-background px-3 py-2 focus:outline-none focus:ring-2 focus:ring-ring resize-none"
              />
            </div>
          </div>

          <!-- Contact -->
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

          <!-- Dirigeants (read-only) -->
          <div v-if="activeTab === 'dirigeants'" class="space-y-3">
            <p class="text-xs text-muted-foreground flex items-center gap-1">
              <Users class="w-3.5 h-3.5" />
              {{ modalDirigeants.length }} dirigeant{{ modalDirigeants.length > 1 ? 's' : '' }} (lecture seule)
            </p>
            <div
              v-for="d in modalDirigeants"
              :key="d.id"
              class="flex items-center gap-3 p-3 rounded-lg bg-muted/40"
            >
              <div class="w-8 h-8 rounded-full bg-purple-50 text-purple-700 flex items-center justify-center text-[11px] font-semibold">
                {{ d.initials }}
              </div>
              <div>
                <p class="text-sm font-medium">{{ d.fullName }}</p>
                <p class="text-[11px] text-muted-foreground">{{ d.qualite }}</p>
              </div>
            </div>
            <p v-if="modalDirigeants.length === 0" class="text-sm text-muted-foreground italic">
              Aucun dirigeant renseigné
            </p>
          </div>
        </div>

        <!-- Progress Overlay -->
        <div v-if="isLoadingData" class="absolute inset-0 z-20 bg-background/50 flex items-center justify-center backdrop-blur-[1px] pointer-events-none">
          <Loader2 class="h-6 w-6 animate-spin text-tacir-blue" />
        </div>

        <div class="flex-shrink-0 border-t border-border px-6 py-4 flex justify-end gap-3 z-30 bg-background">
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
import { Users, Loader2 } from 'lucide-vue-next'
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

const emptyForm = () => ({
  nom: '', siren: '', siret: '', identifiant: '',
  segment: '', tailleEntreprise: '', secteurActivite: '',
  formeJuridique: '', ville: '', codePostal: '', pays: '',
  caFormatted: '', telephone: '', email: '',
  status: 'Nouveau', notes: '',
})

const form = ref(emptyForm())
const modalDirigeants = ref([])
const isLoadingData = ref(false)
const isSaving = ref(false)

// Populate form when lead changes
watch(() => props.open, async (isOpen) => {
  if (!isOpen || !props.lead) { 
    form.value = emptyForm(); 
    modalDirigeants.value = [];
    return;
  }
  
  const lead = props.lead
  const clean = (v) => (v === '—' ? '' : v ?? '')
  
  // Set initial data before network fetch finishes
  form.value = {
    nom:             clean(lead.nom),
    siren:           clean(lead.siren),
    siret:           clean(lead.siret),
    identifiant:     clean(lead.identifiant),
    segment:         lead.segment ?? '',
    tailleEntreprise:clean(lead.tailleEntreprise),
    secteurActivite: clean(lead.secteurActivite),
    formeJuridique:  clean(lead.formeJuridique),
    ville:           clean(lead.ville),
    codePostal:      clean(lead.codePostal),
    pays:            clean(lead.pays),
    caFormatted:     clean(lead.caFormatted),
    telephone:       clean(lead.telephone),
    email:           clean(lead.email),
    status:          lead.status ?? 'Nouveau',
    notes:           '',
  }
  modalDirigeants.value = lead.dirigeants || []
  activeTab.value = 'general'

  // Fetch precise data from endpoints 
  isLoadingData.value = true
  try {
    const baseUrl = import.meta.env.VITE_FASTAPI_URL || 'http://localhost:8001'
    const leadId = lead.identifiant || lead.siren || lead.id
    
    const res = await axios.get(`${baseUrl}/entreprises/${leadId}/modal`)
    const data = res.data

    const info = data.Informations || {}
    const contact = data.Contact || {}

    form.value = {
      nom:             clean(info.nom_entreprise),
      siren:           clean(info.siren),
      siret:           clean(info.siret),
      identifiant:     clean(info.identifiant),
      tailleEntreprise:clean(info.taille_entreprise),
      secteurActivite: clean(info.secteur_activite),
      formeJuridique:  clean(info.forme_juridique),
      caFormatted:     clean(info.ca_affiche),
      ville:           clean(contact.ville),
      codePostal:      clean(contact.code_postal),
      pays:            clean(contact.pays),
      telephone:       clean(contact.telephone),
      email:           clean(contact.email),
      status:          clean(info.statut) || 'Nouveau',
      notes:           '',
    }

    if (data.Dirigeants) {
      modalDirigeants.value = data.Dirigeants.map((d, i) => ({
        id: `modal-dir-${i}`,
        fullName: `${d.prenoms || ''} ${d.nom || ''}`.trim() || 'Inconnu',
        initials: ((d.prenoms?.[0] || '') + (d.nom?.[0] || '')).toUpperCase() || '?',
        qualite: d.qualite || ''
      }))
    }
  } catch (err) {
    console.error('[Modal] Failed to fetch data:', err)
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
    }

    await axios.patch(`${baseUrl}/entreprises/${leadId}`, payload)

    const dash = (v) => v?.trim() || '—'
    emit('save', props.lead.id, {
      nom:        dash(form.value.nom),
      siren:      dash(form.value.siren),
      siret:      dash(form.value.siret),
      identifiant:dash(form.value.identifiant),
      tailleEntreprise: dash(form.value.tailleEntreprise),
      secteurActivite:  dash(form.value.secteurActivite),
      formeJuridique:   dash(form.value.formeJuridique),
      caFormatted: dash(form.value.caFormatted),
      ville:      dash(form.value.ville),
      codePostal: dash(form.value.codePostal),
      pays:       dash(form.value.pays),
      telephone:  dash(form.value.telephone),
      email:      dash(form.value.email),
      status:     form.value.status,
    })
    emit('close')
  } catch (err) {
    console.error('[Modal] Failed to save lead:', err)
    alert("Erreur lors de la sauvegarde du lead.")
  } finally {
    isSaving.value = false
  }
}
</script>

