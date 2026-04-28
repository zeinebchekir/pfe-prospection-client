<template>
  <div v-if="loading" class="space-y-2 p-4">
    <div v-for="index in 8" :key="index" class="h-16 w-full rounded-lg bg-muted animate-pulse" />
  </div>

  <div
    v-else-if="leads.length === 0"
    class="flex flex-col items-center justify-center py-16 text-center"
  >
    <div class="w-16 h-16 rounded-2xl bg-muted flex items-center justify-center mb-4">
      <SearchX class="w-7 h-7 text-muted-foreground" />
    </div>
    <p class="text-sm font-medium text-foreground mb-1">Aucune opportunite trouvee</p>
    <p class="text-xs text-muted-foreground">
      Ajuste la recherche pour afficher des resultats issus de `lead_opportunity`
    </p>
  </div>

  <template v-else>
    <div class="md:hidden divide-y divide-border">
      <div
        v-for="lead in leads"
        :key="lead.lead_id"
        class="px-4 py-4 space-y-2.5 hover:bg-muted/40 transition-colors"
      >
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <p class="text-sm font-semibold text-foreground truncate">{{ lead.company_name }}</p>
            <p class="text-xs text-muted-foreground truncate">{{ lead.industry || 'Secteur non renseigne' }}</p>
          </div>
          <div class="flex items-center gap-2">
            <Badge :class="temperatureClasses(lead.lead_temperature)">
              {{ temperatureLabel(lead.lead_temperature) }}
            </Badge>
            <Badge variant="outline" class="border-tacir-blue/20 text-tacir-blue bg-tacir-blue/5">
              {{ formatScore(lead.lead_score_predicted) }}
            </Badge>
          </div>
        </div>

        <div class="flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-muted-foreground">
          <span class="flex items-center gap-1">
            <UserRound class="w-3 h-3" />
            {{ lead.contact_name || 'Contact non renseigne' }}
          </span>
          <span class="flex items-center gap-1">
            <BriefcaseBusiness class="w-3 h-3" />
            {{ lead.job_title || 'Poste non renseigne' }}
          </span>
          <span class="flex items-center gap-1">
            <MapPin class="w-3 h-3" />
            {{ locationLabel(lead) }}
          </span>
        </div>

        <div class="grid grid-cols-2 gap-2 text-[11px] text-muted-foreground">
          <span>Total visits : {{ formatInteger(lead.total_visits) }}</span>
          <span>Temps web : {{ formatInteger(lead.time_on_website_sec) }} sec</span>
          <span>Pages moy. : {{ formatDecimal(lead.avg_page_views) }}</span>
          <span>Source : {{ lead.lead_source || '-' }}</span>
        </div>

        <div class="space-y-1 text-[11px] text-muted-foreground">
          <p>Last Activity : {{ lead.last_activity || '-' }}</p>
          <p>Last Notable Activity : {{ lead.last_notable_activity || '-' }}</p>
          <p>Score le {{ formatDateTime(lead.scored_at) }}</p>
        </div>

        <div class="flex flex-wrap items-center justify-between gap-3 text-[11px]">
          <span class="text-muted-foreground">Mis a jour le {{ formatDate(lead.last_modified_date) }}</span>
          <div class="flex flex-wrap items-center gap-2">
            <button
              type="button"
              class="inline-flex items-center gap-1 rounded-md border border-border px-2.5 py-1 text-foreground hover:bg-muted transition-colors"
              @click="emit('edit', lead)"
            >
              <Pencil class="w-3 h-3" />
              Modifier
            </button>
            <button
              type="button"
              class="inline-flex items-center gap-1 rounded-md border border-red-200 px-2.5 py-1 text-red-700 hover:bg-red-50 transition-colors"
              @click="emit('delete', lead)"
            >
              <Trash2 class="w-3 h-3" />
              Supprimer
            </button>
            <a
              v-if="lead.email"
              :href="`mailto:${lead.email}`"
              class="inline-flex items-center gap-1 rounded-md border border-border px-2.5 py-1 text-foreground hover:bg-muted transition-colors"
            >
              <Mail class="w-3 h-3" />
              Email
            </a>
            <a
              v-if="lead.website"
              :href="lead.website"
              target="_blank"
              rel="noreferrer"
              class="inline-flex items-center gap-1 rounded-md border border-border px-2.5 py-1 text-foreground hover:bg-muted transition-colors"
            >
              <Globe class="w-3 h-3" />
              Site
            </a>
          </div>
        </div>
      </div>
    </div>

    <div class="hidden md:block overflow-x-auto">
      <table class="w-full min-w-[1500px] text-sm">
        <thead>
          <tr class="border-b border-border">
            <th class="px-4 py-3 text-left text-[11px] font-medium text-muted-foreground">Entreprise</th>
            <th class="px-4 py-3 text-left text-[11px] font-medium text-muted-foreground">Contact</th>
            <th class="px-4 py-3 text-left text-[11px] font-medium text-muted-foreground">Job Title</th>
            <th class="px-4 py-3 text-left text-[11px] font-medium text-muted-foreground">Industry</th>
            <th class="px-4 py-3 text-left text-[11px] font-medium text-muted-foreground">Country</th>
            <th class="px-4 py-3 text-left text-[11px] font-medium text-muted-foreground">City</th>
            <th class="px-4 py-3 text-left text-[11px] font-medium text-muted-foreground">Lead Source</th>
            <th class="px-4 py-3 text-left text-[11px] font-medium text-muted-foreground">Total Visits</th>
            <th class="px-4 py-3 text-left text-[11px] font-medium text-muted-foreground">Time on Website (sec)</th>
            <th class="px-4 py-3 text-left text-[11px] font-medium text-muted-foreground">Avg Page Views</th>
            <th class="px-4 py-3 text-left text-[11px] font-medium text-muted-foreground">Last Activity</th>
            <th class="px-4 py-3 text-left text-[11px] font-medium text-muted-foreground">Last Notable Activity</th>
            <th class="px-4 py-3 text-left text-[11px] font-medium text-muted-foreground">Lead Score</th>
            <th class="px-4 py-3 text-left text-[11px] font-medium text-muted-foreground">Lead Type</th>
            <th class="px-4 py-3 text-left text-[11px] font-medium text-muted-foreground">Last Modified Date</th>
            <th class="px-4 py-3 text-left text-[11px] font-medium text-muted-foreground">Scored At</th>
            <th class="px-4 py-3 text-right text-[11px] font-medium text-muted-foreground">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="lead in leads"
            :key="lead.lead_id"
            class="border-b border-border last:border-0 hover:bg-muted/30 transition-colors"
          >
            <td class="px-4 py-3 max-w-[220px]">
              <div class="space-y-1">
                <p class="font-medium text-foreground truncate">{{ lead.company_name }}</p>
                <p class="text-xs text-muted-foreground truncate">{{ lead.email || 'Email non renseigne' }}</p>
              </div>
            </td>
            <td class="px-4 py-3 max-w-[180px]">
              <div class="space-y-1">
                <p class="text-sm text-foreground truncate">{{ lead.contact_name || '-' }}</p>
                <p class="text-xs text-muted-foreground truncate">{{ lead.phone_number || 'Telephone non renseigne' }}</p>
              </div>
            </td>
            <td class="px-4 py-3 text-sm text-foreground">{{ lead.job_title || '-' }}</td>
            <td class="px-4 py-3 text-sm text-foreground">{{ lead.industry || '-' }}</td>
            <td class="px-4 py-3 text-sm text-foreground">{{ lead.country || '-' }}</td>
            <td class="px-4 py-3 text-sm text-foreground">{{ lead.city || '-' }}</td>
            <td class="px-4 py-3 text-sm text-foreground">{{ lead.lead_source || '-' }}</td>
            <td class="px-4 py-3 text-sm text-foreground">{{ formatInteger(lead.total_visits) }}</td>
            <td class="px-4 py-3 text-sm text-foreground">{{ formatInteger(lead.time_on_website_sec) }}</td>
            <td class="px-4 py-3 text-sm text-foreground">{{ formatDecimal(lead.avg_page_views) }}</td>
            <td class="px-4 py-3 max-w-[180px] text-sm text-foreground">{{ lead.last_activity || '-' }}</td>
            <td class="px-4 py-3 max-w-[180px] text-sm text-foreground">{{ lead.last_notable_activity || '-' }}</td>
            <td class="px-4 py-3">
              <Badge variant="outline" class="border-tacir-blue/20 text-tacir-blue bg-tacir-blue/5">
                {{ formatScore(lead.lead_score_predicted) }}
              </Badge>
            </td>
            <td class="px-4 py-3">
              <Badge :class="temperatureClasses(lead.lead_temperature)">
                {{ temperatureLabel(lead.lead_temperature) }}
              </Badge>
            </td>
            <td class="px-4 py-3 text-xs text-muted-foreground whitespace-nowrap">{{ formatDate(lead.last_modified_date) }}</td>
            <td class="px-4 py-3 text-xs text-muted-foreground whitespace-nowrap">{{ formatDateTime(lead.scored_at) }}</td>
            <td class="px-4 py-3">
              <div class="flex items-center justify-end gap-2">
                <button
                  type="button"
                  class="inline-flex h-8 w-8 items-center justify-center rounded-md border border-border hover:bg-muted transition-colors"
                  title="Modifier ce lead"
                  @click="emit('edit', lead)"
                >
                  <Pencil class="w-3.5 h-3.5 text-muted-foreground" />
                </button>
                <button
                  type="button"
                  class="inline-flex h-8 w-8 items-center justify-center rounded-md border border-red-200 hover:bg-red-50 transition-colors"
                  title="Supprimer ce lead"
                  @click="emit('delete', lead)"
                >
                  <Trash2 class="w-3.5 h-3.5 text-red-600" />
                </button>
                <a
                  v-if="lead.email"
                  :href="`mailto:${lead.email}`"
                  class="inline-flex h-8 w-8 items-center justify-center rounded-md border border-border hover:bg-muted transition-colors"
                  title="Envoyer un email"
                >
                  <Mail class="w-3.5 h-3.5 text-muted-foreground" />
                </a>
                <a
                  v-if="lead.website"
                  :href="lead.website"
                  target="_blank"
                  rel="noreferrer"
                  class="inline-flex h-8 w-8 items-center justify-center rounded-md border border-border hover:bg-muted transition-colors"
                  title="Ouvrir le site web"
                >
                  <Globe class="w-3.5 h-3.5 text-muted-foreground" />
                </a>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </template>
