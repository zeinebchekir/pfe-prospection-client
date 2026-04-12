<template>
  <!-- Loading state -->
  <div v-if="loading" class="space-y-2 p-4">
    <div v-for="i in 8" :key="i" class="h-10 w-full rounded-lg bg-muted animate-pulse" />
  </div>

  <!-- Empty state -->
  <div v-else-if="leads.length === 0" class="flex flex-col items-center justify-center py-16 text-center">
    <div class="w-16 h-16 rounded-2xl bg-muted flex items-center justify-center mb-4">
      <Eye class="w-7 h-7 text-muted-foreground" />
    </div>
    <p class="text-sm font-medium text-foreground mb-1">Aucun lead trouvé</p>
    <p class="text-xs text-muted-foreground">Ajustez vos filtres ou ajoutez un nouveau lead</p>
  </div>

  <!-- Table -->
  <div v-else class="overflow-x-auto">
    <table class="w-full text-sm">
      <thead>
        <tr class="border-b border-border">
          <SortableHead field="nom"            label="Entreprise"  :sort-field="sortField" :sort-dir="sortDir" @sort="emit('sort', $event)" />
          <SortableHead field="segment"        label="Segment"     :sort-field="sortField" :sort-dir="sortDir" @sort="emit('sort', $event)" />
          <th class="text-[11px] font-medium text-muted-foreground px-4 py-3 text-left whitespace-nowrap">Secteur</th>
          <SortableHead field="ville"          label="Ville"       :sort-field="sortField" :sort-dir="sortDir" @sort="emit('sort', $event)" />
          <th class="text-[11px] font-medium text-muted-foreground px-4 py-3 text-left whitespace-nowrap">SIREN</th>
          <SortableHead field="ca"             label="CA"          :sort-field="sortField" :sort-dir="sortDir" @sort="emit('sort', $event)" />
          <SortableHead field="nbLocaux"       label="Locaux"      :sort-field="sortField" :sort-dir="sortDir" @sort="emit('sort', $event)" />
          <SortableHead field="score"          label="Score"       :sort-field="sortField" :sort-dir="sortDir" @sort="emit('sort', $event)" />
          <SortableHead field="completude"     label="Complétude"  :sort-field="sortField" :sort-dir="sortDir" @sort="emit('sort', $event)" />
          <th class="text-[11px] font-medium text-muted-foreground px-4 py-3 text-left whitespace-nowrap">Statut</th>
          <th class="text-[11px] font-medium text-muted-foreground px-4 py-3 text-right whitespace-nowrap">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="lead in leads"
          :key="lead.id"
          class="border-b border-border last:border-0 cursor-pointer hover:bg-muted/40 transition-colors group"
          @click="emit('preview', lead)"
        >
          <!-- Entreprise -->
          <td class="px-4 py-3 max-w-[180px]">
            <div class="flex flex-col">
              <span class="font-medium text-sm text-foreground truncate">{{ lead.nom }}</span>
              <span v-if="lead.hasBoamp" class="mt-0.5">
                <span class="text-[10px] font-semibold px-1.5 py-0.5 rounded-sm bg-blue-50 text-tacir-blue border border-blue-200">BOAMP</span>
              </span>
            </div>
          </td>
          <!-- Segment -->
          <td class="px-4 py-3">
            <SegmentBadge :segment="lead.segment" />
          </td>
          <!-- Secteur -->
          <td class="px-4 py-3 text-xs text-muted-foreground max-w-[140px] truncate">
            {{ lead.secteurActivite }}
          </td>
          <!-- Ville -->
          <td class="px-4 py-3 text-xs">{{ lead.ville }}</td>
          <!-- SIREN -->
          <td class="px-4 py-3 text-xs font-mono text-muted-foreground">{{ lead.siren }}</td>
          <!-- CA -->
          <td class="px-4 py-3 text-xs font-medium">{{ lead.caFormatted }}</td>
          <!-- Locaux -->
          <td class="px-4 py-3 text-xs">{{ lead.nbLocaux ?? '—' }}</td>
          <!-- Score -->
          <td class="px-4 py-3">
            <ScoreRing :score="lead.score" />
          </td>
          <!-- Complétude -->
          <td class="px-4 py-3">
            <CompletionBar :value="lead.completude" />
          </td>
          <!-- Statut -->
          <td class="px-4 py-3">
            <StatusBadge :status="lead.status" />
          </td>
          <!-- Actions -->
          <td class="px-4 py-3 text-right">
            <div class="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                class="h-7 w-7 flex items-center justify-center rounded hover:bg-muted"
                @click.stop="emit('navigate', lead)"
                title="Voir la fiche"
              >
                <Eye class="w-3.5 h-3.5" />
              </button>
              <button
                class="h-7 w-7 flex items-center justify-center rounded hover:bg-muted"
                @click.stop="emit('edit', lead)"
                title="Modifier"
              >
                <Pencil class="w-3.5 h-3.5" />
              </button>
              <button
                class="h-7 w-7 flex items-center justify-center rounded hover:bg-destructive/10 hover:text-destructive"
                @click.stop="emit('delete', lead)"
                title="Supprimer"
              >
                <Trash2 class="w-3.5 h-3.5" />
              </button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { Eye, Pencil, Trash2, ChevronDown, ChevronUp } from 'lucide-vue-next'
import SegmentBadge from './SegmentBadge.vue'
import StatusBadge  from './StatusBadge.vue'
import ScoreRing    from './ScoreRing.vue'
import CompletionBar from './CompletionBar.vue'
import SortableHead  from './SortableHead.vue'

const props = defineProps({
  leads:     { type: Array, required: true },
  sortField: { type: String, required: true },
  sortDir:   { type: String, required: true },
  loading:   { type: Boolean, default: false },
})

const emit = defineEmits(['sort', 'preview', 'edit', 'delete', 'navigate'])
</script>
