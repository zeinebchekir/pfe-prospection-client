<template>
  <Dialog :open="open" @update:open="handleOpenChange">
    <DialogContent class="max-w-md p-0 overflow-hidden">
      <DialogHeader class="px-6 pt-6 pb-4 border-b border-border">
        <DialogTitle class="text-lg font-semibold text-foreground">
          Supprimer ce lead ?
        </DialogTitle>
      </DialogHeader>

      <div class="px-6 py-5">
        <p class="text-sm text-muted-foreground leading-relaxed">
          Cette action supprimera definitivement
          <strong class="text-foreground">"{{ lead?.company_name || 'ce lead' }}"</strong>.
        </p>
      </div>

      <div class="px-6 py-4 border-t border-border bg-muted/20 flex flex-col-reverse sm:flex-row justify-end gap-3">
        <button
          type="button"
          class="h-9 px-4 text-sm font-medium rounded-md border border-input hover:bg-accent transition-colors disabled:opacity-50"
          :disabled="deleting"
          @click="handleOpenChange(false)"
        >
          Annuler
        </button>
        <button
          type="button"
          class="h-9 px-5 text-sm font-semibold rounded-md bg-red-600 text-white hover:bg-red-700 transition-colors disabled:opacity-60"
          :disabled="deleting"
          @click="$emit('confirm')"
        >
          {{ deleting ? 'Suppression...' : 'Supprimer' }}
        </button>
      </div>
    </DialogContent>
  </Dialog>
</template>

<script setup>
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

defineProps({
  open: { type: Boolean, default: false },
  deleting: { type: Boolean, default: false },
  lead: { type: Object, default: null },
})

const emit = defineEmits(['update:open', 'confirm'])

function handleOpenChange(nextOpen) {
  emit('update:open', nextOpen)
}
</script>
