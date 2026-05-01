<template>
  <div class="flex min-h-screen bg-tacir-lightgray/30">
    <TheSidebar />

    <div class="flex-1 flex flex-col min-w-0 h-screen">
      <!-- ── STICKY HEADER ── -->
      <header class="h-16 border-b border-border bg-white sticky top-0 z-40 px-6 flex items-center justify-between shadow-sm shrink-0">
        <div class="flex items-center gap-3">
          <div class="md:hidden w-10" />
          <div>
            <h2 class="text-sm font-semibold text-tacir-darkblue">ETL Logs Viewer</h2>
            <p class="text-[11px] text-tacir-darkgray">Consultation et suivi des logs de la pipeline ETL Airflow</p>
          </div>
        </div>

        <div class="flex items-center gap-3">
          <span class="hidden sm:inline-flex items-center gap-1.5 bg-tacir-blue/8 text-tacir-blue border border-tacir-blue/15 text-[10px] font-semibold uppercase tracking-widest px-3 py-1 rounded-full">
            <span class="w-1.5 h-1.5 rounded-full bg-tacir-lightblue animate-pulse" />
            ADMIN
          </span>
        </div>
      </header>

      <!-- ── MAIN CONTENT ── -->
      <main class="p-4 md:p-6 flex flex-col lg:flex-row gap-6 flex-1 min-h-0 overflow-hidden">
        
        <!-- Left Panel: File List -->
        <Card class="w-full lg:w-80 flex flex-col border-border shadow-sm rounded-2xl bg-white overflow-hidden shrink-0">
          <CardHeader class="border-b border-border bg-tacir-lightgray/10 px-4 py-4 shrink-0">
            <h3 class="text-sm font-bold text-tacir-darkblue flex items-center gap-2">
              <FileText class="w-4 h-4 text-tacir-blue" />
              Fichiers de logs
            </h3>
            
            <div class="mt-4 space-y-2">
              <label for="dateFilter" class="text-xs font-semibold text-tacir-darkgray">Filtrer par date :</label>
              <div class="flex items-center gap-2">
                <Input id="dateFilter" type="date" v-model="filterDate" class="h-8 text-xs border-border/80 flex-1" />
                <Button @click="resetFilter" variant="outline" size="sm" class="h-8 w-8 p-0 border-border/80 text-tacir-darkgray hover:text-tacir-darkblue" title="Réinitialiser">
                  <RotateCcw class="w-3.5 h-3.5" />
                </Button>
              </div>
            </div>
          </CardHeader>
          
          <CardContent class="p-0 overflow-y-auto flex-1 bg-white">
            <div v-if="loadingFiles" class="p-6 text-center text-xs text-tacir-darkgray">
              Chargement des fichiers...
            </div>
            <ul v-else class="divide-y divide-border/40">
              <li v-for="file in filteredFiles" :key="file"
                  @click="selectFile(file)"
                  :class="['p-3 cursor-pointer transition-colors flex items-start gap-3', 
                           selectedFile === file 
                             ? 'bg-tacir-blue/5 border-l-2 border-l-tacir-blue' 
                             : 'border-l-2 border-l-transparent hover:bg-tacir-lightgray/20']">
                <FileText class="w-4 h-4 text-tacir-blue mt-0.5 shrink-0" />
                <div class="flex flex-col min-w-0">
                  <span class="text-xs font-semibold text-tacir-darkblue truncate">{{ file }}</span>
                  <div class="flex items-center gap-2 mt-1.5">
                    <Badge :class="getBadgeClass(file)" variant="secondary" class="text-[9px] px-1.5 py-0 h-4 rounded-md font-medium">
                      {{ getDagLabel(file) }}
                    </Badge>
                    <span class="text-[10px] text-tacir-darkgray">{{ extractDate(file) }}</span>
                  </div>
                </div>
              </li>
              <li v-if="filteredFiles.length === 0" class="p-6 text-center text-xs text-tacir-darkgray">
                Aucun fichier trouvé.
              </li>
            </ul>
          </CardContent>
        </Card>

        <!-- Right Panel: File Content -->
        <Card class="flex-1 flex flex-col border-border shadow-sm rounded-2xl bg-white overflow-hidden min-w-0">
          <CardHeader class="border-b border-border bg-tacir-lightgray/10 px-4 py-3 flex flex-row items-center justify-between shrink-0 min-h-[68px]">
            <div class="flex items-center gap-3 min-w-0 flex-1">
              <h3 v-if="selectedFile" class="text-sm font-bold text-tacir-darkblue truncate">
                {{ selectedFile }}
              </h3>
              <h3 v-else class="text-sm font-bold text-tacir-darkgray">
                Aucun fichier sélectionné
              </h3>
              
              <Badge v-if="selectedFile && content" :class="hasError ? 'bg-red-100 text-red-800 border-red-200' : 'bg-[#E1F5EE] text-[#085041] border-[#085041]/20'" variant="outline" class="text-[10px] px-2 py-0.5 h-5 shrink-0 whitespace-nowrap">
                {{ hasError ? 'Contient des échecs' : 'Tous succès' }}
              </Badge>
            </div>
            
            <div class="flex items-center gap-2 shrink-0 ml-4" v-if="selectedFile">
              <Button variant="outline" size="sm" class="h-7 text-[11px] border-border/60 bg-tacir-lightgray/10 hover:bg-tacir-lightgray/30 text-tacir-darkblue font-semibold" @click="refreshSelected">
                <RefreshCw class="w-3.5 h-3.5 mr-1 text-tacir-blue" :class="{ 'animate-spin': loadingContent }" />
                Actualiser
              </Button>
              <Button size="sm" class="h-7 text-[11px] bg-tacir-blue text-white hover:bg-tacir-darkblue font-semibold" @click="downloadSelected">
                <Download class="w-3.5 h-3.5 mr-1" />
                Télécharger
              </Button>
            </div>
          </CardHeader>

          <CardContent class="p-0 overflow-y-auto flex-1 relative bg-[#FAFAFA]" ref="logContainer">
            <div v-if="!selectedFile" class="absolute inset-0 flex items-center justify-center text-xs text-tacir-darkgray">
              Sélectionnez un fichier pour voir les logs
            </div>
            <div v-else-if="loadingContent" class="absolute inset-0 flex items-center justify-center text-xs text-tacir-darkgray bg-white/50 z-10">
              Chargement du contenu...
            </div>
            <pre v-if="selectedFile" class="p-4 text-[11px] font-mono leading-relaxed whitespace-pre-wrap"><template v-for="(line, i) in colorizedLines" :key="i"><span :class="line.cls">{{ line.text }}</span>{{ '\n' }}</template></pre>
          </CardContent>
        </Card>

      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import axios from 'axios'
