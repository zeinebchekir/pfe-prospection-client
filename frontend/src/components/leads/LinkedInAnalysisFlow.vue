<template>
  <Dialog :open="isOpen" @update:open="onClose">
    <DialogContent 
      class="max-w-2xl w-full sm:max-w-2xl max-h-[85vh] p-0 flex flex-col overflow-hidden"
      :class="{ '[&>button[type=button]]:hidden': hideCloseButton }"
    >
      <!-- Modal Header -->
      <DialogHeader class="p-6 pb-2 border-b bg-card flex-shrink-0">
        <DialogTitle class="text-xl font-bold flex items-center gap-2">
          {{ modalTitle }}
        </DialogTitle>
        <DialogDescription v-if="currentStep < 4" class="text-sm text-muted-foreground">
          Analyse de la présence de {{ companyName }} sur LinkedIn.
        </DialogDescription>
      </DialogHeader>

      <!-- Modal Body (Scrollable) -->
      <div class="flex-1 overflow-y-auto p-6 relative">
        
        <!-- Header Process Indicator (shown during steps 1-3) -->
        <div v-if="currentStep < 4" class="mb-8 space-y-4">
          <div class="flex items-center justify-between text-sm font-medium text-muted-foreground">
            <span>Analyse en cours...</span>
            <span>{{ Math.round(progressValue) }}%</span>
          </div>
          <Progress :model-value="progressValue" class="transition-all duration-500 ease-out h-2" />
        </div>

        <div class="relative min-h-[300px]">
          <Transition name="fade-slide" mode="out-in">
            
            <!-- ============================================== -->
            <!-- STEP 1: Searching for LinkedIn Profile         -->
            <!-- ============================================== -->
            <div v-if="currentStep === 1" key="step1" class="flex flex-col items-center justify-center space-y-6 pt-6">
              <div class="relative flex items-center justify-center w-24 h-24 rounded-full bg-primary/10 mb-4 animate-pulse">
                <Search class="w-10 h-10 text-primary" />
                <div class="absolute inset-0 border-4 border-primary/20 rounded-full animate-ping"></div>
              </div>
              <div class="text-center space-y-2 max-w-md">
                <h3 class="text-xl font-bold tracking-tight text-foreground">Recherche de la présence LinkedIn...</h3>
                <p class="text-muted-foreground text-sm">
                  Nous scannons le web pour trouver la page LinkedIn officielle de <strong class="text-foreground">{{ companyName }}</strong>.
                </p>
              </div>
              <div class="w-full max-w-sm mt-8 space-y-3 opacity-30 pointer-events-none">
                <Skeleton class="h-12 w-full rounded-md" />
                <Skeleton class="h-12 w-full rounded-md" />
              </div>
            </div>

            <!-- ============================================== -->
            <!-- STEP 2A: Found LinkedIn Profile                -->
            <!-- ============================================== -->
            <div v-else-if="currentStep === 2 && foundUrl" key="step2a" class="flex flex-col items-center justify-center space-y-6 pt-6">
              <Badge variant="outline" class="border-green-500 text-green-700 bg-green-50 px-4 py-1 text-sm font-medium">
                <CheckCircle2 class="w-4 h-4 mr-2" /> Page LinkedIn trouvée
              </Badge>
              <Card class="w-full max-w-sm border-primary/30 shadow-md">
                <CardContent class="p-6 flex items-center gap-4">
                  <div class="p-3 bg-blue-50 text-blue-600 rounded-lg">
                    <Linkedin class="w-6 h-6" />
                  </div>
                  <div class="flex-1 min-w-0">
                    <h4 class="font-semibold text-sm truncate">{{ companyName }}</h4>
                    <p class="text-xs text-muted-foreground truncate">{{ foundUrl }}</p>
                  </div>
                </CardContent>
              </Card>
              <div class="text-center space-y-2 max-w-md pt-4">
                <p class="text-muted-foreground text-sm flex items-center justify-center gap-2">
                  <Loader2 class="w-4 h-4 animate-spin text-primary" />
                  Parfait ! Nous passons à l'extraction des derniers posts...
                </p>
              </div>
            </div>

            <!-- ============================================== -->
            <!-- STEP 2B: Manual Input needed                   -->
            <!-- ============================================== -->
            <div v-else-if="currentStep === 2 && !foundUrl" key="step2b" class="flex flex-col items-center justify-center space-y-6 pt-2">
              <Alert variant="destructive" class="max-w-md bg-amber-50 text-amber-900 border-amber-300">
                <AlertCircle class="w-4 h-4 text-amber-600" />
                <AlertDescription>
                  Page LinkedIn introuvable automatiquement.
                </AlertDescription>
              </Alert>

              <div class="text-center space-y-2 max-w-md">
                <p class="text-muted-foreground text-sm">
                  Nous n'avons pas pu trouver la page LinkedIn pour <strong>{{ companyName }}</strong>. Veuillez entrer l'URL manuellement ou ignorer cette étape.
                </p>
              </div>

              <Card class="w-full max-w-md border-border">
                <CardContent class="p-6 space-y-4">
                  <div class="space-y-2 text-left">
                    <Label for="linkedin-url">URL de l'entreprise LinkedIn</Label>
                    <div class="relative">
                      <Linkedin class="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                      <Input 
                        id="linkedin-url" 
                        v-model="manualUrlInput" 
                        class="pl-9" 
                        placeholder="https://www.linkedin.com/company/..." 
                        @keydown.enter="submitManualUrl"
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            <!-- ============================================== -->
            <!-- STEP 3: Fetching Posts                         -->
            <!-- ============================================== -->
            <div v-else-if="currentStep === 3" key="step3" class="flex flex-col items-center justify-center space-y-8 pt-4">
              <div class="text-center space-y-2 max-w-md">
                <h3 class="text-xl font-bold tracking-tight text-foreground flex items-center justify-center gap-2">
                  Extraction des publications <span class="typing-dots"></span>
                </h3>
                <p class="text-muted-foreground text-sm">
                  Analyse des axes stratégiques et projets actifs...
                </p>
              </div>
              <div class="w-full max-w-lg space-y-4">
                <Card v-for="i in 3" :key="i" class="border-border shadow-sm overflow-hidden relative">
                  <div class="absolute left-0 top-0 bottom-0 w-1 bg-primary/40 animate-pulse"></div>
                  <CardContent class="p-5 flex gap-4">
                    <Skeleton class="w-10 h-10 rounded-full shrink-0" />
                    <div class="space-y-2 flex-1">
                      <Skeleton class="h-4 w-[80%]" />
                      <Skeleton class="h-4 w-full" />
                      <Skeleton class="h-4 w-[60%]" />
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>

            <!-- ============================================== -->
            <!-- STEP 4: Final Results                          -->
            <!-- ============================================== -->
            <div v-else-if="currentStep === 4" key="step4" class="space-y-6">
              <div class="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between p-6 bg-card border rounded-xl shadow-sm">
                <div>
                  <div class="flex items-center gap-3 mb-1">
                    <h2 class="text-2xl font-bold tracking-tight">{{ companyName }}</h2>
                    <Badge class="bg-green-100 text-green-700 border-green-200">
                      <CheckCircle2 class="w-3.5 h-3.5 mr-1" /> Analyse terminée
                    </Badge>
                  </div>
                  <a v-if="foundUrl" :href="foundUrl" target="_blank" class="text-sm text-blue-600 hover:underline flex items-center gap-1">
                    <Linkedin class="w-3.5 h-3.5" /> Voir sur LinkedIn
                  </a>
                </div>
                <Button variant="default" @click="emit('analysisComplete', getAnalysisPayload())">
                  Valider et fermer
                </Button>
              </div>

              <div v-if="finalPosts.length === 0" class="flex flex-col items-center justify-center p-12 text-center border rounded-xl bg-card border-dashed">
                <SearchX class="w-12 h-12 text-muted-foreground mb-4" />
                <h3 class="text-lg font-semibold">Aucune publication disponible</h3>
                <p class="text-sm text-muted-foreground">L'étape a été ignorée ou aucune donnée n'a été trouvée.</p>
              </div>
              <div v-else class="space-y-4">
                <h3 class="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Publications récentes</h3>
                <Card v-for="(post, index) in finalPosts" :key="index" class="border-border overflow-hidden relative">
                  <div class="absolute left-0 top-0 bottom-0 w-1 bg-primary"></div>
                  <CardContent class="p-5">
                    <p class="text-sm text-foreground whitespace-pre-wrap line-clamp-3">{{ post }}</p>
                  </CardContent>
                </Card>
              </div>
            </div>

          </Transition>
        </div>
      </div>

      <!-- Modal Footer (FIX 2: Sticky footer for Step 2B) -->
      <DialogFooter 
        v-if="currentStep === 2 && !foundUrl"
        class="sticky bottom-0 bg-background pt-4 pb-6 px-6 border-t border-border flex flex-row justify-end gap-3 z-10"
      >
        <Button 
          variant="ghost" 
          @click="skipAnalysis"
        >
          Ignorer cette étape &rarr;
        </Button>
        <Button 
          variant="default" 
          :disabled="!isValidLinkedinUrl" 
          @click="submitManualUrl"
          :class="{ 'opacity-50 cursor-not-allowed': !isValidLinkedinUrl }"
        >
          Continuer avec cette URL
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { 
  Search, CheckCircle2, Linkedin, AlertCircle, Loader2, 
  ExternalLink, SearchX
} from 'lucide-vue-next'
import { 
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter 
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import axios from 'axios'

// --- Interfaces & Props ---
interface Props {
  companyName: string
  companyId: string | number
  isOpen: boolean
}

interface AnalysisResult {
  linkedinUrl: string | null
  posts: string[]
  skipped: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'analysisComplete', data: AnalysisResult): void
  (e: 'skip'): void
  (e: 'update:isOpen', value: boolean): void
}>()

