<template>
  <div class="flex min-h-screen bg-tacir-lightgray/30">
    <TheSidebar />

    <div class="flex-1 flex flex-col min-w-0">
      <header class="h-16 border-b border-border bg-white sticky top-0 z-40 px-6 flex items-center justify-between shadow-sm">
        <div class="flex items-center gap-3">
          <div class="md:hidden w-10" />
          <div>
            <h2 class="text-sm font-semibold text-tacir-darkblue">Logs d'audit</h2>
            <p class="text-[11px] text-tacir-darkgray">Sécurité système</p>
          </div>
        </div>

        <div class="flex items-center gap-3">
          <span class="hidden sm:inline-flex items-center gap-1.5 bg-tacir-blue/8 text-tacir-blue border border-tacir-blue/15 text-[10px] font-semibold uppercase tracking-widest px-3 py-1 rounded-full">
            <span class="w-1.5 h-1.5 rounded-full bg-tacir-lightblue animate-pulse" />
            ADMIN
          </span>
        </div>
      </header>

      <main class="p-4 md:p-8 space-y-6 overflow-y-auto">
        <!-- Filters -->
        <Card class="border-border shadow-sm rounded-2xl overflow-hidden bg-white">
          <CardContent class="p-4 md:p-6 flex flex-col md:flex-row items-stretch md:items-end gap-4">
            <div class="space-y-1.5 flex-1">
              <Label class="text-[10px] font-bold text-tacir-darkgray uppercase tracking-widest ml-1">Cible</Label>
              <div class="relative group">
                <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-tacir-darkgray group-focus-within:text-tacir-blue transition-colors" />
                <Input v-model="filters.target" placeholder="Email de la cible..." class="pl-10 rounded-xl bg-tacir-lightgray/30 border-transparent focus:border-tacir-blue/30 focus:ring-0 transition-all h-10 text-xs" />
              </div>
            </div>

            <div class="space-y-1.5 w-full md:w-48">
              <Label class="text-[10px] font-bold text-tacir-darkgray uppercase tracking-widest ml-1">Action</Label>
              <Select v-model="filters.action">
                <SelectTrigger class="rounded-xl bg-tacir-lightgray/30 border-transparent focus:ring-0 h-10 text-xs">
                  <SelectValue placeholder="Toutes les actions" />
                </SelectTrigger>
                <SelectContent class="rounded-xl border-border">
                  <SelectItem value="ALL">Toutes</SelectItem>
                  <SelectItem value="CREATE">Création</SelectItem>
                  <SelectItem value="UPDATE">Modification</SelectItem>
                  <SelectItem value="DELETE">Suppression</SelectItem>
                  <SelectItem value="LOGIN">Connexion</SelectItem>
                  <SelectItem value="LOGOUT">Déconnexion</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Button @click="fetchLogs" variant="ghost" class="h-10 px-4 rounded-xl hover:bg-tacir-lightgray text-tacir-darkblue font-bold gap-2 border border-border/50 text-xs">
              <RefreshCw class="w-3.5 h-3.5" :class="{ 'animate-spin': loading }" /> <span class="hidden sm:inline">Actualiser</span>
            </Button>
          </CardContent>
        </Card>

        <!-- Logs Table -->
        <Card class="border-border shadow-md rounded-2xl bg-white overflow-hidden overflow-x-auto">
          <div class="min-w-[900px]">
            <Table>
              <TableHeader class="bg-tacir-lightgray/10">
                <TableRow class="hover:bg-transparent border-border">
                  <TableHead class="font-bold text-tacir-darkblue py-3 px-6 text-[10px] uppercase tracking-wider">Date & Heure</TableHead>
                  <TableHead class="font-bold text-tacir-darkblue py-3 text-[10px] uppercase tracking-wider">Utilisateur</TableHead>
                  <TableHead class="font-bold text-tacir-darkblue py-3 text-[10px] uppercase tracking-wider">Action</TableHead>
                  <TableHead class="font-bold text-tacir-darkblue py-3 text-[10px] uppercase tracking-wider">Cible</TableHead>
                  <TableHead class="font-bold text-tacir-darkblue py-3 text-[10px] uppercase tracking-wider">IP Adresse</TableHead>
                  <TableHead class="text-right font-bold text-tacir-darkblue py-3 px-6 text-[10px] uppercase tracking-wider">Détails</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow v-if="loading && logs.length === 0" v-for="i in 8" :key="i">
                  <TableCell class="py-3 px-6"><Skeleton class="h-5 w-32" /></TableCell>
                  <TableCell class="py-3"><Skeleton class="h-5 w-40" /></TableCell>
                  <TableCell class="py-3"><Skeleton class="h-5 w-20" /></TableCell>
                  <TableCell class="py-3"><Skeleton class="h-5 w-40" /></TableCell>
                  <TableCell class="py-3"><Skeleton class="h-5 w-24" /></TableCell>
                  <TableCell class="px-6 py-3"><Skeleton class="h-5 w-6 ml-auto" /></TableCell>
                </TableRow>

                <TableRow v-else-if="logs.length === 0" class="h-48">
                  <TableCell colspan="6" class="text-center">
                    <div class="flex flex-col items-center gap-3 text-tacir-darkgray">
                      <ShieldCheck class="w-10 h-10 opacity-20" />
                      <p class="text-sm font-medium">Aucun log d'audit trouvé.</p>
                    </div>
                  </TableCell>
                </TableRow>

                <TableRow v-for="log in paginatedLogs" :key="log.id" class="hover:bg-tacir-lightgray/10 transition-colors border-border group h-14">
                  <TableCell class="py-2 px-6 text-[10px] font-medium text-tacir-darkgray">
                    {{ formatDateTime(log.timestamp) }}
                  </TableCell>
                  <TableCell class="py-2">
                    <div class="flex flex-col">
                      <span class="font-bold text-tacir-darkblue text-xs">{{ log.full_name }}</span>
                      <span class="text-[9px] text-tacir-darkgray uppercase font-black">{{ log.user_email }}</span>
                    </div>
                  </TableCell>
                  <TableCell class="py-2">
                    <Badge :class="getActionClass(log.action)" class="rounded-lg font-black uppercase text-[9px] tracking-widest px-2 py-0">
                      {{ log.action }}
                    </Badge>
                  </TableCell>
                  <TableCell class="py-2 text-[10px] font-bold text-tacir-darkblue">
                    {{ log.target }}
                  </TableCell>
                  <TableCell class="py-2">
                    <span class="text-[9px] font-mono text-tacir-darkgray bg-tacir-lightgray/50 px-1.5 py-0.5 rounded">
                      {{ log.ip_address || '—' }}
                    </span>
                  </TableCell>
                  <TableCell class="text-right px-6 py-2">
                    <Dialog>
                      <DialogTrigger as-child>
                        <Button variant="ghost" size="icon" class="h-8 w-8 rounded-lg hover:bg-tacir-blue/10 hover:text-tacir-blue">
                          <Info class="w-3.5 h-3.5" />
                        </Button>
                      </DialogTrigger>
                      <DialogContent class="sm:max-w-[600px] rounded-3xl p-0 overflow-hidden border-none shadow-2xl bg-white">
                        <div class="h-1.5 w-full bg-tacir-darkblue"></div>
                        <DialogHeader class="px-8 pt-8 pb-4">
                          <DialogTitle class="text-xl font-black text-tacir-darkblue">Détails de l'action</DialogTitle>
                          <DialogDescription class="text-xs font-medium">
                            Informations complètes sur l'événement enregistré.
                          </DialogDescription>
                        </DialogHeader>
                        <div class="px-8 pb-8">
                          <div class="bg-tacir-lightgray/30 rounded-2xl p-6 border border-border/50">
                            <pre class="text-[11px] font-mono text-tacir-darkblue whitespace-pre-wrap break-all leading-relaxed">{{ JSON.stringify(log.details, null, 2) }}</pre>
                          </div>
                        </div>
                      </DialogContent>
                    </Dialog>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </div>

          <!-- Pagination Footer -->
          <div class="px-4 md:px-6 py-3 border-t border-border flex flex-col sm:flex-row items-center justify-between bg-white gap-4">
            <div class="flex items-center gap-6">
              <div class="text-[11px] font-bold text-tacir-darkgray uppercase tracking-widest">
                {{ paginationInfo }}
              </div>

              <div class="flex items-center gap-2">
                <span class="text-[10px] font-bold text-tacir-darkgray uppercase tracking-tighter">Afficher</span>
                <Select v-model="pageSize" @update:modelValue="currentPage = 1">
                  <SelectTrigger class="h-7 w-[65px] rounded-lg border-border bg-transparent text-[10px] font-black focus:ring-0">
                    <SelectValue :placeholder="pageSize.toString()" />
                  </SelectTrigger>
                  <SelectContent class="rounded-xl border-border min-w-[65px]">
                    <SelectItem v-for="size in [5, 10, 20, 50]" :key="size" :value="size.toString()" class="text-[10px] font-bold">
                      {{ size }}
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div class="flex items-center gap-2">
              <Button 
                variant="outline" 
                size="icon" 
                @click="prevPage" 
                :disabled="currentPage === 1"
                class="h-8 w-8 rounded-lg border-border hover:bg-tacir-lightgray disabled:opacity-50"
              >
                <ChevronLeft class="w-4 h-4" />
              </Button>
              <div class="text-xs font-black text-tacir-darkblue px-2">
                Page {{ currentPage }} sur {{ totalPages || 1 }}
              </div>
              <Button 
                variant="outline" 
                size="icon" 
                @click="nextPage" 
                :disabled="currentPage === totalPages || totalPages === 0"
                class="h-8 w-8 rounded-lg border-border hover:bg-tacir-lightgray disabled:opacity-50"
              >
                <ChevronRight class="w-4 h-4" />
              </Button>
            </div>
          </div>
        </Card>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, computed } from 'vue'
