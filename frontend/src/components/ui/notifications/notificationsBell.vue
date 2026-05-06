<template>
  <div class="relative">

    <!-- Cloche -->
    <button
      @click="open = !open"
      class="relative p-2 rounded-lg hover:bg-tacir-lightgray transition"
    >
      <Bell class="w-5 h-5 text-tacir-darkgray" />

      <!-- Badge rouge avec le nombre non lus -->
      <span
        v-if="unread > 0"
        class="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white
               text-[10px] font-bold rounded-full flex items-center justify-center"
      >
        {{ unread > 9 ? '9+' : unread }}
      </span>

      <!-- Point vert = connecté, rouge = déconnecté -->
      <span
        class="absolute bottom-1 right-1 w-2 h-2 rounded-full border border-white"
        :class="connected ? 'bg-green-500' : 'bg-red-400'"
      />
    </button>

    <!-- Dropdown -->
    <div
      v-if="open"
      class="absolute right-0 top-12 w-88 bg-white border border-border
             rounded-xl shadow-lg z-50 overflow-hidden"
      style="width: 360px"
    >
      <!-- Header -->
      <div class="flex items-center justify-between px-4 py-3 border-b border-border">
        <div class="flex items-center gap-2">
          <span class="text-xs font-bold text-tacir-darkblue uppercase tracking-widest">
            Alertes ETL
          </span>
          <span
            class="text-[10px] px-2 py-0.5 rounded-full"
            :class="connected
              ? 'bg-green-100 text-green-700'
              : 'bg-red-100 text-red-600'"
          >
            {{ connected ? 'En direct' : 'Reconnexion...' }}
          </span>
        </div>
        <div class="flex items-center gap-3">
          <button
            v-if="unread > 0"
            @click="markAllAsRead"
            class="text-[10px] text-tacir-blue hover:underline"
          >
            Tout lire
          </button>
          <button
            v-if="alerts.length"
            @click="clearAll"
            class="text-[10px] text-slate-400 hover:text-red-500 transition"
          >
            Effacer
          </button>
        </div>
      </div>

      <!-- Liste -->
      <div class="max-h-80 overflow-y-auto divide-y divide-border">

        <div
          v-if="!alerts.length"
          class="px-4 py-8 text-center text-xs text-slate-400"
        >
          Aucune alerte — pipeline OK ✅
        </div>

        <!-- Carte alerte -->
        <div
          v-for="alert in alerts"
          :key="alert.id"
          @click="markAsRead(alert.id)"
          :class="[
            'px-4 py-3 transition',
            !alert.read ? 'bg-red-50' : 'hover:bg-slate-50'
          ]"
        >
          <!-- Titre : DAG + tâche -->
          <div class="flex items-center gap-2 mb-1.5">
            <span
              class="w-2 h-2 rounded-full flex-shrink-0"
              :class="alert.read ? 'bg-slate-300' : 'bg-red-500'"
            />
            <div class="flex flex-col min-w-0">
              <span class="text-xs font-bold text-tacir-darkblue truncate">
                {{ formatDagId(alert.dag_id) }}
              </span>
              <span class="text-[10px] text-slate-500 font-mono">
                tâche : <strong class="text-tacir-darkgray">{{ alert.task_id }}</strong>
              </span>
            </div>
          </div>

          <!-- Horodatage -->
          <p class="text-[10px] text-slate-400 ml-4 mb-1.5">
            {{ alert.timestamp }}
          </p>

          <!-- Lien vers le fichier de logs -->
          <RouterLink
            v-if="alert.log_file"
            :to="`/admin/etllogs?file=${alert.log_file}`"
            @click.stop="open = false"
            class="ml-4 inline-flex items-center gap-1.5 text-[10px] font-semibold
                   text-tacir-blue hover:underline"
          >
            <FileText class="w-3 h-3" />
            Voir les logs → {{ alert.log_file }}
          </RouterLink>
        </div>

      </div>
    </div>

  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Bell, FileText } from 'lucide-vue-next'
import { RouterLink } from 'vue-router'
import { useSSENotifications } from '@/composables/useSSENotifications'

const { alerts, unread, connected, markAsRead, markAllAsRead, clearAll }
  = useSSENotifications()

const open = ref(false)

/**
 * Transforme "sync_boamp" → "Pipeline BOAMP"
 * Transforme "sync_datagouv" → "Pipeline DataGouv"
 */
function formatDagId(dagId) {
  if (!dagId) return dagId
  return dagId
    .replace('sync_', 'Pipeline ')
    .replace('boamp', 'BOAMP')
    .replace('datagouv', 'DataGouv')
    .replace('_', ' ')
}
</script>