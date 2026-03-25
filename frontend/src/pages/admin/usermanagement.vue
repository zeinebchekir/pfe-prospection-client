<template>
  <div class="flex min-h-screen bg-tacir-lightgray/30">
    <TheSidebar />

    <div class="flex-1 flex flex-col min-w-0">
      <header class="h-16 border-b border-border bg-white sticky top-0 z-40 px-6 flex items-center justify-between shadow-sm">
        <div class="flex items-center gap-3">
          <div class="md:hidden w-10" />
          <div>
            <h2 class="text-sm font-semibold text-tacir-darkblue">Gestion des Utilisateurs</h2>
            <p class="text-[11px] text-tacir-darkgray">Administration équipe</p>
          </div>
        </div>

        <div class="flex items-center gap-4">
          <Button @click="openCreateModal" class="h-9 px-4 bg-tacir-blue hover:bg-tacir-darkblue text-white rounded-lg gap-2 shadow-sm transition-all active:scale-95 text-xs font-bold">
            <Plus class="w-3.5 h-3.5" /> Ajouter un membre
          </Button>
        </div>
      </header>

      <main class="p-4 md:p-8 space-y-6 overflow-y-auto">
        <!-- Filters -->
        <Card class="border-border shadow-sm rounded-2xl overflow-hidden bg-white">
          <CardContent class="p-4 md:p-6 flex flex-col md:flex-row items-stretch md:items-end gap-4">
            <div class="space-y-1.5 flex-1">
              <Label class="text-[10px] font-bold text-tacir-darkgray uppercase tracking-widest ml-1">Recherche</Label>
              <div class="relative group">
                <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-tacir-darkgray group-focus-within:text-tacir-blue transition-colors" />
                <Input v-model="filters.search" placeholder="Nom, email..." class="pl-10 rounded-xl bg-tacir-lightgray/30 border-transparent focus:border-tacir-blue/30 focus:ring-0 transition-all h-10 text-xs" />
              </div>
            </div>

            <div class="flex flex-col sm:flex-row gap-4">
              <div class="space-y-1.5 w-full sm:w-40">
                <Label class="text-[10px] font-bold text-tacir-darkgray uppercase tracking-widest ml-1">Rôle</Label>
                <Select v-model="filters.role">
                  <SelectTrigger class="rounded-xl bg-tacir-lightgray/30 border-transparent focus:ring-0 h-10 text-xs">
                    <SelectValue placeholder="Tous les rôles" />
                  </SelectTrigger>
                  <SelectContent class="rounded-xl border-border">
                    <SelectItem value="ALL">Tous les rôles</SelectItem>
                    <SelectItem value="CEO">CEO</SelectItem>
                    <SelectItem value="COMMERCIAL">Commercial</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div class="space-y-1.5 w-full sm:w-40">
                <Label class="text-[10px] font-bold text-tacir-darkgray uppercase tracking-widest ml-1">Statut</Label>
                <Select v-model="filters.is_active">
                  <SelectTrigger class="rounded-xl bg-tacir-lightgray/30 border-transparent focus:ring-0 h-10 text-xs">
                    <SelectValue placeholder="Tous les statuts" />
                  </SelectTrigger>
                  <SelectContent class="rounded-xl border-border">
                    <SelectItem value="ALL">Tous</SelectItem>
                    <SelectItem value="true">Actifs</SelectItem>
                    <SelectItem value="false">Inactifs</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <Button @click="fetchUsers" variant="ghost" class="h-10 px-4 rounded-xl hover:bg-tacir-lightgray text-tacir-darkblue font-bold gap-2 border border-border/50 text-xs">
              <RefreshCw class="w-3.5 h-3.5" :class="{ 'animate-spin': loading }" /> <span class="hidden sm:inline">Actualiser</span>
            </Button>
          </CardContent>
        </Card>

        <!-- Users Table -->
        <Card class="border-border shadow-md rounded-2xl bg-white overflow-hidden overflow-x-auto">
          <div class="min-w-[800px]">
            <Table>
              <TableHeader class="bg-tacir-lightgray/10">
                <TableRow class="hover:bg-transparent border-border">
                  <TableHead class="w-[300px] font-bold text-tacir-darkblue py-3 px-6 text-[10px] uppercase tracking-wider">Utilisateur</TableHead>
                  <TableHead class="font-bold text-tacir-darkblue py-3 text-[10px] uppercase tracking-wider">Rôle</TableHead>
                  <TableHead class="font-bold text-tacir-darkblue py-3 text-[10px] uppercase tracking-wider">Statut</TableHead>
                  <TableHead class="font-bold text-tacir-darkblue py-3 text-[10px] uppercase tracking-wider">Date création</TableHead>
                  <TableHead class="text-right font-bold text-tacir-darkblue py-3 px-6 text-[10px] uppercase tracking-wider">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow v-if="loading && users.length === 0" v-for="i in 5" :key="i">
                  <TableCell class="py-3 px-6"><Skeleton class="h-8 w-full rounded-lg" /></TableCell>
                  <TableCell class="py-3"><Skeleton class="h-5 w-20 rounded-lg" /></TableCell>
                  <TableCell class="py-3"><Skeleton class="h-5 w-16 rounded-lg" /></TableCell>
                  <TableCell class="py-3"><Skeleton class="h-5 w-24 rounded-lg" /></TableCell>
                  <TableCell class="px-6 py-3"><Skeleton class="h-8 w-8 ml-auto rounded-lg" /></TableCell>
                </TableRow>
                
                <TableRow v-else-if="users.length === 0" class="h-48">
                  <TableCell colspan="5" class="text-center">
                    <div class="flex flex-col items-center gap-3 text-tacir-darkgray">
                      <Users class="w-10 h-10 opacity-20" />
                      <p class="text-sm font-medium">Aucun utilisateur trouvé.</p>
                    </div>
                  </TableCell>
                </TableRow>

                <TableRow v-for="user in paginatedUsers" :key="user.id" class="hover:bg-tacir-lightgray/10 transition-colors border-border group h-14">
                  <TableCell class="py-2 px-6">
                    <div class="flex items-center gap-3">
                      <Avatar class="h-8 w-8 rounded-full gradient-brand flex items-center justify-center">
                        <AvatarFallback class="bg-transparent text-white font-bold text-sm">
                          {{ user.full_name[0] }}
                        </AvatarFallback>
                      </Avatar>
                      <div class="flex flex-col">
                        <span class="font-bold text-tacir-darkblue text-xs group-hover:text-tacir-blue transition-colors">
                          {{ user.full_name }}
                        </span>
                        <span class="text-[9px] text-tacir-darkgray font-medium">{{ user.email }}</span>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell class="py-2">
                    <Badge :variant="user.role === 'CEO' ? 'default' : 'secondary'" class="rounded-lg font-bold text-[9px] tracking-tight px-2 py-0">
                      {{ user.role }}
                    </Badge>
                  </TableCell>
                  <TableCell class="py-2">
                    <div class="flex items-center gap-2">
                      <div class="w-1.5 h-1.5 rounded-full" :class="user.is_active ? 'bg-tacir-green' : 'bg-tacir-darkgray'"></div>
                      <span class="text-[10px] font-bold" :class="user.is_active ? 'text-tacir-green' : 'text-tacir-darkgray'">
                        {{ user.is_active ? 'Actif' : 'Inactif' }}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell class="text-[10px] text-tacir-darkgray font-medium py-2">
                    {{ formatDate(user.date_creation) }}
                  </TableCell>
                  <TableCell class="text-right px-6 py-2">
                    <div class="flex items-center justify-end gap-1 md:opacity-0 md:group-hover:opacity-100 transition-opacity">
                      <Button @click="openEditModal(user)" variant="ghost" size="icon" class="h-8 w-8 rounded-lg hover:bg-tacir-blue/10 hover:text-tacir-blue">
                        <Edit2 class="w-3.5 h-3.5" />
                      </Button>
                      <Button @click="toggleUserActive(user)" variant="ghost" size="icon" class="h-8 w-8 rounded-lg hover:bg-orange-50 hover:text-tacir-yellow">
                        <Power class="w-3.5 h-3.5" />
                      </Button>
                      <Button @click="confirmDelete(user)" variant="ghost" size="icon" class="h-8 w-8 rounded-lg hover:bg-red-50 hover:text-tacir-pink">
                        <Trash2 class="w-3.5 h-3.5" />
                      </Button>
                    </div>
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

    <!-- Create/Edit Modal -->
    <Dialog :open="modal.open" @update:open="modal.open = $event">
      <DialogContent class="sm:max-w-[440px] rounded-[2rem] p-0 overflow-hidden border-none shadow-2xl bg-white">
        <!-- Accent Top Bar -->
        <div class="h-1.5 w-full bg-tacir-darkblue/10">
          <div class="h-full bg-tacir-blue transition-all duration-500" :style="{ width: modal.isEdit ? '100%' : '100%' }"></div>
        </div>
        
        <DialogHeader class="px-8 pt-8 pb-4">
          <div class="flex items-center gap-4 mb-1">
            <div class="w-12 h-12 rounded-2xl flex items-center justify-center text-white shadow-xl transform transition-all duration-500"
                 :class="modal.isEdit ? 'bg-tacir-darkblue rotate-3' : 'bg-tacir-blue -rotate-3'">
              <UserPlus v-if="!modal.isEdit" class="w-6 h-6" />
              <Edit3 v-else class="w-6 h-6" />
            </div>
            <div>
              <DialogTitle class="text-2xl font-black text-tacir-darkblue tracking-tight">
                {{ modal.isEdit ? 'Modifier le membre' : 'Nouveau membre' }}
              </DialogTitle>
              <DialogDescription class="text-xs text-tacir-darkgray font-medium">
                {{ modal.isEdit ? 'Mise à jour des accès et privilèges.' : 'Configuration d\'un nouvel accès équipe.' }}
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <form @submit.prevent="saveUser" class="px-8 pb-8 space-y-6">
          <!-- Error Feedback -->
          <div v-if="modal.error" class="p-3 rounded-xl bg-red-50 border border-red-100 flex gap-3 items-center animate-in fade-in slide-in-from-top-1">
            <div class="w-2 h-2 rounded-full bg-red-500 animate-pulse"></div>
            <p class="text-[11px] font-bold text-red-600 uppercase tracking-wider">{{ modal.error }}</p>
          </div>

          <!-- Section: Identité -->
          <div class="space-y-4">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <div class="w-1.5 h-4 bg-tacir-lightblue rounded-full"></div>
                <h4 class="text-[10px] font-black uppercase tracking-[0.2em] text-tacir-darkblue/60">Informations personnelles</h4>
              </div>
            </div>
            
            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-1.5">
                <Label class="text-[10px] font-bold text-tacir-darkblue ml-1 uppercase tracking-tighter">Prénom</Label>
                <div class="relative group">
                  <User class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-tacir-darkgray group-focus-within:text-tacir-blue transition-colors" />
                  <Input v-model="form.prenom" required placeholder="Jean" class="pl-10 rounded-xl bg-tacir-lightgray/40 border-transparent focus:border-tacir-blue/30 focus:ring-4 focus:ring-tacir-blue/5 h-11 text-sm font-semibold text-tacir-darkblue" />
                </div>
              </div>
              <div class="space-y-1.5">
                <Label class="text-[10px] font-bold text-tacir-darkblue ml-1 uppercase tracking-tighter">Nom</Label>
                <div class="relative group">
                  <User class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-tacir-darkgray group-focus-within:text-tacir-blue transition-colors" />
                  <Input v-model="form.nom" required placeholder="Dupont" class="pl-10 rounded-xl bg-tacir-lightgray/40 border-transparent focus:border-tacir-blue/30 focus:ring-4 focus:ring-tacir-blue/5 h-11 text-sm font-semibold text-tacir-darkblue" />
                </div>
              </div>
            </div>

            <div class="space-y-1.5">
              <Label class="text-[10px] font-bold text-tacir-darkblue ml-1 uppercase tracking-tighter">Adresse Email Professionnelle</Label>
              <div class="relative group">
                <Mail class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-tacir-darkgray group-focus-within:text-tacir-blue transition-colors" />
                <Input v-model="form.email" type="email" required placeholder="jean.dupont@crmpfe.com" class="pl-10 rounded-xl bg-tacir-lightgray/40 border-transparent focus:border-tacir-blue/30 focus:ring-4 focus:ring-tacir-blue/5 h-11 text-sm font-semibold text-tacir-darkblue" />
              </div>
            </div>
          </div>

          <!-- Section: Rôle & Sécurité -->
          <div class="space-y-4">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <div class="w-1.5 h-4 bg-tacir-blue rounded-full"></div>
                <h4 class="text-[10px] font-black uppercase tracking-[0.2em] text-tacir-darkblue/60">Accès & Paramètres</h4>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-1.5">
                <Label class="text-[10px] font-bold text-tacir-darkblue ml-1 uppercase tracking-tighter">Rôle plateforme</Label>
                <Select v-model="form.role">
                  <SelectTrigger class="rounded-xl bg-tacir-lightgray/40 border-transparent focus:ring-4 focus:ring-tacir-blue/5 h-11 text-sm font-bold text-tacir-darkblue">
                    <SelectValue placeholder="Choisir" />
                  </SelectTrigger>
                  <SelectContent class="rounded-2xl border-border shadow-2xl p-1">
                    <SelectItem value="CEO" class="rounded-xl py-2.5">
                      <div class="flex items-center gap-2">
                        <div class="w-2 h-2 rounded-full bg-tacir-darkblue"></div>
                        <span class="font-bold text-xs text-tacir-darkblue">CEO / Manager</span>
                      </div>
                    </SelectItem>
                    <SelectItem value="COMMERCIAL" class="rounded-xl py-2.5">
                      <div class="flex items-center gap-2">
                        <div class="w-2 h-2 rounded-full bg-tacir-lightblue"></div>
                        <span class="font-bold text-xs text-tacir-darkblue">Commercial</span>
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div v-if="!modal.isEdit" class="space-y-1.5">
                <Label class="text-[10px] font-bold text-tacir-darkblue ml-1 uppercase tracking-tighter">Mot de passe</Label>
                <div class="relative group">
                  <Key class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-tacir-darkgray group-focus-within:text-tacir-blue transition-colors" />
                  <Input v-model="form.password" type="password" required placeholder="••••••••" class="pl-10 rounded-xl bg-tacir-lightgray/40 border-transparent focus:border-tacir-blue/30 focus:ring-4 focus:ring-tacir-blue/5 h-11 text-sm font-semibold" />
                </div>
              </div>
              <div v-else class="space-y-1.5">
                <Label class="text-[10px] font-bold text-tacir-darkblue ml-1 uppercase tracking-tighter">Statut du compte</Label>
                <div @click="form.is_active = !form.is_active" 
                     class="h-11 flex items-center justify-between px-4 bg-tacir-lightgray/40 rounded-xl border border-transparent hover:border-tacir-blue/10 cursor-pointer transition-all group/status">
                  <span class="text-[11px] font-black uppercase tracking-tighter transition-colors" :class="form.is_active ? 'text-tacir-lightblue' : 'text-tacir-darkgray'">
                    {{ form.is_active ? 'Actif' : 'Inactif' }}
                  </span>
                  <div class="w-10 h-6 rounded-full p-1 transition-all duration-300 shadow-inner" :class="form.is_active ? 'bg-tacir-lightblue' : 'bg-tacir-darkgray/30'">
                    <div class="w-4 h-4 bg-white rounded-full transition-transform duration-300 transform shadow-sm" :class="form.is_active ? 'translate-x-4' : 'translate-x-0'"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <DialogFooter class="pt-6 flex flex-row gap-4">
            <Button 
              type="button" 
              variant="ghost" 
              @click="modal.open = false" 
              class="flex-1 h-12 rounded-2xl font-bold text-xs text-tacir-darkgray hover:bg-tacir-lightgray hover:text-tacir-darkblue transition-all duration-300"
            >
              Annuler
            </Button>
            <Button 
              type="submit" 
              :disabled="modal.loading" 
              class="flex-[2] h-12 rounded-2xl font-black text-xs text-white shadow-2xl transition-all duration-300 active:scale-[0.98] group overflow-hidden relative"
              :class="modal.isEdit ? 'bg-tacir-darkblue hover:bg-tacir-blue shadow-tacir-darkblue/20' : 'bg-tacir-blue hover:bg-tacir-darkblue shadow-tacir-blue/20'"
            >
              <div class="absolute inset-0 bg-white/10 translate-y-full group-hover:translate-y-0 transition-transform duration-300"></div>
              <div class="relative flex items-center justify-center gap-2">
                <Loader2 v-if="modal.loading" class="w-4 h-4 animate-spin" />
                <Check v-else class="w-4 h-4 transition-transform group-hover:scale-110" />
                <span>{{ modal.isEdit ? 'Enregistrer les modifications' : 'Confirmer la création' }}</span>
              </div>
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, computed } from 'vue'
import { 
  Plus, Search, Users, RefreshCw, Edit2, Trash2, Power, 
  Loader2, Activity, ShieldCheck, Zap, FileText, LayoutDashboard,
  Target, RefreshCw as RefreshIcon, BarChart3, CheckCircle2,
  UserPlus, Edit3, Mail, Key, User, Check, ChevronLeft, ChevronRight
} from 'lucide-vue-next'
import TheSidebar from '@/components/AppSidebar.vue'
import api from '@/api/axios'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog'