// --- State ---
const currentStep = ref<number>(1)
const progressValue = ref<number>(0)
const foundUrl = ref<string | null>(null)
const manualUrlInput = ref<string>('')
const finalPosts = ref<string[]>([])
const isSkipped = ref<boolean>(false)

// --- Computed ---
const modalTitle = computed(() => {
  switch (currentStep.value) {
    case 1: return "🔍 Analyse LinkedIn"
    case 2: return foundUrl.value ? "✅ Page LinkedIn trouvée" : "⚠️ Saisie manuelle requise"
    case 3: return "📥 Récupération des publications..."
    case 4: return "📊 Analyse terminée"
    default: return "Analyse LinkedIn"
  }
})

const hideCloseButton = computed(() => {
  // Visible only on step 4 and step 2B (currentStep 2 and !foundUrl)
  if (currentStep.value === 4) return false
  if (currentStep.value === 2 && !foundUrl.value) return false
  return true
})

const isValidLinkedinUrl = computed(() => {
  const url = manualUrlInput.value.trim().toLowerCase()
  return url.includes('linkedin.com/company/')
})

// --- Control Flow ---
onMounted(() => {
  if (props.isOpen) startAnalysisFlow()
})

const onClose = (value: boolean) => {
  emit('update:isOpen', value)
}

