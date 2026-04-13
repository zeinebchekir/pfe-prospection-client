<template>
  <!-- ── Loading state ─────────────────────────────────────── -->
  <div v-if="loading" class="space-y-2 p-4">
    <div v-for="i in 8" :key="i" class="h-14 w-full rounded-lg bg-muted animate-pulse" />
  </div>

  <!-- ── Empty state ────────────────────────────────────────── -->
  <div v-else-if="leads.length === 0" class="flex flex-col items-center justify-center py-16 text-center">
    <div class="w-16 h-16 rounded-2xl bg-muted flex items-center justify-center mb-4">
      <Eye class="w-7 h-7 text-muted-foreground" />
    </div>
    <p class="text-sm font-medium text-foreground mb-1">Aucun lead trouvé</p>
    <p class="text-xs text-muted-foreground">Ajustez vos filtres ou ajoutez un nouveau lead</p>
  </div>

  <template v-else>

    <!-- ══════════════════════════════════════════════════════ -->
    <!--  MOBILE — card list  (< md)                           -->
    <!-- ══════════════════════════════════════════════════════ -->
    <div class="md:hidden divide-y divide-border">
      <div
        v-for="lead in leads"
        :key="lead.id"
        class="px-4 py-3 flex items-start gap-3 hover:bg-muted/40 active:bg-muted/60 cursor-pointer transition-colors"
        @click="emit('preview', lead)"
      >
        <!-- Avatar initial -->
        <div
          class="w-9 h-9 rounded-xl flex-shrink-0 flex items-center justify-center text-xs font-bold text-white mt-0.5"
          :style="{ backgroundColor: avatarColor(lead.nom) }"
        >
          {{ lead.nom?.[0]?.toUpperCase() ?? '?' }}
        </div>

        <!-- Info -->
        <div class="flex-1 min-w-0">
          <div class="flex items-center justify-between gap-2">
            <span class="text-sm font-semibold text-foreground truncate">{{ lead.nom }}</span>
            <StatusBadge :status="lead.status" class="flex-shrink-0" />
          </div>
          <div class="flex items-center gap-2 mt-0.5 flex-wrap">
            <SegmentBadge :segment="lead.segment" />
            <span class="text-[10px] text-muted-foreground">{{ lead.ville }}</span>
            <span v-if="lead.caFormatted !== '—'" class="text-[10px] font-medium text-foreground">{{ lead.caFormatted }}</span>
            <span v-if="lead.hasBoamp" class="text-[9px] font-semibold px-1.5 py-0.5 rounded-sm bg-blue-50 text-tacir-blue border border-blue-200">BOAMP</span>
          </div>
          <div class="flex items-center gap-3 mt-1.5">
            <CompletionBar :value="lead.completude" class="flex-1 max-w-[100px]" />
            <span class="text-[10px] text-muted-foreground">{{ lead.completude }}%</span>
          </div>
        </div>

        <!-- Quick actions -->
        <div class="flex items-center gap-0.5 flex-shrink-0">
          <button
            class="h-8 w-8 flex items-center justify-center rounded-md hover:bg-muted transition-colors"
            @click.stop="emit('edit', lead)"
            title="Modifier"
          >
            <Pencil class="w-3.5 h-3.5 text-muted-foreground" />
          </button>
          <button
            class="h-8 w-8 flex items-center justify-center rounded-md hover:bg-destructive/10 hover:text-destructive transition-colors"
            @click.stop="emit('delete', lead)"
            title="Supprimer"
          >
            <Trash2 class="w-3.5 h-3.5 text-muted-foreground" />
          </button>
        </div>
      </div>
    </div>

    <!-- ══════════════════════════════════════════════════════ -->
    <!--  TABLET + DESKTOP — table  (≥ md)                     -->
    <!-- ══════════════════════════════════════════════════════ -->
    <div class="hidden md:block overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-border">
            <!-- Always visible -->
            <SortableHead field="nom"        label="Entreprise" :sort-field="sortField" :sort-dir="sortDir" @sort="emit('sort', $event)" />
            <SortableHead field="segment"    label="Segment"    :sort-field="sortField" :sort-dir="sortDir" @sort="emit('sort', $event)" />
            <!-- Hidden on tablet, visible on desktop -->
            <th class="hidden lg:table-cell text-[11px] font-medium text-muted-foreground px-4 py-3 text-left whitespace-nowrap">Secteur</th>
            <SortableHead field="ville"      label="Ville"      :sort-field="sortField" :sort-dir="sortDir" @sort="emit('sort', $event)" class="hidden lg:table-cell" />
            <th class="hidden xl:table-cell text-[11px] font-medium text-muted-foreground px-4 py-3 text-left whitespace-nowrap">SIREN</th>
            <SortableHead field="ca"         label="CA"         :sort-field="sortField" :sort-dir="sortDir" @sort="emit('sort', $event)" />
            <SortableHead field="nbLocaux"   label="Locaux"     :sort-field="sortField" :sort-dir="sortDir" @sort="emit('sort', $event)" class="hidden lg:table-cell" />
            <SortableHead field="score"      label="Score"      :sort-field="sortField" :sort-dir="sortDir" @sort="emit('sort', $event)" class="hidden lg:table-cell" />
            <SortableHead field="completude" label="Complétude" :sort-field="sortField" :sort-dir="sortDir" @sort="emit('sort', $event)" />
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
            <!-- Entreprise — always visible -->
            <td class="px-4 py-3 max-w-[180px]">
              <div class="flex flex-col">
                <span class="font-medium text-sm text-foreground truncate">{{ lead.nom }}</span>
                <span v-if="lead.hasBoamp" class="mt-0.5">
                  <span class="text-[10px] font-semibold px-1.5 py-0.5 rounded-sm bg-blue-50 text-tacir-blue border border-blue-200">BOAMP</span>
                </span>
              </div>
            </td>
            <!-- Segment — always visible -->
            <td class="px-4 py-3">
              <SegmentBadge :segment="lead.segment" />
            </td>
            <!-- Secteur — lg+ -->
            <td class="hidden lg:table-cell px-4 py-3 text-xs text-muted-foreground max-w-[140px] truncate">
              {{ lead.secteurActivite }}
            </td>
            <!-- Ville — lg+ -->
            <td class="hidden lg:table-cell px-4 py-3 text-xs">{{ lead.ville }}</td>
            <!-- SIREN — xl+ -->
            <td class="hidden xl:table-cell px-4 py-3 text-xs font-mono text-muted-foreground">{{ lead.siren }}</td>
            <!-- CA — always visible -->
            <td class="px-4 py-3 text-xs font-medium">{{ lead.caFormatted }}</td>
            <!-- Locaux — lg+ -->
            <td class="hidden lg:table-cell px-4 py-3 text-xs">{{ lead.nbLocaux ?? '—' }}</td>
            <!-- Score — lg+ -->
            <td class="hidden lg:table-cell px-4 py-3">
              <ScoreRing :score="lead.score" />
            </td>
            <!-- Complétude — always visible -->
            <td class="px-4 py-3">
              <CompletionBar :value="lead.completude" />
            </td>
            <!-- Statut — always visible -->
            <td class="px-4 py-3">
              <StatusBadge :status="lead.status" />
            </td>
            <!-- Actions — always visible -->
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
</template>

<script setup>
import { Eye, Pencil, Trash2 } from 'lucide-vue-next'
import SegmentBadge  from './SegmentBadge.vue'
import StatusBadge   from './StatusBadge.vue'
import ScoreRing     from './ScoreRing.vue'
import CompletionBar from './CompletionBar.vue'
import SortableHead  from './SortableHead.vue'

const props = defineProps({
  leads:     { type: Array,   required: true },
  sortField: { type: String,  required: true },
  sortDir:   { type: String,  required: true },
  loading:   { type: Boolean, default: false },
})

const emit = defineEmits(['sort', 'preview', 'edit', 'delete', 'navigate'])

// Deterministic avatar color from company name
const AVATAR_PALETTE = [
  '#303E8C', '#56A632', '#F29F05', '#04ADBF',
  '#7C3AED', '#DB2777', '#0891B2', '#D97706',
]
function avatarColor(nom) {
  if (!nom) return AVATAR_PALETTE[0]
  const code = [...nom].reduce((acc, c) => acc + c.charCodeAt(0), 0)
  return AVATAR_PALETTE[code % AVATAR_PALETTE.length]
}
</script>
