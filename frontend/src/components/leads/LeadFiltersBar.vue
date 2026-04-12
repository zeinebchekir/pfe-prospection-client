<template>
  <div class="space-y-3">
    <!-- Search + toggle button -->
    <div class="flex items-center gap-3">
      <!-- Search input -->
      <div class="relative flex-1">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <input
          id="leads-search"
          type="text"
          placeholder="Rechercher par nom, SIREN, ville, secteur, dirigeant…"
          :value="filters.search"
          @input="emit('update:filter', 'search', $event.target.value)"
          class="
            w-full pl-9 pr-8 h-9 text-sm rounded-md border border-input bg-background
            ring-offset-background placeholder:text-muted-foreground
            focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2
          "
        />
        <button
          v-if="filters.search"
          @click="emit('update:filter', 'search', '')"
          class="absolute right-3 top-1/2 -translate-y-1/2"
          aria-label="Effacer la recherche"
        >
          <X class="w-3.5 h-3.5 text-muted-foreground hover:text-foreground" />
        </button>
      </div>

      <!-- Toggle expanded filters -->
      <button
        id="leads-filter-toggle"
        @click="filtersOpen = !filtersOpen"
        class="
          inline-flex items-center gap-2 h-9 px-3 text-sm rounded-md border border-input
          bg-background hover:bg-accent hover:text-accent-foreground
          focus:outline-none focus:ring-2 focus:ring-ring transition-colors
        "
        :aria-expanded="filtersOpen"
      >
        <SlidersHorizontal class="w-3.5 h-3.5" />
        Filtres
        <span
          v-if="activeCount > 0"
          class="ml-1 h-5 px-1.5 text-[10px] bg-tacir-blue text-white rounded-full inline-flex items-center font-semibold"
        >
          {{ activeCount }}
        </span>
      </button>

      <!-- Reset -->
      <button
        v-if="activeCount > 0"
        @click="emit('reset')"
        class="
          inline-flex items-center gap-1 h-9 px-3 text-sm rounded-md text-muted-foreground
          hover:bg-accent hover:text-accent-foreground transition-colors
        "
      >
        <RotateCcw class="w-3.5 h-3.5" />
        Réinitialiser
      </button>
    </div>

    <!-- Active filter chips -->
    <div v-if="activeCount > 0" class="flex flex-wrap gap-1.5">
      <button
        v-for="s in filters.segments"
        :key="`seg-${s}`"
        @click="emit('toggle-array', 'segments', s)"
        class="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground hover:bg-secondary/80"
      >
        {{ s }} <X class="w-3 h-3" />
      </button>
      <button
        v-for="s in filters.statuses"
        :key="`sta-${s}`"
        @click="emit('toggle-array', 'statuses', s)"
        class="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground hover:bg-secondary/80"
      >
        {{ s }} <X class="w-3 h-3" />
      </button>
      <button
        v-for="v in filters.villes"
        :key="`ville-${v}`"
        @click="emit('toggle-array', 'villes', v)"
        class="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground hover:bg-secondary/80"
      >
        {{ v }} <X class="w-3 h-3" />
      </button>
      <button
        v-if="filters.hasBoamp !== null"
        @click="emit('update:filter', 'hasBoamp', null)"
        class="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground hover:bg-secondary/80"
      >
        BOAMP: {{ filters.hasBoamp ? 'Oui' : 'Non' }} <X class="w-3 h-3" />
      </button>
      <button
        v-if="filters.hasEmail !== null"
        @click="emit('update:filter', 'hasEmail', null)"
        class="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground hover:bg-secondary/80"
      >
        Email: {{ filters.hasEmail ? 'Oui' : 'Non' }} <X class="w-3 h-3" />
      </button>
      <button
        v-if="filters.hasTelephone !== null"
        @click="emit('update:filter', 'hasTelephone', null)"
        class="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground hover:bg-secondary/80"
      >
        Tél: {{ filters.hasTelephone ? 'Oui' : 'Non' }} <X class="w-3 h-3" />
      </button>
      <button
        v-if="filters.hasLinkedin !== null"
        @click="emit('update:filter', 'hasLinkedin', null)"
        class="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground hover:bg-secondary/80"
      >
        LinkedIn: {{ filters.hasLinkedin ? 'Oui' : 'Non' }} <X class="w-3 h-3" />
      </button>
      <button
        v-if="filters.hasDirigeants !== null"
        @click="emit('update:filter', 'hasDirigeants', null)"
        class="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground hover:bg-secondary/80"
      >
        Dirigeants: {{ filters.hasDirigeants ? 'Oui' : 'Non' }} <X class="w-3 h-3" />
      </button>
      <button
        v-if="filters.scoreMin !== null || filters.scoreMax !== null"
        @click="emit('update:filter', 'scoreMin', null); emit('update:filter', 'scoreMax', null)"
        class="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground hover:bg-secondary/80"
      >
        Score: {{ filters.scoreMin ?? '0' }}–{{ filters.scoreMax ?? '100' }} <X class="w-3 h-3" />
      </button>
      <button
        v-if="filters.caMin !== null || filters.caMax !== null"
        @click="emit('update:filter', 'caMin', null); emit('update:filter', 'caMax', null)"
        class="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground hover:bg-secondary/80"
      >
        CA filtré <X class="w-3 h-3" />
      </button>
    </div>

    <!-- Expanded filter panel -->
    <Transition name="filter-expand">
      <div
        v-if="filtersOpen"
        class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3 p-4 rounded-xl border border-border bg-card"
      >
        <!-- Segment -->
        <div class="space-y-1">
          <label class="text-[11px] font-medium text-muted-foreground">Segment</label>
          <div class="flex flex-wrap gap-1">
            <button
              v-for="s in uniqueSegments"
              :key="s"
              @click="emit('toggle-array', 'segments', s)"
              :class="[
                'text-[10px] px-2 py-0.5 rounded-full border font-medium transition-colors',
                filters.segments.includes(s)
                  ? 'bg-tacir-blue text-white border-tacir-blue'
                  : 'border-border text-muted-foreground hover:border-tacir-blue hover:text-tacir-blue'
              ]"
            >
              {{ s }}
            </button>
          </div>
        </div>

        <!-- Statut -->
        <div class="space-y-1">
          <label class="text-[11px] font-medium text-muted-foreground">Statut</label>
          <div class="flex flex-wrap gap-1">
            <button
              v-for="s in uniqueStatuses"
              :key="s"
              @click="emit('toggle-array', 'statuses', s)"
              :class="[
                'text-[10px] px-2 py-0.5 rounded-full border font-medium transition-colors',
                filters.statuses.includes(s)
                  ? 'bg-tacir-blue text-white border-tacir-blue'
                  : 'border-border text-muted-foreground hover:border-tacir-blue hover:text-tacir-blue'
              ]"
            >
              {{ s }}
            </button>
          </div>
        </div>

        <!-- Ville -->
        <div class="space-y-1">
          <label class="text-[11px] font-medium text-muted-foreground">Ville</label>
          <select
            :value="filters.villes[0] ?? ''"
            @change="emit('update:filter', 'villes', $event.target.value ? [$event.target.value] : [])"
            class="w-full h-8 text-xs rounded-md border border-input bg-background px-2 focus:outline-none focus:ring-1 focus:ring-ring"
          >
            <option value="">Toutes</option>
            <option v-for="v in uniqueVilles.slice(0, 30)" :key="v" :value="v">{{ v }}</option>
          </select>
        </div>

        <!-- BOAMP -->
        <div class="space-y-1">
          <label class="text-[11px] font-medium text-muted-foreground">BOAMP</label>
          <select
            :value="filters.hasBoamp === null ? '' : filters.hasBoamp ? 'true' : 'false'"
            @change="emit('update:filter', 'hasBoamp', $event.target.value === '' ? null : $event.target.value === 'true')"
            class="w-full h-8 text-xs rounded-md border border-input bg-background px-2 focus:outline-none focus:ring-1 focus:ring-ring"
          >
            <option value="">Tous</option>
            <option value="true">Oui</option>
            <option value="false">Non</option>
          </select>
        </div>

        <!-- Email -->
        <div class="space-y-1">
          <label class="text-[11px] font-medium text-muted-foreground">Email</label>
          <select
            :value="filters.hasEmail === null ? '' : filters.hasEmail ? 'true' : 'false'"
            @change="emit('update:filter', 'hasEmail', $event.target.value === '' ? null : $event.target.value === 'true')"
            class="w-full h-8 text-xs rounded-md border border-input bg-background px-2 focus:outline-none focus:ring-1 focus:ring-ring"
          >
            <option value="">Tous</option>
            <option value="true">Avec</option>
            <option value="false">Sans</option>
          </select>
        </div>

        <!-- Téléphone -->
        <div class="space-y-1">
          <label class="text-[11px] font-medium text-muted-foreground">Téléphone</label>
          <select
            :value="filters.hasTelephone === null ? '' : filters.hasTelephone ? 'true' : 'false'"
            @change="emit('update:filter', 'hasTelephone', $event.target.value === '' ? null : $event.target.value === 'true')"
            class="w-full h-8 text-xs rounded-md border border-input bg-background px-2 focus:outline-none focus:ring-1 focus:ring-ring"
          >
            <option value="">Tous</option>
            <option value="true">Avec</option>
            <option value="false">Sans</option>
          </select>
        </div>

        <!-- LinkedIn dirigeant -->
        <div class="space-y-1">
          <label class="text-[11px] font-medium text-muted-foreground">LinkedIn</label>
          <select
            :value="filters.hasLinkedin === null ? '' : filters.hasLinkedin ? 'true' : 'false'"
            @change="emit('update:filter', 'hasLinkedin', $event.target.value === '' ? null : $event.target.value === 'true')"
            class="w-full h-8 text-xs rounded-md border border-input bg-background px-2 focus:outline-none focus:ring-1 focus:ring-ring"
          >
            <option value="">Tous</option>
            <option value="true">Avec</option>
            <option value="false">Sans</option>
          </select>
        </div>

        <!-- Dirigeants -->
        <div class="space-y-1">
          <label class="text-[11px] font-medium text-muted-foreground">Dirigeants</label>
          <select
            :value="filters.hasDirigeants === null ? '' : filters.hasDirigeants ? 'true' : 'false'"
            @change="emit('update:filter', 'hasDirigeants', $event.target.value === '' ? null : $event.target.value === 'true')"
            class="w-full h-8 text-xs rounded-md border border-input bg-background px-2 focus:outline-none focus:ring-1 focus:ring-ring"
          >
            <option value="">Tous</option>
            <option value="true">Avec</option>
            <option value="false">Sans</option>
          </select>
        </div>

        <!-- Score min -->
        <div class="space-y-1">
          <label class="text-[11px] font-medium text-muted-foreground">Score min</label>
          <input
            type="number"
            min="0"
            max="100"
            :value="filters.scoreMin ?? ''"
            @change="emit('update:filter', 'scoreMin', $event.target.value === '' ? null : Number($event.target.value))"
            placeholder="0"
            class="w-full h-8 text-xs rounded-md border border-input bg-background px-2 focus:outline-none focus:ring-1 focus:ring-ring"
          />
        </div>

        <!-- Score max -->
        <div class="space-y-1">
          <label class="text-[11px] font-medium text-muted-foreground">Score max</label>
          <input
            type="number"
            min="0"
            max="100"
            :value="filters.scoreMax ?? ''"
            @change="emit('update:filter', 'scoreMax', $event.target.value === '' ? null : Number($event.target.value))"
            placeholder="100"
            class="w-full h-8 text-xs rounded-md border border-input bg-background px-2 focus:outline-none focus:ring-1 focus:ring-ring"
          />
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Search, SlidersHorizontal, X, RotateCcw } from 'lucide-vue-next'

const props = defineProps({
  filters: { type: Object, required: true },
  activeCount: { type: Number, default: 0 },
  uniqueVilles: { type: Array, default: () => [] },
  uniqueSegments: { type: Array, default: () => [] },
  uniqueStatuses: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:filter', 'toggle-array', 'reset'])

const filtersOpen = ref(false)
</script>

<style scoped>
.filter-expand-enter-active,
.filter-expand-leave-active {
  transition: all 0.2s ease;
  overflow: hidden;
}
.filter-expand-enter-from,
.filter-expand-leave-to {
  opacity: 0;
  max-height: 0;
}
.filter-expand-enter-to,
.filter-expand-leave-from {
  opacity: 1;
  max-height: 400px;
}
</style>