</template>

<script setup>
import {
  BriefcaseBusiness,
  Globe,
  Mail,
  MapPin,
  Pencil,
  SearchX,
  Trash2,
  UserRound,
} from 'lucide-vue-next'

import { Badge } from '@/components/ui/badge'

defineProps({
  leads: { type: Array, required: true },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['edit', 'delete'])

function formatDate(value) {
  if (!value) return '-'
  return new Intl.DateTimeFormat('fr-FR', {
    dateStyle: 'medium',
  }).format(new Date(value))
}

function formatDateTime(value) {
  if (!value) return '-'
  return new Intl.DateTimeFormat('fr-FR', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function formatInteger(value) {
  if (value === null || value === undefined) return '-'
  return new Intl.NumberFormat('fr-FR').format(Number(value))
}

function formatDecimal(value) {
  if (value === null || value === undefined) return '-'
  return new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 1 }).format(Number(value))
}

function formatScore(value) {
  if (value === null || value === undefined) return '-'
  return `${Number(value)}/100`
}

function temperatureLabel(value) {
  if (value === 'HOT') return 'Chaud'
  if (value === 'WARM') return 'Tiede'
  if (value === 'COLD') return 'Froid'
  return 'Non score'
}

function temperatureClasses(value) {
  if (value === 'HOT') {
    return 'border-emerald-200 bg-emerald-50 text-emerald-700'
  }
  if (value === 'WARM') {
    return 'border-amber-200 bg-amber-50 text-amber-700'
  }
  if (value === 'COLD') {
    return 'border-rose-200 bg-rose-50 text-rose-700'
  }
  return 'border-border bg-muted text-muted-foreground'
}

function locationLabel(lead) {
  return [lead.country, lead.city].filter(Boolean).join(', ') || '-'
}
</script>