import TheSidebar from '@/components/AppSidebar.vue'
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import {
  FileText, RotateCcw, RefreshCw, Download
} from 'lucide-vue-next'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8001'

const files = ref([])
const selectedFile = ref(null)
const content = ref('')
const loadingFiles = ref(false)
const loadingContent = ref(false)
const logContainer = ref(null)

const filterDate = ref('')

const filteredFiles = computed(() => {
  if (!filterDate.value) return files.value
  return files.value.filter(f => f.includes(filterDate.value))
})

const resetFilter = () => {
  filterDate.value = ''
}

async function fetchFiles() {
  loadingFiles.value = true
  try {
    const { data } = await axios.get(`${API}/logs/`)
    files.value = data
  } catch (error) {
    console.error("Erreur lors de la récupération des fichiers", error)
  } finally {
    loadingFiles.value = false
  }
}

async function selectFile(filename) {
  selectedFile.value = filename
  loadingContent.value = true
  try {
    const { data } = await axios.get(`${API}/logs/${filename}`)
    content.value = data
  } catch (error) {
    console.error("Erreur lors de la récupération du fichier", error)
    content.value = "Erreur lors du chargement du contenu du fichier."
  } finally {
    loadingContent.value = false
    await nextTick()
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight
    }
  }
}

async function refreshSelected() {
  if (selectedFile.value) {
    await selectFile(selectedFile.value)
  }
}

function downloadSelected() {
  if (!content.value || !selectedFile.value) return
  
  const blob = new Blob([content.value], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = selectedFile.value
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

function extractDate(filename) {
  const parts = filename.split('__')
  if (parts.length > 1) {
    return parts[1].replace('.txt', '')
  }
  return '—'
}

function getDagLabel(filename) {
  const parts = filename.split('__')
  if (parts.length > 0) {
    return parts[0].replace('sync_', '')
  }
  return 'inconnu'
}

function getBadgeClass(filename) {
  if (filename.includes('boamp')) return 'bg-[#E6F1FB] text-[#0C447C] hover:bg-[#E6F1FB] border-[#0C447C]/20 border'
  if (filename.includes('datagouv')) return 'bg-[#E1F5EE] text-[#085041] hover:bg-[#E1F5EE] border-[#085041]/20 border'
  return 'bg-tacir-lightgray/50 text-tacir-darkgray hover:bg-tacir-lightgray/50 border-border/60 border'
}

const colorizedLines = computed(() => {
  if (!content.value) return []
  return content.value.split('\n').map(text => {
    if (text.includes('✓  SUCCÈS')) return { text, cls: 'text-[#0F6E56]' }
    if (text.includes('✗  ÉCHEC') || text.includes('Exception') || (text.includes('Statut') && text.includes('ÉCHEC'))) return { text, cls: 'text-[#A32D2D] font-medium' }
    if (text.includes('▶  DÉBUT')) return { text, cls: 'text-tacir-darkgray' }
    if (text.includes('Traceback')) return { text, cls: 'text-[#854F0B]' }
    if (text.startsWith('─') || text.startsWith('=')) return { text, cls: 'text-tacir-darkgray/40' }
    if (text.includes('Statut') && text.includes('SUCCÈS')) return { text, cls: 'text-[#0F6E56]' }
    return { text, cls: 'text-tacir-darkblue' }
  })
})

const hasError = computed(() => {
  if (!content.value) return false
  return content.value.includes('✗  ÉCHEC')
})

fetchFiles()
</script>