<template>
  <div class="flex min-h-screen bg-tacir-lightgray/30">
    <TheSidebar />

    <div class="flex-1 flex flex-col min-w-0">
      <!-- Header -->
      <header class="h-16 border-b border-border bg-white sticky top-0 z-40 px-6 flex items-center justify-between shadow-sm">
        <div class="flex items-center gap-3">
          <div class="md:hidden w-10" />
          <div>
            <h2 class="text-sm font-semibold text-tacir-darkblue">Mon Profil</h2>
            <p class="text-[11px] text-tacir-darkgray">Paramètres personnels</p>
          </div>
        </div>

        <div class="flex items-center gap-3">
          <span class="inline-flex items-center gap-1.5 bg-tacir-green/8 text-tacir-green border border-tacir-green/15 text-[10px] font-semibold uppercase tracking-widest px-3 py-1 rounded-full">
            <span class="w-1.5 h-1.5 rounded-full bg-tacir-green animate-pulse" />
            Compte Actif
          </span>
        </div>
      </header>

      <main class="p-6 space-y-6 overflow-y-auto max-w-5xl mx-auto w-full">
        
        <!-- Profile Header -->
        <div class="flex items-center gap-6 animate-fade-in">
          <div class="relative group">
            <Avatar class="h-20 w-20 border-2 border-white shadow-lg ring-1 ring-border">
              <AvatarFallback class="bg-tacir-blue text-white text-2xl font-bold">
                {{ initials }}
              </AvatarFallback>
            </Avatar>
            <button class="absolute -bottom-0.5 -right-0.5 w-7 h-7 bg-tacir-darkblue rounded-lg flex items-center justify-center shadow-lg hover:bg-tacir-blue transition-all text-white border-2 border-white">
              <Pencil class="w-3.5 h-3.5" />
            </button>
          </div>

          <div class="flex-1">
            <h2 class="text-xl font-bold text-tacir-darkblue tracking-tight">{{ name }}</h2>
            <p class="text-tacir-darkgray font-semibold uppercase text-[10px] tracking-wider mt-0.5">{{ role }} · {{ company }}</p>
          </div>

          <Button 
            variant="ghost" 
            @click="handleLogout"
            class="text-red-500 hover:bg-red-50 hover:text-red-600 font-bold gap-2 rounded-xl text-xs h-9"
          >
            <LogOut class="w-3.5 h-3.5" /> Déconnexion
          </Button>
        </div>

        <!-- Tabs Navigation -->
        <div class="flex items-center gap-1.5 p-1 bg-white border border-border rounded-xl w-fit shadow-sm">
          <button
            v-for="tab in tabs"
            :key="tab.value"
            @click="activeTab = tab.value"
            :class="[
              'flex items-center gap-2 px-4 h-9 rounded-lg text-xs font-bold transition-all duration-200',
              activeTab === tab.value
                ? 'bg-tacir-darkblue text-white shadow-md'
                : 'text-tacir-darkgray hover:text-tacir-darkblue hover:bg-tacir-lightgray/50'
            ]"
          >
            <component :is="tab.icon" class="w-3.5 h-3.5" />
            {{ tab.label }}
          </button>
        </div>

        <!-- Content Area -->
        <div class="animate-fade-in">
          <!-- Success Feedback -->
          <div v-if="savedFeedback" class="mb-5 p-3 rounded-xl bg-tacir-green/10 border border-tacir-green/20 flex gap-2.5 items-center">
            <CheckCircle2 class="w-4 h-4 text-tacir-green" />
            <p class="text-xs font-bold text-tacir-green uppercase tracking-wider">{{ savedFeedback }}</p>
          </div>

          <!-- Error Feedback -->
          <div v-if="errorMessage" class="mb-5 p-3 rounded-xl bg-red-500/10 border border-red-500/20 flex gap-2.5 items-center">
            <Shield class="w-4 h-4 text-red-500" />
            <p class="text-xs font-bold text-red-500 uppercase tracking-wider">{{ errorMessage }}</p>
          </div>

          <!-- TAB: Informations -->
          <div v-if="activeTab === 'info'" class="space-y-5">
            <Card class="border-border shadow-sm rounded-2xl overflow-hidden bg-white">
              <div class="h-1 w-full bg-tacir-lightblue"></div>
              <CardContent class="p-6">
                <div class="flex items-center justify-between mb-6">
                  <div>
                    <h3 class="text-lg font-bold text-tacir-darkblue">Informations personnelles</h3>
                    <p class="text-xs text-tacir-darkgray font-medium mt-0.5">Mettez à jour vos coordonnées professionnelles</p>
                  </div>
                  <Button 
                    v-if="!editingInfo" 
                    @click="editingInfo = true"
                    variant="outline"
                    class="rounded-lg font-bold border-border hover:bg-tacir-lightgray text-tacir-darkblue gap-2 h-9 text-xs"
                  >
                    <Edit3 class="w-3.5 h-3.5" /> Modifier
                  </Button>
                  <div v-else class="flex gap-2">
                    <Button @click="editingInfo = false" variant="ghost" class="rounded-lg font-bold text-tacir-darkgray h-9 text-xs">Annuler</Button>
                    <Button @click="handleSaveInfo" class="bg-tacir-darkblue hover:bg-tacir-blue text-white rounded-lg font-bold px-4 gap-2 h-9 text-xs">
                      <Save class="w-3.5 h-3.5" /> Enregistrer
                    </Button>
                  </div>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div class="space-y-1.5">
                    <Label class="text-[9px] font-bold text-tacir-darkblue ml-1 uppercase tracking-tight opacity-70">Nom complet</Label>
                    <div class="relative group">
                      <User class="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-tacir-darkgray group-focus-within:text-tacir-blue transition-colors" />
                      <Input v-model="name" :disabled="!editingInfo" class="pl-9 rounded-lg bg-tacir-lightgray/30 border-transparent focus:border-tacir-blue/30 focus:ring-4 focus:ring-tacir-blue/5 h-10 text-xs font-semibold text-tacir-darkblue disabled:opacity-60" />
                    </div>
                  </div>
                  <div class="space-y-1.5">
                    <Label class="text-[9px] font-bold text-tacir-darkblue ml-1 uppercase tracking-tight opacity-70">Email professionnel</Label>
                    <div class="relative group">
                      <Mail class="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-tacir-darkgray group-focus-within:text-tacir-blue transition-colors" />
                      <Input v-model="email" :disabled="!editingInfo" class="pl-9 rounded-lg bg-tacir-lightgray/30 border-transparent focus:border-tacir-blue/30 focus:ring-4 focus:ring-tacir-blue/5 h-10 text-xs font-semibold text-tacir-darkblue disabled:opacity-60" />
                    </div>
                  </div>
                  <div class="space-y-1.5">
                    <Label class="text-[9px] font-bold text-tacir-darkblue ml-1 uppercase tracking-tight opacity-70">Entreprise</Label>
                    <div class="relative group">
                      <Building2 class="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-tacir-darkgray group-focus-within:text-tacir-blue transition-colors" />
                      <Input v-model="company" :disabled="!editingInfo" class="pl-9 rounded-lg bg-tacir-lightgray/30 border-transparent focus:border-tacir-blue/30 focus:ring-4 focus:ring-tacir-blue/5 h-10 text-xs font-semibold text-tacir-darkblue disabled:opacity-60" />
                    </div>
                  </div>
                  <div class="space-y-1.5">
                    <Label class="text-[9px] font-bold text-tacir-darkblue ml-1 uppercase tracking-tight opacity-70">Fonction</Label>
                    <div class="relative group">
                      <Shield class="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-tacir-darkgray group-focus-within:text-tacir-blue transition-colors" />
                      <Input v-model="fonction" :disabled="!editingInfo" class="pl-9 rounded-lg bg-tacir-lightgray/30 border-transparent focus:border-tacir-blue/30 focus:ring-4 focus:ring-tacir-blue/5 h-10 text-xs font-semibold text-tacir-darkblue disabled:opacity-60" />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <!-- TAB: Sécurité -->
          <div v-else-if="activeTab === 'security'" class="space-y-5">
            <Card class="border-border shadow-sm rounded-2xl overflow-hidden bg-white">
              <div class="h-1 w-full bg-tacir-blue"></div>
              <CardContent class="p-6">
                <div class="mb-6">
                  <h3 class="text-lg font-bold text-tacir-darkblue">Changer le mot de passe</h3>
                  <p class="text-xs text-tacir-darkgray font-medium mt-0.5">Utilisez un mot de passe robuste pour protéger votre accès</p>
                </div>

                <form @submit.prevent="handleSavePw" class="space-y-5 max-w-lg">
                  <div class="space-y-1.5">
                    <Label class="text-[9px] font-bold text-tacir-darkblue ml-1 uppercase tracking-tight opacity-70">Mot de passe actuel</Label>
                    <div class="relative group">
                      <Lock class="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-tacir-darkgray group-focus-within:text-tacir-blue transition-colors" />
                      <Input 
                        v-model="currentPw" 
                        :type="showCurrent ? 'text' : 'password'" 
                        class="pl-9 pr-9 rounded-lg bg-tacir-lightgray/30 border-transparent focus:border-tacir-blue/30 focus:ring-4 focus:ring-tacir-blue/5 h-10 text-xs font-semibold" 
                      />
                      <button type="button" @click="showCurrent = !showCurrent" class="absolute right-3 top-1/2 -translate-y-1/2 text-tacir-darkgray hover:text-tacir-blue transition-colors">
                        <EyeOff v-if="showCurrent" class="w-3.5 h-3.5" /><Eye v-else class="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>

                  <div class="space-y-1.5">
                    <Label class="text-[9px] font-bold text-tacir-darkblue ml-1 uppercase tracking-tight opacity-70">Nouveau mot de passe</Label>
                    <div class="relative group">
                      <Lock class="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-tacir-darkgray group-focus-within:text-tacir-blue transition-colors" />
                      <Input 
                        v-model="newPw" 
                        :type="showNew ? 'text' : 'password'" 
                        class="pl-9 pr-9 rounded-lg bg-tacir-lightgray/30 border-transparent focus:border-tacir-blue/30 focus:ring-4 focus:ring-tacir-blue/5 h-10 text-xs font-semibold" 
                      />
                      <button type="button" @click="showNew = !showNew" class="absolute right-3 top-1/2 -translate-y-1/2 text-tacir-darkgray hover:text-tacir-blue transition-colors">
                        <EyeOff v-if="showNew" class="w-3.5 h-3.5" /><Eye v-else class="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>

                  <div class="space-y-1.5">
                    <Label class="text-[9px] font-bold text-tacir-darkblue ml-1 uppercase tracking-tight opacity-70">Confirmer le nouveau mot de passe</Label>
                    <div class="relative group">
                      <Lock class="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-tacir-darkgray group-focus-within:text-tacir-blue transition-colors" />
                      <Input 
                        v-model="confirmPw" 
                        :type="showConfirm ? 'text' : 'password'" 
                        class="pl-9 pr-9 rounded-lg bg-tacir-lightgray/30 border-transparent focus:border-tacir-blue/30 focus:ring-4 focus:ring-tacir-blue/5 h-10 text-xs font-semibold" 
                        :class="{ 'border-red-400 bg-red-50': confirmPw && confirmPw !== newPw }"
                      />
                      <button type="button" @click="showConfirm = !showConfirm" class="absolute right-3 top-1/2 -translate-y-1/2 text-tacir-darkgray hover:text-tacir-blue transition-colors">
                        <EyeOff v-if="showConfirm" class="w-3.5 h-3.5" /><Eye v-else class="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>

                  <Button 
                    type="submit" 
                    :disabled="!currentPw || !newPw || newPw !== confirmPw"
                    class="w-full h-10 bg-tacir-darkblue hover:bg-tacir-blue text-white rounded-lg font-bold shadow-md transition-all active:scale-95 mt-2 text-xs"
                  >
                    Mettre à jour le mot de passe
                  </Button>
                </form>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { 
  User, Mail, Building2, Shield, Pencil, Save, 
  Lock, Eye, EyeOff, CheckCircle2, LogOut, Edit3
} from 'lucide-vue-next'
import TheSidebar from '@/components/AppSidebar.vue'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { useAuth } from '@/composables/useAuth'

