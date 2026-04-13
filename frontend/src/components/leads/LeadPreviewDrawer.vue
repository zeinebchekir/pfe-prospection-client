<template>
  <Sheet :open="open" @update:open="emit('close')">
    <SheetContent class="w-full sm:w-[460px] max-h-screen overflow-y-auto p-0 flex flex-col">
      <template v-if="lead">
        <!-- Header -->
        <SheetHeader class="p-5 pb-0">
          <div class="flex items-start gap-3">
            <div class="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center text-tacir-blue font-semibold text-base flex-shrink-0">
              {{ initials }}
            </div>
            <div class="flex-1 min-w-0">
              <SheetTitle class="text-base font-semibold text-foreground truncate">{{ lead.nom }}</SheetTitle>
              <p class="text-xs text-muted-foreground mt-0.5">
                SIREN {{ lead.siren }} · {{ lead.ville }}, {{ lead.pays }}
              </p>
              <div class="flex flex-wrap gap-1.5 mt-2">
                <SegmentBadge :segment="lead.segment" />
                <StatusBadge  :status="lead.status"  />
                <span
                  v-if="lead.hasBoamp"
                  class="text-[10px] font-semibold px-2 py-0.5 rounded-sm bg-blue-50 text-tacir-blue border border-blue-200"
                >
                  BOAMP
                </span>
              </div>
            </div>
          </div>
        </SheetHeader>

        <!-- Metrics -->
        <div class="grid grid-cols-3 gap-3 p-5">
          <div class="text-center p-3 rounded-xl bg-muted/50">
            <ScoreRing :score="lead.score" size="md" />
            <p class="text-[10px] text-muted-foreground mt-1">Score</p>
          </div>
          <div class="text-center p-3 rounded-xl bg-muted/50">
            <p class="text-lg font-semibold text-foreground">{{ lead.probaConversion }}%</p>
            <p class="text-[10px] text-muted-foreground">Proba.</p>
          </div>
          <div class="text-center p-3 rounded-xl bg-muted/50">
            <p class="text-lg font-semibold text-foreground">{{ lead.completude }}%</p>
            <p class="text-[10px] text-muted-foreground">Complétude</p>
          </div>
        </div>

        <Separator />

        <!-- Info rows -->
        <div class="p-5 space-y-3">
          <h4 class="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Informations</h4>
          <div class="space-y-2 text-sm">
            <div v-for="row in infoRows" :key="row.label" class="flex items-center gap-2">
              <component :is="row.icon" class="w-3.5 h-3.5 text-muted-foreground flex-shrink-0" />
              <span class="text-muted-foreground text-xs w-28 flex-shrink-0">{{ row.label }}</span>
              <span :class="['text-xs font-medium truncate', row.value === '\u2014' ? 'text-muted-foreground italic' : 'text-foreground']">
                {{ row.value }}
              </span>
            </div>
          </div>
        </div>

        <Separator />

        <!-- Dirigeants -->
        <div class="p-5 space-y-3">
          <h4 class="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1">
            <Users class="w-3.5 h-3.5" /> Dirigeants ({{ lead.nbDirigeants }})
          </h4>
          <div v-if="lead.dirigeants.length === 0" class="text-xs text-muted-foreground italic">
            Aucun dirigeant renseigné
          </div>
          <div
            v-for="d in lead.dirigeants.slice(0, 4)"
            :key="d.id"
            class="flex items-center gap-3 p-2.5 rounded-lg bg-muted/40"
          >
            <div class="w-8 h-8 rounded-full bg-purple-50 text-purple-700 flex items-center justify-center text-[11px] font-semibold flex-shrink-0">
              {{ d.initials }}
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium text-foreground truncate">{{ d.fullName }}</p>
              <p class="text-[11px] text-muted-foreground">{{ d.qualite }}</p>
            </div>
            <div class="flex items-center gap-1">
              <span v-if="d.age" class="text-xs text-muted-foreground">{{ d.age }} ans</span>
              <a
                v-if="d.linkedinUrl"
                :href="d.linkedinUrl"
                target="_blank"
                rel="noreferrer"
                @click.stop
              >
                <Linkedin class="w-3.5 h-3.5 text-blue-600" />
              </a>
            </div>
          </div>
          <p v-if="lead.nbDirigeants > 4" class="text-xs text-muted-foreground text-center">
            +{{ lead.nbDirigeants - 4 }} autres dirigeants
          </p>
        </div>

        <Separator />

        <!-- Actions -->
        <div class="p-5 flex flex-col gap-2 mt-auto">
          <button
            @click="emit('navigate', lead)"
            class="w-full h-9 flex items-center justify-center gap-2 text-sm font-medium rounded-md bg-tacir-blue text-white hover:opacity-90 transition-opacity"
          >
            <Eye class="w-4 h-4" /> Voir la fiche complète
          </button>
          <div class="flex gap-2">
            <button
              @click="emit('edit', lead)"
              class="flex-1 h-9 flex items-center justify-center gap-2 text-sm rounded-md border border-input hover:bg-accent transition-colors"
            >
              <Pencil class="w-3.5 h-3.5" /> Modifier
            </button>
            <button
              @click="emit('delete', lead)"
              class="h-9 px-3 flex items-center justify-center gap-2 text-sm rounded-md border border-input hover:bg-destructive/10 hover:text-destructive hover:border-destructive/30 transition-colors"
            >
              <Trash2 class="w-3.5 h-3.5" /> Supprimer
            </button>
          </div>
        </div>
      </template>
    </SheetContent>
  </Sheet>
</template>

<script setup>
import { computed } from 'vue'
import { Eye, Pencil, Trash2, MapPin, Phone, Mail, Linkedin, Building2, Users } from 'lucide-vue-next'
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { Separator } from '@/components/ui/separator'
import SegmentBadge from './SegmentBadge.vue'
import StatusBadge  from './StatusBadge.vue'
import ScoreRing    from './ScoreRing.vue'

const props = defineProps({
  lead: { type: Object, default: null },
  open: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'navigate', 'edit', 'delete'])

const initials = computed(() => {
  if (!props.lead) return ''
  return props.lead.nom
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0] ?? '')
    .join('')
    .toUpperCase()
})

const infoRows = computed(() => {
  if (!props.lead) return []
  const l = props.lead
  return [
    { icon: Building2, label: 'Secteur',         value: l.secteurActivite },
    { icon: Building2, label: 'Forme juridique', value: l.formeJuridique },
    { icon: Building2, label: 'CA',              value: l.caFormatted },
    { icon: MapPin,    label: 'Ville',            value: `${l.ville} (${l.codePostal})` },
    { icon: Phone,     label: 'Téléphone',        value: l.telephone },
    { icon: Mail,      label: 'Email',            value: l.email },
  ]
})
</script>