const startAnalysisFlow = () => {
  currentStep.value = 1
  progressValue.value = 0
  
  let simProgress = 0
  const interval = setInterval(() => {
    if (currentStep.value === 1 && simProgress < 60) {
      simProgress += 5
      progressValue.value = simProgress
    } else {
      clearInterval(interval)
    }
  }, 200)

  setTimeout(async () => {
    try {
      const url = await fetchLinkedInUrl(props.companyName)
      clearInterval(interval)
      
      if (url) {
        foundUrl.value = url
        progressValue.value = 75
        currentStep.value = 2
        setTimeout(() => { startFetchingPosts() }, 1500)
      } else {
        foundUrl.value = null
        currentStep.value = 2
      }
    } catch (e) {
      currentStep.value = 2
    }
  }, 500)
}

const submitManualUrl = () => {
  if (!isValidLinkedinUrl.value) return
  foundUrl.value = manualUrlInput.value.trim()
  startFetchingPosts()
}

const skipAnalysis = () => {
  isSkipped.value = true
  progressValue.value = 100
  foundUrl.value = null
  finalPosts.value = []
  currentStep.value = 4
  emit('skip')
}

const startFetchingPosts = () => {
  currentStep.value = 3
  progressValue.value = 75
  
  let simProgress = 75
  const interval = setInterval(() => {
    if (currentStep.value === 3 && simProgress < 95) {
      simProgress += 2
      progressValue.value = simProgress
    } else {
      clearInterval(interval)
    }
  }, 300)

  setTimeout(async () => {
    try {
      if (foundUrl.value) {
        const postsResponse = await fetchLinkedInPosts(foundUrl.value)
        finalPosts.value = postsResponse
      }
    } catch(e) {
      finalPosts.value = []
    } finally {
      clearInterval(interval)
      progressValue.value = 100
      setTimeout(() => { currentStep.value = 4 }, 500)
    }
  }, 500)
}

const getAnalysisPayload = (): AnalysisResult => {
  return {
    linkedinUrl: foundUrl.value,
    posts: finalPosts.value,
    skipped: isSkipped.value
  }
}

// --- API Calls ---
const fetchLinkedInUrl = async (name: string) => {
  try {
    const response = await axios.post('http://localhost:8002/linkedin/url', {
      nom_entreprise: name, pays: "france"
    })
    return response.data.linkedin_url
  } catch (error) {
    return null
  }
}

const fetchLinkedInPosts = async (url: string) => {
  try {
    const response = await axios.post('http://localhost:8002/linkedin/posts', {
      linkedin_url: url, max_posts: 10
    })
    return response.data.posts || []
  } catch (error) {
    return []
  }
}
</script>

<style scoped>
.fade-slide-enter-active, .fade-slide-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: absolute; width: 100%;
}
.fade-slide-enter-from { opacity: 0; transform: translateY(16px); }
.fade-slide-leave-to { opacity: 0; transform: translateY(-16px); }

.typing-dots::after {
  content: ''; animation: typing 1.5s infinite; font-weight: 900; letter-spacing: 2px;
}
@keyframes typing {
  0% { content: ''; } 25% { content: '.'; } 50% { content: '..'; } 75% { content: '...'; } 100% { content: ''; }
}
</style>
