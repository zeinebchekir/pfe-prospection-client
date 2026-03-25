<template>
  <!-- Single root element wrapping both desktop sidebar and mobile sheet -->
  <div>

    <!-- ── DESKTOP SIDEBAR ── -->
    <div class="hidden md:flex flex-col w-64 h-screen sticky top-0 bg-white border-r border-border shadow-sm">

      <!-- Logo -->
      <div data-v-53430c37="" class="px-10 py-4 border-b border-border flex items-center justify-center"><img data-v-53430c37="" src="/src/assets/logo.png" alt="crmPfe Logo" class="h-8 w-auto object-contain"></div>

      <!-- Navigation -->
      <nav class="flex-1 px-3 py-4 overflow-y-auto space-y-5">
        <div v-for="group in navigation" :key="group.title">
          <p class="px-3 mb-1.5 text-[10px] font-semibold text-tacir-darkgray uppercase tracking-widest">
            {{ group.title }}
          </p>
          <div class="space-y-0.5">
            <RouterLink
              v-for="item in group.items"
              :key="item.name"
              :to="item.href"
              class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150"
              :class="[
                item.exact 
                  ? $route.path === item.href 
                  : $route.path.startsWith(item.href)
                    ? 'bg-tacir-blue text-white shadow-sm'
                    : 'text-tacir-darkgray hover:text-tacir-darkblue hover:bg-tacir-lightgray'
              ]"
            >
              <component :is="item.icon" class="h-4 w-4 flex-shrink-0" />
              {{ item.name }}
            </RouterLink>
          </div>
        </div>
      </nav>

      <!-- User profile -->
      <div class="p-3 border-t border-border">
        <DropdownMenu>
          <DropdownMenuTrigger as-child>
            <Button
              variant="ghost"
              class="w-full justify-start gap-3 h-14 px-3 rounded-xl hover:bg-tacir-lightgray transition-all border border-transparent hover:border-border"
            >
              <Avatar class="h-8 w-8 flex-shrink-0">
                <AvatarFallback class="gradient-brand text-white font-bold text-sm">
                  {{ userInitial }}
                </AvatarFallback>
              </Avatar>
              <div class="flex flex-col items-start text-left overflow-hidden flex-1">
                <span class="text-sm font-semibold text-tacir-darkblue truncate w-full">
                  {{ user?.full_name || 'Utilisateur' }}
                </span>
                <span class="text-[10px] text-tacir-lightblue font-medium uppercase tracking-wider">
                  {{ user?.role }}
                </span>
              </div>
              <ChevronUp class="h-4 w-4 text-tacir-darkgray flex-shrink-0" />
            </Button>
          </DropdownMenuTrigger>

          <DropdownMenuContent align="end" side="top" class="w-52 mb-1 rounded-xl border-border bg-white shadow-lg p-1">
            <DropdownMenuLabel class="text-[10px] font-semibold text-tacir-darkgray uppercase tracking-widest px-2 py-1.5">
              Mon compte
            </DropdownMenuLabel>
            <DropdownMenuSeparator class="bg-border my-1" />
            <DropdownMenuItem 
              @click="router.push('/profil')"
              class="rounded-lg gap-2.5 cursor-pointer focus:bg-tacir-lightgray py-2 text-sm text-tacir-darkblue"
            >
              <User class="h-4 w-4 text-tacir-blue" /> Profil
            </DropdownMenuItem>
            <DropdownMenuItem class="rounded-lg gap-2.5 cursor-pointer focus:bg-tacir-lightgray py-2 text-sm text-tacir-darkblue">
              <Settings class="h-4 w-4 text-tacir-blue" /> Paramètres
            </DropdownMenuItem>
            <DropdownMenuSeparator class="bg-border my-1" />
            <DropdownMenuItem
              @click.prevent.stop="handleLogout"
              class="rounded-lg gap-2.5 cursor-pointer focus:bg-red-50 focus:text-red-600 text-red-500 py-2 text-sm font-medium"
            >
              <LogOut class="h-4 w-4" /> Se déconnecter
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>

    <!-- ── MOBILE : trigger + sheet ── -->
    <Sheet>
      <SheetTrigger as-child>
        <Button
          variant="ghost"
          size="icon"
          class="md:hidden fixed top-4 left-4 z-50 bg-white rounded-lg shadow-md border border-border text-tacir-darkblue hover:bg-tacir-lightgray"
        >
          <Menu class="h-5 w-5" />
        </Button>
      </SheetTrigger>

      <SheetContent side="left" class="p-0 w-64 bg-white border-r border-border">
        <div class="flex flex-col h-full">

          <!-- Logo -->
          <div data-v-53430c37="" class="px-10 py-4 border-b border-border flex items-center justify-center"><img data-v-53430c37="" src="/src/assets/logo.png" alt="crmPfe Logo" class="h-8 w-auto object-contain"></div>

          <!-- Navigation -->
          <nav class="flex-1 px-3 py-4 overflow-y-auto space-y-5">
            <div v-for="group in navigation" :key="group.title">
              <p class="px-3 mb-1.5 text-[10px] font-semibold text-tacir-darkgray uppercase tracking-widest">
                {{ group.title }}
              </p>
              <div class="space-y-0.5">
                <RouterLink
                  v-for="item in group.items"
                  :key="item.name"
                  :to="item.href"
                  class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150"
                  :class="[
                    item.exact 
                      ? $route.path === item.href 
                      : $route.path.startsWith(item.href)
                        ? 'bg-tacir-blue text-white shadow-sm'
                        : 'text-tacir-darkgray hover:text-tacir-darkblue hover:bg-tacir-lightgray'
                  ]"
                >
                  <component :is="item.icon" class="h-4 w-4 flex-shrink-0" />
                  {{ item.name }}
                </RouterLink>
              </div>
            </div>
          </nav>

          <!-- User (mobile) -->
          <div class="p-4 border-t border-border">
            <div class="flex items-center gap-3 px-3 py-3 bg-tacir-lightgray/50 rounded-xl border border-border">
              <Avatar class="h-8 w-8 flex-shrink-0">
                <AvatarFallback class="gradient-brand text-white font-bold text-sm">
                  {{ userInitial }}
                </AvatarFallback>
              </Avatar>
              <div class="flex flex-col overflow-hidden flex-1">
                <span class="text-sm font-semibold text-tacir-darkblue truncate">
                  {{ user?.full_name || 'Utilisateur' }}
                </span>
                <span class="text-[10px] text-tacir-lightblue font-medium uppercase tracking-wider">
                  {{ user?.role }}
                </span>
              </div>
              <Button
                variant="ghost"
                size="icon"
                @click.prevent.stop="handleLogout"
                class="text-tacir-darkgray hover:text-red-500 hover:bg-red-50 rounded-lg flex-shrink-0 h-8 w-8"
              >
                <LogOut class="h-4 w-4" />
              </Button>
            </div>
          </div>

        </div>
      </SheetContent>
    </Sheet>

  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { RouterLink } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet'
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

