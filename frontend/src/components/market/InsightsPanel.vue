<template>
  <div class="bg-white border border-border rounded-xl p-4 sm:p-5 shadow-sm">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
      <div class="flex items-center gap-2">
        <Lightbulb class="w-4 h-4 text-yellow-500 flex-shrink-0" />
        <div>
          <h3 class="font-semibold text-tacir-darkblue text-sm">Insights stratégiques</h3>
          <p class="text-[11px] text-tacir-darkgray">
            <span v-if="source === 'gemini-1.5-flash'" class="text-tacir-lightblue font-medium">✦ Gemini AI</span>
            <span v-else class="text-tacir-darkgray">Analyse basée sur les données</span>
          </p>
        </div>
      </div>
      <!-- Priority legend -->
      <div class="flex items-center gap-3 text-[10px] text-tacir-darkgray">
        <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-red-400"></span> Haute</span>
        <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-amber-400"></span> Moyenne</span>
        <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-gray-300"></span> Basse</span>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="!insights.length" class="grid grid-cols-1 md:grid-cols-2 gap-3">
      <div v-for="i in 6" :key="i" class="h-20 bg-gray-100 rounded-lg animate-pulse" />
    </div>

    <!-- Insight cards -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-3">
      <div
        v-for="insight in insights"
        :key="insight.title"
        class="flex gap-3 p-3.5 rounded-xl border transition-all hover:shadow-sm"
        :class="priorityBorder(insight.priority)"
      >
        <!-- Icon -->
        <div
          class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
          :class="priorityIconBg(insight.priority)"
        >
          <component :is="resolveIcon(insight.icon)" class="w-4 h-4" :class="priorityIconColor(insight.priority)" />
        </div>
        <!-- Text -->
        <div class="min-w-0">
          <div class="flex items-center gap-2 mb-1 flex-wrap">
            <p class="text-xs font-semibold text-tacir-darkblue leading-tight">{{ insight.title }}</p>
            <span
              class="text-[9px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded-full flex-shrink-0"
              :class="priorityBadge(insight.priority)"
            >
              {{ priorityLabel(insight.priority) }}
            </span>
          </div>
          <p class="text-[11px] text-tacir-darkgray leading-relaxed">{{ insight.description }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  Lightbulb, TrendingUp, Target, Zap, AlertTriangle,
  Users, BarChart3, RefreshCw, MapPin, Clock, Info,
} from "lucide-vue-next";

const props = defineProps({
  insights: { type: Array,  default: () => [] },
  source:   { type: String, default: "" },
});

// ── Icon resolver ──────────────────────────────────────────────────────────
const ICON_MAP = {
  TrendingUp, Target, Zap, AlertTriangle, Users,
  BarChart3, RefreshCw, MapPin, Clock, Info, Lightbulb,
};
function resolveIcon(name) {
  return ICON_MAP[name] || Info;
}

// ── Priority styling ───────────────────────────────────────────────────────
function priorityBorder(p) {
  if (p === "high")   return "border-red-100 bg-red-50/30";
  if (p === "medium") return "border-amber-100 bg-amber-50/20";
  return "border-gray-100 bg-gray-50/50";
}
function priorityIconBg(p) {
  if (p === "high")   return "bg-red-100";
  if (p === "medium") return "bg-amber-100";
  return "bg-gray-100";
}
function priorityIconColor(p) {
  if (p === "high")   return "text-red-500";
  if (p === "medium") return "text-amber-500";
  return "text-gray-400";
}
function priorityBadge(p) {
  if (p === "high")   return "bg-red-100 text-red-600";
  if (p === "medium") return "bg-amber-100 text-amber-600";
  return "bg-gray-100 text-gray-500";
}
function priorityLabel(p) {
  if (p === "high")   return "Priorité haute";
  if (p === "medium") return "Priorité moyenne";
  return "Info";
}
</script>
