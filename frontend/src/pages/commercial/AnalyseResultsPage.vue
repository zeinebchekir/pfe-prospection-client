<template>
  <div>
    <div class="flex min-h-screen bg-tacir-lightgray/30">
      <TheSidebar />
      <div class="flex-1 flex flex-col min-w-0">
        <!-- Header -->
        <header class="h-14 sm:h-16 border-b border-border bg-white sticky top-0 z-40 px-3 sm:px-6 flex items-center shadow-sm gap-4">
          <button @click="goBack" class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-tacir-lightgray text-tacir-darkgray transition-colors">
            <ArrowLeft class="h-4 w-4" />
          </button>
          <span class="text-sm font-semibold truncate">Résultats d'analyse: {{ lead?.nom || 'Entreprise' }}</span>
        </header>

        <main class="flex-1 p-6 md:p-8 overflow-y-auto">
          <div class="max-w-[1100px] mx-auto space-y-6">
            
            <div v-if="!result" class="flex flex-col items-center justify-center p-12 bg-white rounded-xl border shadow-card">
              <Loader2 class="w-8 h-8 animate-spin text-tacir-blue mb-4" v-if="isLoading" />
              <p class="text-muted-foreground">{{ isLoading ? 'Chargement...' : 'Aucune donnée trouvée. Veuillez relancer une analyse.' }}</p>
              <Button v-if="!isLoading" @click="goBack" class="mt-4">Retour</Button>
            </div>

            <template v-else>
              <!-- Score Card -->
              <div class="bg-white rounded-xl border border-border shadow-card p-6 flex flex-col md:flex-row items-center gap-8">
                <!-- gauge / score -->
                <div class="relative w-32 h-32 flex shrink-0 items-center justify-center rounded-full" :class="scoreColorBg">
                  <svg class="absolute inset-0 w-full h-full transform -rotate-90">
                    <circle cx="64" cy="64" r="58" class="stroke-muted/30" stroke-width="12" fill="none" />
                    <circle cx="64" cy="64" r="58" :class="scoreColorStroke" stroke-width="12" fill="none" :stroke-dasharray="364" :stroke-dashoffset="364 - (364 * result.score / 100)" stroke-linecap="round" class="transition-all duration-1000 ease-out" />
                  </svg>
                  <div class="flex flex-col items-center justify-center z-10">
                    <span class="text-4xl font-bold" :class="scoreColorText">{{result.score}}</span>
                    <span class="text-[10px] text-muted-foreground font-medium uppercase tracking-wider">/ 100</span>
                  </div>
                </div>
                
                <div class="flex-1 min-w-0 space-y-3">
                  <div>
                    <h2 class="text-2xl font-bold mb-3 flex items-center justify-between">
                      <span class="flex items-center gap-3">
                        Potentiel: <span :class="scoreColorText">{{result.score >=75 ? 'Fort' : result.score >=40 ? 'Moyen' : 'Faible'}}</span>
                      </span>
                    </h2>
                    <p class="text-foreground leading-relaxed text-sm p-4 bg-muted/40 rounded-lg border">
                      {{ result.resume_strategique }}
                    </p>
                  </div>
                </div>
              </div>

              <!-- Two columns layout -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                
                <!-- Besoins liés aux services -->
                <div class="bg-white rounded-xl border border-border shadow-card p-5 h-full flex flex-col">
                  <div class="flex items-center gap-2 mb-4 pb-3 border-b shrink-0">
                    <div class="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center">
                      <Target class="w-4 h-4 text-blue-600" />
                    </div>
                    <h2 class="text-sm font-semibold">Besoins potentiels liés aux services</h2>
                  </div>
                  
                  <div v-if="parsedBesoins.length === 0" class="flex-1 flex items-center justify-center text-sm text-muted-foreground italic py-8">
                    Aucun besoin potentiel identifié.
                  </div>
                  
                  <div v-else class="space-y-4 flex-1">
                    <div v-for="(besoin, i) in parsedBesoins" :key="i" class="bg-muted/30 rounded-lg p-4 border border-border hover:border-blue-200 transition-colors">
                      <h3 class="text-sm font-bold text-foreground mb-1.5 flex items-start gap-2">
                        <span class="text-blue-500 mt-0.5">📡</span>
                        <span class="leading-snug">{{ typeof besoin === 'object' ? besoin.signal : besoin }}</span>
                      </h3>
                      
                      <p v-if="besoin.besoin_it" class="text-sm text-muted-foreground ml-6 mb-3 leading-relaxed flex items-start gap-2">
                        <span class="text-amber-500 shrink-0 mt-0.5">💡</span>
                        <span>{{ besoin.besoin_it }}</span>
                      </p>
                      
                      <div v-if="besoin.service_numeryx" class="ml-6 flex items-center gap-2">
                        <span class="text-xs text-muted-foreground shrink-0 flex items-center gap-1"><span class="text-emerald-500">🏷</span> Service concerné:</span>
                        <span class="text-[11px] font-medium px-2 py-1 rounded-md border" :class="getServiceColor(besoin.service_numeryx)">
                          {{ besoin.service_numeryx }}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Signaux Positifs & Négatifs -->
                <div class="space-y-6">
                  <div class="bg-white rounded-xl border border-border shadow-card p-5">
                    <div class="flex items-center gap-2 mb-4 pb-3 border-b">
                      <div class="w-8 h-8 rounded-lg bg-emerald-50 flex items-center justify-center">
                        <ThumbsUp class="w-4 h-4 text-emerald-600" />
                      </div>
                      <h2 class="text-sm font-semibold text-emerald-800">Signaux positifs</h2>
                    </div>
                    <ul class="space-y-3">
                      <li v-for="(signal, i) in result.signaux_positifs" :key="i" class="flex items-start gap-3 text-sm">
                        <CheckCircle2 class="w-4 h-4 text-emerald-500 mt-0.5 shrink-0 bg-emerald-50 rounded-full" />
                        <span class="text-emerald-900 leading-snug">{{ signal }}</span>
                      </li>
                    </ul>
                    <div v-if="!result.signaux_positifs?.length" class="text-sm text-muted-foreground italic">Aucun signal positif.</div>
                  </div>

                  <div class="bg-white rounded-xl border border-border shadow-card p-5">
                    <div class="flex items-center gap-2 mb-4 pb-3 border-b">
                      <div class="w-8 h-8 rounded-lg bg-rose-50 flex items-center justify-center">
                        <ThumbsDown class="w-4 h-4 text-rose-600" />
                      </div>
                      <h2 class="text-sm font-semibold text-rose-800">Signaux négatifs / Risques</h2>
                    </div>
                    <ul class="space-y-3">
                      <li v-for="(signal, i) in result.signaux_negatifs" :key="i" class="flex items-start gap-3 text-sm">
                        <AlertTriangle class="w-4 h-4 text-rose-500 mt-0.5 shrink-0 bg-rose-50 rounded-full" />
                        <span class="text-rose-900 leading-snug">{{ signal }}</span>
                      </li>
                    </ul>
                    <div v-if="!result.signaux_negatifs?.length" class="text-sm text-muted-foreground italic">Aucun signal négatif.</div>
                  </div>
                </div>

              </div>

              <!-- Recommandation IA Card -->
              <div v-if="result.recommandation" class="bg-white rounded-xl border border-border shadow-card p-6 mt-6">
                <div class="flex items-center gap-2 mb-4 pb-3 border-b">
                  <div class="w-8 h-8 rounded-lg bg-amber-50 flex items-center justify-center">
                    <Sparkles class="w-4 h-4 text-amber-600" />
                  </div>
                  <h2 class="text-sm font-semibold text-amber-800">Recommandation IA</h2>
                </div>
                <div class="bg-amber-50/50 rounded-lg p-4 border border-amber-100">
                  <p class="text-sm text-foreground leading-relaxed whitespace-pre-wrap">
                    {{ result.recommandation }}
                  </p>
                </div>
              </div>

              <!-- Generate Email Button Section -->
              <div class="mt-8 mb-8 flex justify-center">
                <Button
                  @click="generateEmail"
                  :disabled="isGeneratingEmail"
                  class="bg-blue-600 hover:bg-blue-700 text-white shadow-md gap-2 h-11 px-6"
                  size="lg"
                >
                  <Loader2 v-if="isGeneratingEmail" class="w-4 h-4 animate-spin" />
                  <Mail v-else class="w-4 h-4" />
                  {{ isGeneratingEmail ? 'Génération en cours...' : '✉ Générer un email de prospection' }}
                </Button>
              </div>

            </template>
          </div>
        </main>
      </div>
    </div>

    <!-- Email Modal -->
    <Dialog :open="showEmailModal" @update:open="showEmailModal = $event">
      <DialogContent class="max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader class="px-6 py-4 border-b">
          <DialogTitle class="flex items-center gap-2">
            <Mail class="w-5 h-5 text-primary" /> Email de prospection généré
          </DialogTitle>
          <DialogDescription>
            Vous pouvez ajuster le contenu avant de le copier.
          </DialogDescription>
        </DialogHeader>
        
        <div class="space-y-4 px-6 py-4 flex-1 overflow-y-auto">
          <div class="space-y-2">
            <Label for="email-subject">Objet</Label>
            <Input id="email-subject" v-model="generatedEmailSubject" />
          </div>
          <div class="space-y-2">
            <Label for="email-body">Corps de l'email</Label>
            <Textarea 
              id="email-body"
              v-model="generatedEmailBody" 
              class="min-h-[250px] resize-y"
            />
          </div>

          <!-- AI Chat Assistant -->
          <div class="border border-border rounded-xl overflow-hidden bg-muted/20">
            <!-- Chat header -->
            <div class="flex items-center justify-between px-4 py-2.5 border-b border-border bg-white">
              <div class="flex items-center gap-2">
                <div class="w-6 h-6 rounded-md bg-blue-50 flex items-center justify-center">
                  <Bot class="w-3.5 h-3.5 text-blue-600" />
                </div>
                <span class="text-xs font-semibold text-foreground">Ajuster avec l'IA</span>
              </div>
              <button
                v-if="chatHistory.length > 1"
                @click="resetChat"
                class="flex items-center gap-1 text-[11px] text-muted-foreground hover:text-foreground transition-colors px-2 py-1 rounded-md hover:bg-muted"
                title="Réinitialiser la conversation"
              >
                <RotateCcw class="w-3 h-3" />
                Recommencer
              </button>
            </div>

            <!-- Conversation bubbles (last 3 user+assistant pairs, skip first assistant = original email) -->
            <div v-if="chatHistory.length > 1" class="px-4 py-3 space-y-2 max-h-40 overflow-y-auto">
              <template v-for="(msg, i) in chatHistory.slice(1).slice(-6)" :key="i">
                <div
                  :class="[
                    'flex',
                    msg.role === 'user' ? 'justify-end' : 'justify-start'
                  ]"
                >
                  <div
                    :class="[
                      'max-w-[80%] text-[11px] leading-relaxed px-3 py-2 rounded-xl',
                      msg.role === 'user'
                        ? 'bg-blue-600 text-white rounded-br-sm'
                        : 'bg-white border border-border text-foreground rounded-bl-sm'
                    ]"
                  >
                    <span v-if="msg.role === 'assistant'" class="line-clamp-2">
                      ✅ Email mis à jour
                    </span>
                    <span v-else>{{ msg.content }}</span>
                  </div>
                </div>
              </template>
            </div>

            <!-- Chat input -->
            <div class="flex items-center gap-2 px-3 py-2.5 border-t border-border bg-white">
              <input
                id="chat-adjustment-input"
                v-model="chatInput"
                @keydown.enter.prevent="sendAdjustment"
                :disabled="isAdjusting"
                type="text"
                placeholder="Ex: Rends le ton plus formel, raccourcis l'introduction..."
                class="flex-1 text-xs bg-muted/40 border border-border rounded-lg px-3 py-2 outline-none focus:ring-1 focus:ring-blue-400 focus:border-blue-400 disabled:opacity-50 transition-all"
              />
              <button
                @click="sendAdjustment"
                :disabled="isAdjusting || !chatInput.trim()"
                class="flex items-center justify-center w-8 h-8 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40 transition-colors flex-shrink-0"
                title="Envoyer"
              >
                <Loader2 v-if="isAdjusting" class="w-3.5 h-3.5 animate-spin" />
                <Send v-else class="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>

        <DialogFooter class="flex sm:justify-between items-center gap-3 px-6 py-4 border-t bg-muted/20">
          <p v-if="emailError" class="text-sm text-red-500">{{ emailError }}</p>
          <div class="flex gap-2 w-full sm:w-auto justify-end ml-auto">
            <Button variant="outline" @click="showEmailModal = false">
              Fermer
            </Button>
            <Button @click="copyGeneratedEmail" class="gap-2">
              <Check v-if="emailCopied" class="w-4 h-4" />
              <Copy v-else class="w-4 h-4" />
              {{ emailCopied ? 'Copié !' : 'Copier' }}
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowLeft, Loader2, Target, ThumbsUp, ThumbsDown, 
  CheckCircle2, AlertTriangle, Mail, Copy, Check, Sparkles,
  Send, RotateCcw, Bot
} from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import TheSidebar from '@/components/AppSidebar.vue'
import { Button } from '@/components/ui/button'
import Textarea from '@/components/ui/textarea/Textarea.vue'
import { 
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter 
} from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import axios from 'axios'