import {
  Zap, LayoutDashboard, Users, Target, BarChart3, Settings,
  LogOut, Menu, ChevronUp, User, ShieldCheck, RefreshCw,
  CheckCircle2, FileText,
} from 'lucide-vue-next'

const router = useRouter()
const { user, logout } = useAuth()

const userInitial = computed(() => {
  const name = user.value?.full_name || user.value?.email || 'U'
  return name.charAt(0).toUpperCase()
})

const navigation = computed(() => {
  const role = user.value?.role
  const items = []

  if (role === 'ADMIN') {
    items.push({
      title: 'Administration',
      items: [
        { name: 'Dashboard', href: '/admin', icon: ShieldCheck, exact: true },
        { name: 'Utilisateurs', href: '/admin/users', icon: Users },
        { name: 'Logs système', href: '/admin/logs', icon: FileText },
        { name: 'Config CRM', href: '/admin/crm', icon: Settings },
      ],
    })
  }

  if (role === 'CEO') {
    items.push({
      title: 'Management',
      items: [
        { name: 'Dashboard', href: '/manager', icon: LayoutDashboard, exact: true },
        { name: 'Pipeline équipe', href: '/manager/team', icon: Target },
        { name: 'Statistiques', href: '/manager/sync', icon: RefreshCw },
        { name: 'Rapports', href: '/manager/reports', icon: BarChart3 },
      ],
    })
  }

  if (role === 'COMMERCIAL') {
    items.push({
      title: 'Ventes',
      items: [
        { name: 'Dashboard', href: '/commercial', icon: Zap, exact: true },
        { name: 'Prospection', href: '/commercial/prospects', icon: Target },
        { name: 'Qualification', href: '/commercial/qualify', icon: CheckCircle2 },
        { name: 'Sync Boond', href: '/commercial/sync', icon: RefreshCw },
      ],
    })
  }

  return items
})

async function handleLogout() {
  await logout()
  router.push('/login')
}
</script>

<style scoped>
.gradient-brand {
  background: linear-gradient(135deg, #303e8c, #04adbf);
}
</style>