import { 
  Search, RefreshCw, ShieldCheck, Info, Activity,
  Zap, FileText, LayoutDashboard, Target, BarChart3, CheckCircle2,
  ChevronLeft, ChevronRight
} from 'lucide-vue-next'
import TheSidebar from '@/components/AppSidebar.vue'
import api from '@/api/axios'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import {
  Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger,
} from '@/components/ui/dialog'

const logs = ref([])
const loading = ref(false)
const filters = reactive({
  target: '',
  action: 'ALL'
})

// Pagination
const currentPage = ref(1)
const pageSize = ref('10')
const totalLogs = computed(() => logs.value.length)
const totalPages = computed(() => Math.ceil(totalLogs.value / parseInt(pageSize.value)))

const paginatedLogs = computed(() => {
  const size = parseInt(pageSize.value)
  const start = (currentPage.value - 1) * size
  const end = start + size
  return logs.value.slice(start, end)
})

const paginationInfo = computed(() => {
  const size = parseInt(pageSize.value)
  if (totalLogs.value === 0) return '0-0 sur 0'
  const start = (currentPage.value - 1) * size + 1
  const end = Math.min(currentPage.value * size, totalLogs.value)
  return `${start}-${end} sur ${totalLogs.value}`
})

function nextPage() {
  if (currentPage.value < totalPages.value) currentPage.value++
}

