<template>
  <Dialog :open="open" @update:open="handleOpenChange">
    <DialogContent class="w-[calc(100vw-2rem)] max-w-4xl max-h-[92vh] overflow-hidden p-0">
      <div class="flex flex-col max-h-[92vh]">
        <DialogHeader class="border-b border-border px-6 py-5">
          <DialogTitle class="text-base font-semibold text-tacir-darkblue">
            {{ dialogTitle }}
          </DialogTitle>
          <p class="text-xs text-muted-foreground">
            {{ dialogDescription }}
          </p>
        </DialogHeader>

        <form class="flex-1 overflow-y-auto px-6 py-5 space-y-5" @submit.prevent="submitForm">
          <div class="grid gap-4 md:grid-cols-2">
            <div class="space-y-1.5">
              <label class="text-xs font-semibold text-foreground">Company Name</label>
              <input v-model="form.company_name" :class="fieldClass" placeholder="Ex : Acme Corp" />
              <p v-if="submitted && !form.company_name.trim()" class="text-[11px] text-red-600">
                Le nom de l'entreprise est obligatoire.
              </p>
            </div>

            <div class="space-y-1.5">
              <label class="text-xs font-semibold text-foreground">Contact Name</label>
              <input v-model="form.contact_name" :class="fieldClass" placeholder="Ex : Sarah Ben Ali" />
            </div>

            <div class="space-y-1.5">
              <label class="text-xs font-semibold text-foreground">Job Title</label>
              <input
                v-model="form.job_title"
                :class="fieldClass"
                :list="jobTitleListId"
                placeholder="Choisir ou saisir un job title"
              />
              <p class="text-[11px] text-muted-foreground">
                {{ optionsLoading ? 'Chargement des suggestions...' : `${jobTitleOptions.length} choix depuis la base` }}
              </p>
            </div>

            <div class="space-y-1.5">
              <label class="text-xs font-semibold text-foreground">Email</label>
              <input v-model="form.email" :class="fieldClass" type="email" placeholder="contact@entreprise.com" />
            </div>

            <div class="space-y-1.5">
              <label class="text-xs font-semibold text-foreground">Phone Number</label>
              <input v-model="form.phone_number" :class="fieldClass" placeholder="+216 20 000 000" />
            </div>

            <div class="space-y-1.5">
              <label class="text-xs font-semibold text-foreground">Website</label>
              <input v-model="form.website" :class="fieldClass" placeholder="https://entreprise.com" />
            </div>

            <div class="space-y-1.5">
              <label class="text-xs font-semibold text-foreground">Last Modified Date</label>
              <input v-model="form.last_modified_date" :class="fieldClass" type="datetime-local" />
            </div>

            <div class="space-y-1.5">
              <label class="text-xs font-semibold text-foreground">Industry</label>
              <input v-model="form.industry" :class="fieldClass" placeholder="Ex : Software" />
            </div>

            <div class="space-y-1.5">
              <label class="text-xs font-semibold text-foreground">Company Size</label>
              <input v-model="form.company_size" :class="fieldClass" placeholder="Ex : 50-99" />
            </div>

            <div class="space-y-1.5">
              <label class="text-xs font-semibold text-foreground">Annual Revenue</label>
              <input v-model="form.annual_revenue" :class="fieldClass" placeholder="Ex : 1M-5M" />
            </div>

            <div class="space-y-1.5">
              <label class="text-xs font-semibold text-foreground">Country</label>
              <input v-model="form.country" :class="fieldClass" placeholder="Ex : Tunisia" />
            </div>

            <div class="space-y-1.5">
              <label class="text-xs font-semibold text-foreground">City</label>
              <input v-model="form.city" :class="fieldClass" placeholder="Ex : Tunis" />
            </div>

            <div class="space-y-1.5">
              <label class="text-xs font-semibold text-foreground">Lead Source</label>
              <input
                v-model="form.lead_source"
                :class="fieldClass"
                :list="leadSourceListId"
                placeholder="Choisir ou saisir une source"
              />
              <p class="text-[11px] text-muted-foreground">
                {{ optionsLoading ? 'Chargement des suggestions...' : `${leadSourceOptions.length} choix depuis la base` }}
              </p>
            </div>

            <div class="space-y-1.5">
              <label class="text-xs font-semibold text-foreground">Total Visits</label>
              <input v-model="form.total_visits" :class="fieldClass" type="number" min="0" placeholder="12" />
            </div>

            <div class="space-y-1.5">
              <label class="text-xs font-semibold text-foreground">Time on Website (sec)</label>
              <input v-model="form.time_on_website_sec" :class="fieldClass" type="number" min="0" placeholder="360" />
            </div>

            <div class="space-y-1.5">
              <label class="text-xs font-semibold text-foreground">Avg Page Views</label>
              <input v-model="form.avg_page_views" :class="fieldClass" type="number" min="0" step="0.1" placeholder="4.5" />
            </div>

            <div class="space-y-1.5">
              <label class="text-xs font-semibold text-foreground">Last Activity</label>
              <input
                v-model="form.last_activity"
                :class="fieldClass"
                :list="lastActivityListId"
                placeholder="Choisir ou saisir une activite"
              />
              <p class="text-[11px] text-muted-foreground">
                {{ optionsLoading ? 'Chargement des suggestions...' : `${lastActivityOptions.length} choix depuis la base` }}
              </p>
            </div>

            <div class="space-y-1.5">
              <label class="text-xs font-semibold text-foreground">Last Notable Activity</label>
              <input
                v-model="form.last_notable_activity"
                :class="fieldClass"
                :list="lastNotableActivityListId"
                placeholder="Choisir ou saisir une activite notable"
              />
              <p class="text-[11px] text-muted-foreground">
                {{ optionsLoading ? 'Chargement des suggestions...' : `${lastNotableActivityOptions.length} choix depuis la base` }}
              </p>
            </div>
          </div>

          <div class="space-y-1.5">
            <label class="text-xs font-semibold text-foreground">Interaction History</label>
            <textarea
              v-model="form.interaction_history"
              rows="5"
              :class="[fieldClass, 'min-h-[120px] h-auto resize-y py-2.5']"
              placeholder="Historique des echanges, reunions, objections, interet, etc."
            />
          </div>
        </form>

        <div class="border-t border-border px-6 py-4 flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-end bg-muted/20">
          <button
            type="button"
            class="inline-flex h-9 items-center justify-center rounded-md border border-input px-4 text-sm font-medium hover:bg-accent transition-colors"
            :disabled="saving"
            @click="handleOpenChange(false)"
          >
            Annuler
          </button>
          <button
            type="button"
            class="inline-flex h-9 items-center justify-center rounded-md bg-tacir-blue px-4 text-sm font-semibold text-white hover:opacity-90 transition-opacity disabled:opacity-60"
            :disabled="saving"
            @click="submitForm"
          >
            {{ saving ? savingLabel : submitLabel }}
          </button>
        </div>
      </div>
    </DialogContent>
  </Dialog>

  <datalist :id="jobTitleListId">
    <option v-for="option in jobTitleOptions" :key="`job-${listIdPrefix}-${option}`" :value="option" />
  </datalist>

  <datalist :id="leadSourceListId">
    <option v-for="option in leadSourceOptions" :key="`source-${listIdPrefix}-${option}`" :value="option" />
  </datalist>

  <datalist :id="lastActivityListId">
    <option v-for="option in lastActivityOptions" :key="`activity-${listIdPrefix}-${option}`" :value="option" />
  </datalist>

  <datalist :id="lastNotableActivityListId">
    <option
      v-for="option in lastNotableActivityOptions"
      :key="`notable-${listIdPrefix}-${option}`"
      :value="option"
    />
  </datalist>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