const users = ref([])
const loading = ref(false)
const filters = reactive({
  search: '',
  role: 'ALL',
  is_active: 'ALL'
})

// Pagination
const currentPage = ref(1)
const pageSize = ref('10')
const totalUsers = computed(() => users.value.length)
const totalPages = computed(() => Math.ceil(totalUsers.value / parseInt(pageSize.value)))

const paginatedUsers = computed(() => {
  const size = parseInt(pageSize.value)
  const start = (currentPage.value - 1) * size
  const end = start + size
  return users.value.slice(start, end)
})

const paginationInfo = computed(() => {
  const size = parseInt(pageSize.value)
  if (totalUsers.value === 0) return '0-0 sur 0'
  const start = (currentPage.value - 1) * size + 1
  const end = Math.min(currentPage.value * size, totalUsers.value)
  return `${start}-${end} sur ${totalUsers.value}`
})

function nextPage() {
  if (currentPage.value < totalPages.value) currentPage.value++
}

function prevPage() {
  if (currentPage.value > 1) currentPage.value--
}

const modal = reactive({
  open: false,
  isEdit: false,
  loading: false,
  userId: null,
  error: null
})

const form = reactive({
  email: '',
  nom: '',
  prenom: '',
  role: 'COMMERCIAL',
  password: '',
  is_active: true
})