function prevPage() {
  if (currentPage.value > 1) currentPage.value--
}

async function fetchLogs() {
  loading.value = true
  try {
    const params = {}
    if (filters.target) params.target = filters.target
    if (filters.action !== 'ALL') params.action = filters.action
    
    const response = await api.get('/audit/', { params })
    logs.value = response.data
  } catch (error) {
    console.error('Fetch logs error:', error)
  } finally {
    loading.value = false
  }
}

function getActionClass(action) {
  switch (action) {
    case 'CREATE': return 'bg-tacir-green/10 text-tacir-green border-tacir-green/20'
    case 'UPDATE': return 'bg-tacir-yellow/10 text-tacir-yellow border-tacir-yellow/20'
    case 'DELETE': return 'bg-tacir-pink/10 text-tacir-pink border-tacir-pink/20'
    case 'LOGIN': return 'bg-tacir-lightblue/10 text-tacir-lightblue border-tacir-lightblue/20'
    case 'LOGOUT': return 'bg-tacir-darkgray/10 text-tacir-darkgray border-tacir-darkgray/20'
    default: return 'bg-slate-100 text-slate-600 border-slate-200'
  }
}

function formatDateTime(dateStr) {
  return new Date(dateStr).toLocaleString('fr-FR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  })
}

watch(filters, () => fetchLogs())

onMounted(fetchLogs)
</script>
