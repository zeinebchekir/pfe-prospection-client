// ============================================================
// dashboardData.js — Port JS pur de dashboard-data.ts
// Calcule les KPIs, segments, distribution et funnel
// depuis le tableau de leads UI adapté par leadAdapter.js
// ============================================================

import { formatCA } from '@/lib/leadAdapter'

const CURRENT_YEAR = new Date().getFullYear()

export const SEGMENT_COLORS = {
  Microentreprise: '#303E8C',
  PME:             '#56A632',
  ETI:             '#F29F05',
  'Grande Entreprise': '#04ADBF',
  Inconnu:         '#94a3b8',
}

export const SEGMENT_BG = {
  Microentreprise: 'bg-[#303E8C]/10 text-[#303E8C]',
  PME:             'bg-[#56A632]/10 text-[#56A632]',
  ETI:             'bg-[#F29F05]/10 text-[#F29F05]',
  'Grande Entreprise': 'bg-[#04ADBF]/10 text-[#04ADBF]',
}

export const SEGMENT_BORDER = {
  Microentreprise: 'border-l-[#303E8C]',
  PME:             'border-l-[#56A632]',
  ETI:             'border-l-[#F29F05]',
  'Grande Entreprise': 'border-l-[#04ADBF]',
}

// Segment display labels (segment code → full label)
export const SEGMENT_LABELS = {
  Micro: 'Microentreprise',
  PME:   'PME',
  ETI:   'ETI',
  GE:    'Grande Entreprise',
  Inconnu: 'Inconnu',
}

// Ordered for display — 'Inconnu' MUST be included so all leads are counted
const SEGMENT_ORDER = ['Micro', 'PME', 'ETI', 'GE', 'Inconnu']

function companyAge(dateCreation) {
  if (!dateCreation) return null
  const y = new Date(dateCreation).getFullYear()
  if (isNaN(y)) return null
  return CURRENT_YEAR - y
}

function median(arr) {
  if (!arr.length) return 0
  const sorted = [...arr].sort((a, b) => a - b)
  const mid = Math.floor(sorted.length / 2)
  return sorted.length % 2
    ? sorted[mid]
    : (sorted[mid - 1] + sorted[mid]) / 2
}

/**
 * Compute all dashboard analytics from an array of adapted leads (from leadAdapter).
 *
 * @param {Array} leads - Array of adapted UI lead objects
 * @returns {{ kpis, segmentSummaries, distribution, funnel }}
 */
export function computeDashboardData(leads) {
  const total = leads.length

  // ── Global KPIs ───────────────────────────────────────────────
  const revenues = leads.map((l) => l.ca ?? 0)
  const avgRevenue = total ? revenues.reduce((a, b) => a + b, 0) / total : 0
  const totalCA    = revenues.reduce((a, b) => a + b, 0)

  const avgCompleteness = total
    ? Math.round(leads.reduce((s, l) => s + l.completude, 0) / total)
    : 0

  const ages = leads
    .map((l) => companyAge(l.dateCreation))
    .filter((a) => a !== null && a >= 0 && a < 300)

  const avgAge = ages.length
    ? Math.round(ages.reduce((s, a) => s + a, 0) / ages.length)
    : 0

  const kpis = {
    totalLeads:          total,
    averageRevenue:      formatCA(Math.round(avgRevenue)),
    totalCA:             formatCA(Math.round(totalCA)),
    averageCompleteness: avgCompleteness,
    averageAge:          avgAge,
    qualified:           leads.filter((l) => l.status === 'Qualifié').length,
    opportunities:       leads.filter((l) => l.status === 'Opportunité').length,
  }

  // ── Segment summaries ─────────────────────────────────────────
  const segmentSummaries = SEGMENT_ORDER.map((seg) => {
    const label     = SEGMENT_LABELS[seg]
    const segLeads  = leads.filter((l) => l.segment === seg)
    const count     = segLeads.length
    const cas       = segLeads.map((l) => l.ca ?? 0)
    const caMoyenRaw   = count ? cas.reduce((a, b) => a + b, 0) / count : 0
    const caMedianRaw  = median(cas)
    const completude   = count
      ? Math.round(segLeads.reduce((s, l) => s + l.completude, 0) / count)
      : 0
    const segAges = segLeads
      .map((l) => companyAge(l.dateCreation))
      .filter((a) => a !== null && a >= 0)
    const ageMoyen  = segAges.length
      ? Math.round(segAges.reduce((s, a) => s + a, 0) / segAges.length)
      : 0
    // Potentiel: moyenne probaConversion ou completude comme proxy si ML absent
    // potentiel = 0 jusqu'à l'implémentation du scoring ML
    const potentiel = 0

    return {
      name:        label,
      segment:     seg,
      caMoyen:     formatCA(Math.round(caMoyenRaw)),
      caMoyenRaw:  Math.round(caMoyenRaw),
      caMedianRaw: Math.round(caMedianRaw),
      completude,
      ageMoyen,
      count,
      potentiel,
    }
  })

  // ── Distribution pie ──────────────────────────────────────────
  // Use the real total (leads.length) for percentages — not the sum of
  // known segments — so the donut always matches the KPI card.
  // Filter out segments with 0 prospects to keep the chart clean.
  const distribution = segmentSummaries
    .filter((s) => s.count > 0)
    .map((s) => ({
      name:    s.name,
      segment: s.segment,
      value:   s.count,
      percent: total ? Math.round((s.count / total) * 100) : 0,
    }))

  // ── Funnel ────────────────────────────────────────────────────
  const funnel = [
    { name: 'Nouveaux',    value: leads.filter((l) => l.status === 'Nouveau').length    },
    { name: 'Qualifiés',   value: leads.filter((l) => l.status === 'Qualifié').length   },
    { name: 'Opportunités',value: leads.filter((l) => l.status === 'Opportunité').length },
  ]

  return { kpis, segmentSummaries, distribution, funnel }
}