const router = useRouter()
const { logout, user, updateProfile, changePassword } = useAuth()

// ── Profile Data ──
const name    = ref('')
const email   = ref('')
const company = ref('')
const role    = ref('')
const fonction = ref('')
const editingInfo = ref(false)
const savedFeedback = ref('')
const errorMessage = ref('')

onMounted(() => {
  if (user.value) {
    name.value = user.value.full_name || ''
    email.value = user.value.email || ''
    role.value = user.value.role || ''
    company.value = user.value.entreprise || 'Numeryx'
    fonction.value = user.value.fonction || ''
  }
})

const initials = computed(() =>
  name.value ? name.value.split(' ').map(n => n[0]).join('').toUpperCase() : 'U'
)

async function handleSaveInfo() {
  errorMessage.value = ''
  // Split name into first_name and last_name (simple split)
  const names = name.value.trim().split(' ')
  const prenom = names[0] || ''
  const nom = names.slice(1).join(' ') || ''

  const result = await updateProfile({
    prenom,
    nom,
    entreprise: company.value,
    fonction: fonction.value
  })

  if (result.success) {
    editingInfo.value = false
    savedFeedback.value = 'Profil mis à jour avec succès'
    setTimeout(() => { savedFeedback.value = '' }, 3000)
  } else {
    errorMessage.value = result.message
  }
}

// ── Security Data ──
const currentPw   = ref('')
const newPw       = ref('')
const confirmPw   = ref('')
const showCurrent = ref(false)
const showNew     = ref(false)
const showConfirm = ref(false)

async function handleSavePw() {
  errorMessage.value = ''
  const result = await changePassword({
    currentPw: currentPw.value,
    newPw: newPw.value,
    confirmPw: confirmPw.value
  })

  if (result.success) {
    savedFeedback.value = 'Mot de passe mis à jour'
    currentPw.value = ''
    newPw.value = ''
    confirmPw.value = ''
    setTimeout(() => { savedFeedback.value = '' }, 3000)
  } else {
    errorMessage.value = result.message
  }
}

async function handleLogout() {
  await logout()
  router.push('/login')
}

// ── Tabs ──
type TabValue = 'info' | 'security'
const activeTab = ref<TabValue>('info')

const tabs = [
  { value: 'info' as TabValue,     label: 'Informations', icon: User  },
  { value: 'security' as TabValue, label: 'Sécurité',     icon: Lock  },
]
</script>
