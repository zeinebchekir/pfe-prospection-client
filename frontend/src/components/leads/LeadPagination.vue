<template>
  <div v-if="totalItems > 0" class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-4">
    <div class="flex items-center gap-4">
      <p class="text-xs text-muted-foreground">
        {{ rangeStart }}–{{ rangeEnd }} sur {{ totalItems }} leads
      </p>
      <div class="flex items-center gap-1.5 text-xs text-muted-foreground">
        <label for="pageSize">Lignes par page :</label>
        <select
          id="pageSize"
          :value="pageSize"
          @change="emit('size-change', Number($event.target.value))"
          class="h-7 rounded-md border border-input bg-transparent px-2 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-tacir-blue"
        >
          <option :value="10">10</option>
          <option :value="20">20</option>
          <option :value="50">50</option>
          <option :value="100">100</option>
        </select>
      </div>
    </div>

    <div class="flex items-center gap-1" v-if="totalPages > 1">
      <!-- Previous -->
      <button
        :disabled="page <= 1"
        @click="emit('page-change', page - 1)"
        class="h-8 px-3 text-xs rounded-md border border-input hover:bg-accent transition-colors disabled:opacity-50 disabled:pointer-events-none"
      >
        Préc.
      </button>

      <!-- Page buttons -->
      <template v-for="p in pageNumbers" :key="p === 'ellipsis' ? `e-${p}` : p">
        <span v-if="p === 'ellipsis'" class="px-2 text-xs text-muted-foreground">…</span>
        <button
          v-else
          @click="emit('page-change', p)"
          :class="[
            'h-8 w-8 text-xs rounded-md border transition-colors',
            p === page
              ? 'bg-tacir-blue text-white border-tacir-blue'
              : 'border-input hover:bg-accent'
          ]"
        >
          {{ p }}
        </button>
      </template>

      <!-- Next -->
      <button
        :disabled="page >= totalPages"
        @click="emit('page-change', page + 1)"
        class="h-8 px-3 text-xs rounded-md border border-input hover:bg-accent transition-colors disabled:opacity-50 disabled:pointer-events-none"
      >
        Suiv.
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  page:       { type: Number, required: true },
  totalPages: { type: Number, required: true },
  totalItems: { type: Number, required: true },
  pageSize:   { type: Number, required: true },
})

const emit = defineEmits(['page-change', 'size-change'])

const rangeStart = computed(() => (props.page - 1) * props.pageSize + 1)
const rangeEnd   = computed(() => Math.min(props.page * props.pageSize, props.totalItems))

const pageNumbers = computed(() => {
  const { page, totalPages } = props
  const pages = []
  if (totalPages <= 7) {
    for (let i = 1; i <= totalPages; i++) pages.push(i)
  } else {
    pages.push(1)
    if (page > 3) pages.push('ellipsis')
    for (let i = Math.max(2, page - 1); i <= Math.min(totalPages - 1, page + 1); i++) {
      pages.push(i)
    }
    if (page < totalPages - 2) pages.push('ellipsis')
    pages.push(totalPages)
  }
  return pages
})
</script>
