<template>
  <Dialog :open="open" @update:open="handleOpenChange">
    <DialogContent class="max-w-md p-0 overflow-hidden">
      
      <!-- Header -->
      <DialogHeader class="px-6 pt-6 pb-4 border-b border-border">
        <DialogTitle class="text-lg font-semibold flex items-center gap-2 text-foreground">
          <span class="w-8 h-8 rounded-xl bg-red-100 flex items-center justify-center flex-shrink-0">
            <Trash2 class="w-4 h-4 text-red-600" />
          </span>
          Supprimer ce lead ?
        </DialogTitle>
      </DialogHeader>

      <!-- Body -->
      <div class="px-6 py-5">
        <p class="text-sm text-muted-foreground leading-relaxed">
          Êtes-vous sûr de vouloir supprimer le lead 
          <strong class="text-foreground font-semibold">"{{ lead?.nom }}"</strong> ? 
          Cette action est irréversible et supprimera toutes les données associées.
        </p>
      </div>

      <!-- Footer -->
      <div class="px-6 py-4 border-t border-border bg-muted/20 flex flex-col-reverse sm:flex-row justify-end gap-3">
        <button
          @click="handleClose"
          :disabled="isDeleting"
          class="h-9 px-4 text-sm font-medium rounded-md border border-input hover:bg-accent transition-colors disabled:opacity-50"
        >
          Annuler
        </button>
        <button
          @click="handleDelete"
          :disabled="isDeleting"
          class="h-9 px-5 text-sm font-semibold rounded-md bg-red-600 text-white hover:bg-red-700 active:scale-95 transition-all flex items-center justify-center gap-2 disabled:opacity-60 shadow-sm"
        >
          <Loader2 v-if="isDeleting" class="h-4 w-4 animate-spin" />
          {{ isDeleting ? 'Suppression...' : 'Supprimer' }}
        </button>
      </div>
      
    </DialogContent>
  </Dialog>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { Trash2, Loader2 } from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
} from '@/components/ui/dialog'

const props = defineProps({
  open: { type: Boolean, default: false },
  lead: { type: Object, default: null }
})

const emit = defineEmits(['close', 'deleted'])

const BASE_URL = import.meta.env.VITE_FASTAPI_URL || 'http://localhost:8001'

const isDeleting = ref(false)

function handleClose() {
  if (isDeleting.value) return
  emit('close')
}

function handleOpenChange(val) {
  if (!val) handleClose()
}

async function handleDelete() {
  if (!props.lead?.id) return
  
  isDeleting.value = true
  try {
    const response = await axios.delete(`${BASE_URL}/entreprises/${props.lead.id}`, {
      headers: {
        'Accept': 'application/json'
      }
    })
    
    toast.success('Lead supprimé', {
      description: response.data.message || `Lead '${props.lead.nom}' supprimé avec succès.`,
    })
    
    emit('deleted', props.lead.id)
    emit('close')
    
  } catch (error) {
    console.error('[DeleteLead] error:', error)
    toast.error('Erreur de suppression', {
      description: error.response?.data?.detail || 'Une erreur inattendue est survenue.',
    })
  } finally {
    isDeleting.value = false
  }
}
</script>