const router = useRouter()
const result = ref(null)
const lead = ref(null)
const isLoading = ref(true)

const emailCorps = ref('')
const copied = ref(false)

const isGeneratingEmail = ref(false)
const showEmailModal = ref(false)
const generatedEmailSubject = ref('')
const generatedEmailBody = ref('')
const emailCopied = ref(false)
const emailError = ref('')

// Chat assistant state
const chatHistory = ref([])
const originalEmail = ref({ subject: '', body: '' })
const chatInput = ref('')
const isAdjusting = ref(false)

onMounted(() => {
  try {
    const storedResult = sessionStorage.getItem('analysisResult')
    const storedLead = sessionStorage.getItem('analysisLead')
    if (storedResult) {
      result.value = JSON.parse(storedResult)
      emailCorps.value = result.value.email_prospection?.corps || ''
    }
    if (storedLead) {
      lead.value = JSON.parse(storedLead)
    }
  } catch (e) {
    console.error("Erreur de parsing des données d'analyse", e)
  } finally {
    isLoading.value = false
  }
})

const goBack = () => {
  if (lead.value?.id) {
    router.push(`/commercial/leads/${lead.value.id}`)
  } else {
    router.back()
  }
}

const copyEmail = async () => {
  const fullEmail = `Objet : ${result.value?.email_prospection?.objet || ''}\n\n${emailCorps.value}`
  try {
    await navigator.clipboard.writeText(fullEmail)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch (err) {
    console.error('Failed to copy', err)
  }
}

const generateEmail = async () => {
  if (!result.value || !lead.value) return;
  
  isGeneratingEmail.value = true
  emailError.value = ''
  
  try {
    result.value["nom"]=lead.value.nom;
    const payload = {
      rapport: result.value,
      remarques: ''
    }
    
    const baseUrl = import.meta.env.VITE_IA_SERVICE_URL || 'http://localhost:8002'
    const response = await axios.post(`${baseUrl}/ia/generate-email`, payload)
    
    const subject = response.data.objet || 'Proposition de collaboration Numeryx'
    const body = response.data.corps || ''

    generatedEmailSubject.value = subject
    generatedEmailBody.value = body

    // Init chat history with the first generated email
    const fullEmail = `Objet : ${subject}\n\n${body}`
    chatHistory.value = [{ role: 'assistant', content: fullEmail }]
    originalEmail.value = { subject, body }
    chatInput.value = ''
    
    showEmailModal.value = true
  } catch (err) {
    console.error('Error generating email:', err)
    emailError.value = err.response?.data?.detail || "Erreur lors de la génération de l'email."
    toast.error(emailError.value)
  } finally {
    isGeneratingEmail.value = false
  }
}

const sendAdjustment = async () => {
  const userMsg = chatInput.value.trim()
  if (!userMsg || isAdjusting.value) return
  if (!result.value || !lead.value) return

  isAdjusting.value = true
  emailError.value = ''

  const messagesWithNew = [
    ...chatHistory.value,
    { role: 'user', content: userMsg }
  ]

  try {
    result.value["nom"] = lead.value.nom
    const payload = {
      rapport: result.value,
      remarques: '',
      messages: messagesWithNew
    }

    const baseUrl = import.meta.env.VITE_IA_SERVICE_URL || 'http://localhost:8002'
    const response = await axios.post(`${baseUrl}/ia/generate-email`, payload)

    const newSubject = response.data.objet || generatedEmailSubject.value
    const newBody = response.data.corps || ''

    generatedEmailSubject.value = newSubject
    generatedEmailBody.value = newBody

    const assistantContent = `Objet : ${newSubject}\n\n${newBody}`
    chatHistory.value = [
      ...messagesWithNew,
      { role: 'assistant', content: assistantContent }
    ]
    chatInput.value = ''
  } catch (err) {
    console.error('Error adjusting email:', err)
    emailError.value = err.response?.data?.detail || "Erreur lors de l'ajustement."
    toast.error(emailError.value)
  } finally {
    isAdjusting.value = false
  }
}

const resetChat = () => {
  chatHistory.value = originalEmail.value.body
    ? [{ role: 'assistant', content: `Objet : ${originalEmail.value.subject}\n\n${originalEmail.value.body}` }]
    : []
  generatedEmailSubject.value = originalEmail.value.subject
  generatedEmailBody.value = originalEmail.value.body
  chatInput.value = ''
}

const copyGeneratedEmail = async () => {
  const fullEmail = `Objet : ${generatedEmailSubject.value}\n\n${generatedEmailBody.value}`
  try {
    await navigator.clipboard.writeText(fullEmail)
    emailCopied.value = true
    setTimeout(() => { emailCopied.value = false }, 2000)
    toast.success("Email copié dans le presse-papiers !")
  } catch (err) {
    console.error('Failed to copy', err)
    toast.error("Erreur lors de la copie")
  }
}

// --- Computed styling for score ---
const isHigh = computed(() => {
  const s = result.value?.score || 0;
  const n = (result.value?.niveau || '').toLowerCase();
  return s >= 70 || n.includes('élevé') || n.includes('fort') || n.includes('bon');
})
const isMedium = computed(() => {
  const s = result.value?.score || 0;
  const n = (result.value?.niveau || '').toLowerCase();
  return (s >= 40 && !isHigh.value) || n.includes('moyen');
})

const scoreColorBg = computed(() => {
  if (isHigh.value) return 'bg-emerald-50'
  if (isMedium.value) return 'bg-orange-50'
  return 'bg-rose-50'
})

const scoreColorStroke = computed(() => {
  if (isHigh.value) return 'stroke-emerald-500'
  if (isMedium.value) return 'stroke-orange-500'
  return 'stroke-rose-500'
})

const scoreColorText = computed(() => {
  if (isHigh.value) return 'text-emerald-600'
  if (isMedium.value) return 'text-orange-600'
  return 'text-rose-600'
})

const parsedBesoins = computed(() => {
  if (!result.value) return [];
  let rawBesoins = result.value.besoins_potentiels || result.value.mapping_besoins || [];
  
  if (typeof rawBesoins === 'string') {
    try {
      rawBesoins = JSON.parse(rawBesoins);
    } catch (e) {
      console.error("Erreur de parsing des besoins potentiels:", e);
      return [];
    }
  }
  
  if (Array.isArray(rawBesoins)) {
    return rawBesoins;
  }
  return [];
});

const getServiceColor = (service) => {
  const s = (service || '').toLowerCase();
  if (s.includes('cyber')) return 'bg-red-50 text-red-700 border-red-200';
  if (s.includes('infra') || s.includes('réseau')) return 'bg-blue-50 text-blue-700 border-blue-200';
  if (s.includes('industriel') || s.includes('embarqué')) return 'bg-orange-50 text-orange-700 border-orange-200';
  if (s.includes('conseil') || s.includes('intégration')) return 'bg-purple-50 text-purple-700 border-purple-200';
  if (s.includes('développement') || s.includes('web') || s.includes('mobile')) return 'bg-emerald-50 text-emerald-700 border-emerald-200';
  return 'bg-gray-50 text-gray-700 border-gray-200';
}

</script>

<style scoped>
.shadow-card {
  box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(48,62,140,0.06);
}
</style>