const props = defineProps({
  open: { type: Boolean, default: false },
  saving: { type: Boolean, default: false },
  mode: { type: String, default: 'create' },
  lead: { type: Object, default: null },
  listIdPrefix: { type: String, default: 'opportunity-form' },
  optionsLoading: { type: Boolean, default: false },
  jobTitleOptions: { type: Array, default: () => [] },
  leadSourceOptions: { type: Array, default: () => [] },
  lastActivityOptions: { type: Array, default: () => [] },
  lastNotableActivityOptions: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:open', 'submit'])

const submitted = ref(false)
const fieldClass =
  'h-9 w-full rounded-md border border-input bg-background px-3 text-sm outline-none transition-colors focus:border-tacir-blue focus:ring-2 focus:ring-tacir-blue/20'

const dialogTitle = computed(() =>
  props.mode === 'edit' ? 'Modifier une opportunite' : 'Ajouter une opportunite',
)
const dialogDescription = computed(() =>
  props.mode === 'edit'
    ? "Le score est recalcule cote serveur juste apres la modification du lead."
    : "Le score est calcule cote serveur juste apres l'enregistrement du lead.",
)
const submitLabel = computed(() =>
  props.mode === 'edit' ? 'Enregistrer et recalculer le score' : 'Creer et scorer',
)
const savingLabel = computed(() =>
  props.mode === 'edit' ? 'Mise a jour...' : 'Enregistrement...',
)

const jobTitleListId = computed(() => `${props.listIdPrefix}-job-title-options`)
const leadSourceListId = computed(() => `${props.listIdPrefix}-lead-source-options`)
const lastActivityListId = computed(() => `${props.listIdPrefix}-last-activity-options`)
const lastNotableActivityListId = computed(() => `${props.listIdPrefix}-last-notable-activity-options`)

function formatDateTimeLocal(value) {
  const source = value ? new Date(value) : new Date()
  if (Number.isNaN(source.getTime())) {
    return ''
  }

  const pad = (part) => String(part).padStart(2, '0')
  return [
    source.getFullYear(),
    pad(source.getMonth() + 1),
    pad(source.getDate()),
  ].join('-') + `T${pad(source.getHours())}:${pad(source.getMinutes())}`
}

function emptyValue(value) {
  return value ?? ''
}

function createInitialForm() {
  const sourceLead = props.mode === 'edit' ? props.lead : null

  return {
    company_name: emptyValue(sourceLead?.company_name),
    contact_name: emptyValue(sourceLead?.contact_name),
    job_title: emptyValue(sourceLead?.job_title),
    email: emptyValue(sourceLead?.email),
    phone_number: emptyValue(sourceLead?.phone_number),
    website: emptyValue(sourceLead?.website),
    last_modified_date: formatDateTimeLocal(sourceLead?.last_modified_date),
    industry: emptyValue(sourceLead?.industry),
    company_size: emptyValue(sourceLead?.company_size),
    annual_revenue: emptyValue(sourceLead?.annual_revenue),
    country: emptyValue(sourceLead?.country),
    city: emptyValue(sourceLead?.city),
    lead_source: emptyValue(sourceLead?.lead_source),
    total_visits: sourceLead?.total_visits ?? '',
    time_on_website_sec: sourceLead?.time_on_website_sec ?? '',
    avg_page_views: sourceLead?.avg_page_views ?? '',
    last_activity: emptyValue(sourceLead?.last_activity),
    last_notable_activity: emptyValue(sourceLead?.last_notable_activity),
    interaction_history: emptyValue(sourceLead?.interaction_history),
  }
}

const form = reactive(createInitialForm())

function syncForm() {
  Object.assign(form, createInitialForm())
  submitted.value = false
}

function handleOpenChange(nextOpen) {
  if (!nextOpen) {
    syncForm()
  }
  emit('update:open', nextOpen)
}

function nullableString(value) {
  const cleaned = `${value ?? ''}`.trim()
  return cleaned || null
}

function nullableNumber(value) {
  if (value === '' || value === null || value === undefined) return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

function submitForm() {
  submitted.value = true

  if (!form.company_name.trim()) {
    return
  }

  emit('submit', {
    company_name: form.company_name.trim(),
    contact_name: nullableString(form.contact_name),
    job_title: nullableString(form.job_title),
    email: nullableString(form.email),
    phone_number: nullableString(form.phone_number),
    website: nullableString(form.website),
    last_modified_date: form.last_modified_date ? new Date(form.last_modified_date).toISOString() : null,
    industry: nullableString(form.industry),
    company_size: nullableString(form.company_size),
    annual_revenue: nullableString(form.annual_revenue),
    country: nullableString(form.country),
    city: nullableString(form.city),
    lead_source: nullableString(form.lead_source),
    total_visits: nullableNumber(form.total_visits),
    time_on_website_sec: nullableNumber(form.time_on_website_sec),
    avg_page_views: nullableNumber(form.avg_page_views),
    last_activity: nullableString(form.last_activity),
    last_notable_activity: nullableString(form.last_notable_activity),
    interaction_history: nullableString(form.interaction_history),
  })
}

watch(
  [() => props.open, () => props.lead, () => props.mode],
  () => {
    syncForm()
  },
  { immediate: true, deep: true },
)
</script>