async function fetchUsers() {
  loading.value = true
  try {
    const params = {}
    if (filters.search) params.search = filters.search
    if (filters.role !== 'ALL') params.role = filters.role
    if (filters.is_active !== 'ALL') params.is_active = filters.is_active
    
    const response = await api.get('/auth/admin/users/', { params })
    users.value = response.data
  } catch (error) {
    console.error('Fetch users error:', error)
  } finally {
    loading.value = false
  }
}

function openCreateModal() {
  modal.isEdit = false
  modal.userId = null
  modal.error = null
  modal.open = true
  Object.assign(form, {
    email: '', nom: '', prenom: '', role: 'COMMERCIAL', password: '', is_active: true
  })
}

function openEditModal(user) {
  modal.isEdit = true
  modal.userId = user.id
  modal.error = null
  modal.open = true
  Object.assign(form, {
    email: user.email,
    nom: user.nom,
    prenom: user.prenom,
    role: user.role,
    is_active: user.is_active,
    password: '' 
  })
}

async function saveUser() {
  modal.loading = true
  modal.error = null
  try {
    if (modal.isEdit) {
      const { password, ...updateData } = form
      await api.patch(`/auth/admin/users/${modal.userId}/`, updateData)
    } else {
      await api.post('/auth/admin/users/', form)
    }
    modal.open = false
    fetchUsers()
  } catch (error) {
    console.error('Save user error:', error)
    modal.error = error.response?.data?.message || error.response?.data?.error || 'Une erreur est survenue lors de l\'enregistrement.'
    
    // Si c'est une erreur de validation (objet), on essaie d'extraire le premier message
    if (typeof error.response?.data === 'object') {
      const firstError = Object.values(error.response.data)[0]
      if (Array.isArray(firstError)) modal.error = firstError[0]
      else if (typeof firstError === 'string') modal.error = firstError
    }
  } finally {
    modal.loading = false
  }
}

async function toggleUserActive(user) {
  try {
    await api.patch(`/auth/admin/users/${user.id}/toggle-active/`)
    fetchUsers()
  } catch (error) {
    console.error('Toggle active error:', error)
  }
}

async function confirmDelete(user) {
  if (confirm(`Supprimer définitivement ${user.full_name} ?`)) {
    try {
      await api.delete(`/auth/admin/users/${user.id}/`)
      fetchUsers()
    } catch (error) {
      console.error('Delete user error:', error)
    }
  }
}

function formatDate(dateStr) {
  return new Date(dateStr).toLocaleDateString('fr-FR', {
    day: 'numeric', month: 'long', year: 'numeric'
  })
}

watch(filters, () => fetchUsers())

onMounted(fetchUsers)
</script>

<style scoped>
.gradient-brand {
  background: linear-gradient(135deg, #303e8c, #04adbf);
}
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #e5e7eb;
  border-radius: 10px;
}
</style>
