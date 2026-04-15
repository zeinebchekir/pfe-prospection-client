<template>
  <div class="flex min-h-screen bg-tacir-lightgray/30">
    <TheSidebar />

    <div class="flex-1 flex flex-col min-w-0">
      <!-- ── STICKY HEADER ── -->
      <header class="h-16 border-b border-border bg-white sticky top-0 z-40 px-6 flex items-center justify-between shadow-sm">
        <div class="flex items-center gap-3">
          <div class="md:hidden w-10" />
          <div>
            <h2 class="text-sm font-semibold text-tacir-darkblue">Reports List</h2>
            <p class="text-[11px] text-tacir-darkgray">Consultation et téléchargement des rapports PDF</p>
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
      <main class="p-4 md:p-6 space-y-6 overflow-y-auto">
        <Card class="border-border shadow-sm rounded-2xl bg-white overflow-hidden">
          <CardHeader class="border-b border-border bg-tacir-lightgray/10 px-6 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h3 class="text-sm font-bold text-tacir-darkblue flex items-center gap-2">
                <FileText class="w-4 h-4 text-tacir-blue" />
                Liste des Rapports PDF
              </h3>
              <p class="text-[11px] text-tacir-darkgray mt-1">
                Filtrez par date pour retrouver plus facilement un rapport généré.
              </p>
            </div>
            
            <div class="flex items-center gap-3">
              <div class="flex items-center gap-2">
                <label for="startDate" class="text-xs font-semibold text-tacir-darkgray">Du :</label>
                <Input id="startDate" type="date" v-model="filters.startDate" class="h-8 text-xs border-border/80 w-32" />
              </div>
              <div class="flex items-center gap-2">
                <label for="endDate" class="text-xs font-semibold text-tacir-darkgray">Au :</label>
                <Input id="endDate" type="date" v-model="filters.endDate" class="h-8 text-xs border-border/80 w-32" />
              </div>
              <Button @click="resetFilters" variant="outline" size="sm" class="h-8 border-border/80 px-3 text-xs text-tacir-darkgray hover:text-tacir-darkblue">
                <RotateCcw class="w-3.5 h-3.5 mr-1" />
                Réinitialiser
              </Button>
            </div>
          </CardHeader>
          <CardContent class="p-0">
            <Table>
              <TableHeader class="bg-tacir-lightgray/50 border-b border-border/60">
                <TableRow class="hover:bg-transparent">
                  <TableHead class="h-10 text-[10px] font-bold uppercase tracking-widest text-tacir-darkgray px-6 w-16">ID</TableHead>
                  <TableHead class="h-10 text-[10px] font-bold uppercase tracking-widest text-tacir-darkgray w-1/3">Nom du Rapport</TableHead>
                  <TableHead class="h-10 text-[10px] font-bold uppercase tracking-widest text-tacir-darkgray text-left">Date de Génération</TableHead>
                  <TableHead class="h-10 text-[10px] font-bold uppercase tracking-widest text-tacir-darkgray text-right">Taille</TableHead>
                  <TableHead class="h-10 text-[10px] font-bold uppercase tracking-widest text-tacir-darkgray text-right px-6">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow v-for="(report, index) in reports" :key="index" class="border-b border-border/60 transition-colors hover:bg-tacir-lightgray/20">
                  <TableCell class="py-3 px-6 text-xs text-tacir-darkgray font-medium">#{{ index + 1 }}</TableCell>
                  <TableCell class="py-3 text-xs text-tacir-darkblue font-semibold">{{ report.name }}</TableCell>
                  <TableCell class="py-3 text-xs font-medium text-tacir-darkgray">{{ formatDate(report.date) }}</TableCell>
                  <TableCell class="py-3 text-right text-xs font-mono text-tacir-darkgray">{{ report.size }}</TableCell>
                  <TableCell class="py-3 px-6 text-right space-x-2">
                    <Button variant="outline" size="sm" class="h-7 text-[11px] border-border/60 bg-tacir-lightgray/10 hover:bg-tacir-lightgray/30 text-tacir-darkblue font-semibold" @click="openPdf(report)">
                      <Eye class="w-3.5 h-3.5 mr-1 text-tacir-blue" />
                      Ouvrir
                    </Button>
                    <Button size="sm" class="h-7 text-[11px] bg-tacir-blue text-white hover:bg-tacir-darkblue font-semibold" @click="downloadPdf(report)">
                      <Download class="w-3.5 h-3.5 mr-1" />
                      Télécharger
                    </Button>
                  </TableCell>
                </TableRow>
                <TableRow v-if="isLoading">
                  <TableCell colspan="5" class="py-8 text-center text-tacir-darkgray text-xs">
                    Chargement des rapports...
                  </TableCell>
                </TableRow>
                <TableRow v-else-if="errorMsg">
                  <TableCell colspan="5" class="py-8 text-center text-red-500 text-xs">
                    {{ errorMsg }}
                  </TableCell>
                </TableRow>
                <TableRow v-else-if="reports.length === 0">
                  <TableCell colspan="5" class="py-8 text-center text-tacir-darkgray text-xs">
                    Aucun rapport trouvé pour ces dates.
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import TheSidebar from '@/components/AppSidebar.vue'
import { Card, CardHeader, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Table,
  TableHeader,
  TableRow,
  TableHead,
  TableBody,
  TableCell
} from '@/components/ui/table'
import {
  FileText, RotateCcw, Eye, Download
} from 'lucide-vue-next'

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8001'

const reports = ref([])
const isLoading = ref(true)
const errorMsg = ref(null)

const filters = ref({
  startDate: '',
  endDate: ''
})

const fetchReports = async () => {
  isLoading.value = true
  errorMsg.value = null
  try {
    let url = `${BASE_URL}/api/rapport/pdf/list?limit=100` // Fetch up to 100 for proper listing
    
    if (filters.value.startDate) {
      url += `&start_date=${filters.value.startDate}`
    }
    if (filters.value.endDate) {
      url += `&end_date=${filters.value.endDate}`
    }

    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`Erreur API: ${response.status}`)
    }

    const data = await response.json()
    
    // Map result array to standard structure 
    reports.value = data.map((d) => ({
      name: `Rapport_ETL_Numeryx_${d.report_date}.pdf`,
      date: d.generated_at,
      size: `${d.file_size_kb || 0} KB`,
      report_date: d.report_date
    }))
  } catch (error) {
    errorMsg.value = error.message || "Erreur hors-ligne lors du chargement des rapports"
  } finally {
    isLoading.value = false
  }
}

watch(filters, () => {
  fetchReports()
}, { deep: true })

onMounted(() => {
  fetchReports()
})

const resetFilters = () => {
  filters.value.startDate = ''
  filters.value.endDate = ''
}

const formatDate = (isoStr) => {
  if (!isoStr) return '—'
  return new Date(isoStr).toLocaleString('fr-FR', {
    dateStyle: 'medium',
    timeStyle: 'short'
  })
}

const openPdf = (report) => {
  const url = `${BASE_URL}/api/rapport/pdf/download/${report.report_date}?inline=true`
  window.open(url, '_blank')
}

const downloadPdf = (report) => {
  const url = `${BASE_URL}/api/rapport/pdf/download/${report.report_date}`
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', report.name) 
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}
</script>
