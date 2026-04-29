<template>
  <Card class="border-border/80">
    <CardHeader class="flex flex-col gap-3 border-b border-border/60 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <CardTitle class="text-sm font-semibold text-tacir-darkblue">Performance</CardTitle>
        <CardDescription>
          Dernier entrainement du modele de lead scoring utilise dans Opportunites.
        </CardDescription>
      </div>

      <button
        class="inline-flex h-9 items-center justify-center rounded-md bg-tacir-blue px-4 text-sm font-semibold text-white hover:opacity-90 transition-opacity disabled:opacity-60"
        :disabled="training"
        @click="$emit('train')"
      >
        {{ training ? 'Entrainement...' : performance ? 'Reentrainer le modele' : 'Lancer le premier entrainement' }}
      </button>
    </CardHeader>

    <CardContent class="p-5">
      <div v-if="loading" class="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <div v-for="index in 8" :key="index" class="h-24 rounded-xl bg-muted animate-pulse" />
      </div>

      <div v-else-if="!performance" class="rounded-xl border border-dashed border-border bg-muted/20 px-5 py-8 text-center">
        <p class="text-sm font-medium text-foreground">Aucune metrique disponible pour le moment.</p>
        <p class="mt-1 text-xs text-muted-foreground">
          Lance l'entrainement pour calculer les scores predictifs et remplir cette section.
        </p>
      </div>

      <div v-else class="space-y-5">
        <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <div v-for="item in metricCards" :key="item.label" class="rounded-xl border border-border bg-white px-4 py-3">
            <p class="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">{{ item.label }}</p>
            <p class="mt-2 text-lg font-semibold text-tacir-darkblue">{{ item.value }}</p>
          </div>
        </div>

        <div v-if="leadTypeThresholds.length" class="rounded-xl border border-border bg-white px-4 py-4">
          <div>
            <p class="text-sm font-semibold text-tacir-darkblue">Seuils par type de lead</p>
            <p class="text-xs text-muted-foreground">
              Regles metier utilisees pour classer les leads en HOT, WARM ou COLD.
            </p>
          </div>

          <div class="mt-4 grid gap-3 md:grid-cols-3">
            <div
              v-for="item in leadTypeThresholds"
              :key="item.label"
              class="rounded-xl border px-4 py-3"
              :class="item.classes"
            >
              <p class="text-[11px] font-semibold uppercase tracking-wide" :class="item.labelClass">{{ item.label }}</p>
              <p class="mt-2 text-lg font-semibold" :class="item.valueClass">{{ item.value }}</p>
            </div>
          </div>
        </div>

        <div v-if="topImportances.length" class="rounded-xl border border-border bg-white px-4 py-4">
          <div class="flex items-center justify-between gap-3">
            <div>
              <p class="text-sm font-semibold text-tacir-darkblue">Top importances reelles du modele CatBoost</p>
              <p class="text-xs text-muted-foreground">
                Variables les plus utilisees par le dernier modele entraine.
              </p>
            </div>
          </div>

          <div class="mt-4 space-y-3">
            <div v-for="item in topImportances" :key="item.feature" class="space-y-1.5">
              <div class="flex items-center justify-between gap-3">
                <p class="text-sm font-medium text-foreground truncate">{{ formatFeatureLabel(item.feature) }}</p>
                <p class="text-xs font-semibold text-tacir-blue whitespace-nowrap">{{ formatImportance(item.importance) }}</p>
              </div>
              <div class="h-2 rounded-full bg-muted overflow-hidden">
                <div
                  class="h-full rounded-full bg-tacir-blue"
                  :style="{ width: `${Math.max(0, Math.min(100, Number(item.importance) || 0))}%` }"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </CardContent>
  </Card>
</template>

<script setup>
import { computed } from 'vue'

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

const props = defineProps({
  performance: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  training: { type: Boolean, default: false },
})

defineEmits(['train'])

function formatPercent(value) {
  if (value === null || value === undefined) return '-'
  return `${(Number(value) * 100).toFixed(1)}%`
}

function formatImportance(value) {
  if (value === null || value === undefined) return '-'
  return `${Number(value).toFixed(1)}%`
}

function formatDateTime(value) {
  if (!value) return '-'
  return new Intl.DateTimeFormat('fr-FR', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function formatFeatureLabel(value) {
  if (!value) return '-'
  return String(value).replaceAll('_', ' ')
}

function formatThreshold(value) {
  if (value === null || value === undefined) return '-'
  return `${(Number(value) * 100).toFixed(0)}`
}

const leadTypeThresholds = computed(() => {
  const thresholds = props.performance?.lead_type_thresholds
  if (!thresholds) return []

  const hotMin = Number(thresholds.hot_min)
  const warmMin = Number(thresholds.warm_min)

  if (Number.isNaN(hotMin) || Number.isNaN(warmMin)) return []

  return [
    {
      label: 'HOT',
      value: `>= ${formatThreshold(hotMin)}`,
      classes: 'border-emerald-200 bg-emerald-50/80',
      labelClass: 'text-emerald-700',
      valueClass: 'text-emerald-900',
    },
    {
      label: 'WARM',
      value: `${formatThreshold(warmMin)} a < ${formatThreshold(hotMin)}`,
      classes: 'border-amber-200 bg-amber-50/80',
      labelClass: 'text-amber-700',
      valueClass: 'text-amber-900',
    },
    {
      label: 'COLD',
      value: `< ${formatThreshold(warmMin)}`,
      classes: 'border-rose-200 bg-rose-50/80',
      labelClass: 'text-rose-700',
      valueClass: 'text-rose-900',
    },
  ]
})

const topImportances = computed(() => props.performance?.top_importances || [])

const metricCards = computed(() => {
  if (!props.performance) return []

  return [
    { label: 'Model Name', value: props.performance.model_name || '-' },
    { label: 'Model Version', value: props.performance.model_version || '-' },
    { label: 'Best Model', value: props.performance.best_model || '-' },
    { label: 'Last Training Date', value: formatDateTime(props.performance.last_training_date) },
    { label: 'Precision des HOT', value: formatPercent(props.performance.hot_precision) },
    { label: 'Precision des COLD', value: formatPercent(props.performance.cold_precision) },
    { label: 'Accuracy', value: formatPercent(props.performance.accuracy) },
    { label: 'Precision', value: formatPercent(props.performance.precision) },
    { label: 'Recall', value: formatPercent(props.performance.recall) },
    { label: 'F1-score', value: formatPercent(props.performance.f1_score) },
    { label: 'ROC-AUC', value: formatPercent(props.performance.roc_auc) },
    { label: 'Threshold', value: props.performance.threshold?.toFixed?.(2) ?? '-' },
    { label: 'Training Dataset Size', value: props.performance.training_dataset_size ?? '-' },
    { label: 'Nombre de features', value: props.performance.feature_count ?? '-' },
  ]
})
</script>
