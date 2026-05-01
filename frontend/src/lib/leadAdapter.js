// ============================================================
// Lead Adapter — transforms raw API data into UI-ready shape
// Ported from lovable_source/lib/lead-adapter.ts to plain JS
// ============================================================

const CURRENT_YEAR = new Date().getFullYear()

const QUALITY_PRIORITY = [
  'Président',
  'Président Directeur Général',
  'PDG',
  'Directeur général',
  'Gérant',
  "Président du conseil d'administration",
  'Directeur',
  'Administrateur',
  'Commissaire aux comptes titulaire',
  'Commissaire aux comptes suppléant',
]

// ---- Helpers ----

export function mapSegment(cat) {
  if (!cat) return 'Inconnu'
  const lower = cat.toLowerCase()
  if (lower.includes('petite') || lower.includes('pme')) return 'PME'
  if (lower.includes('intermédiaire') || lower.includes('eti')) return 'ETI'
  if (lower.includes('grande')) return 'GE'
  if (lower.includes('micro')) return 'Micro'
  return 'Inconnu'
}

export function formatCA(ca) {
  if (ca == null) return '—'
  if (ca >= 1_000_000_000) return `${(ca / 1_000_000_000).toFixed(1).replace('.0', '')} Md€`
  if (ca >= 1_000_000) return `${(ca / 1_000_000).toFixed(1).replace('.0', '')} M€`
  if (ca >= 1_000) return `${(ca / 1_000).toFixed(0)} k€`
  return `${ca} €`
}

export function formatDateFR(dateStr) {
  if (!dateStr) return '—'
  try {
    const d = new Date(dateStr)
    if (isNaN(d.getTime())) return '—'
    return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' })
  } catch {
    return '—'
  }
}

function safeStr(val) {
  if (val == null || val === '') return '—'
  return String(val)
}

function calculateAge(annee) {
  if (!annee) return null
  const y = parseInt(annee, 10)
  if (isNaN(y)) return null
  return CURRENT_YEAR - y
}

function getInitials(nom, prenoms) {
  const first = prenoms ? prenoms.charAt(0).toUpperCase() : ''
  const last = nom ? nom.charAt(0).toUpperCase() : ''
  return `${first}${last}` || '?'
}

function titleCase(str) {
  if (!str) return ''
  return str
    .toLowerCase()
    .split(/[\s-]+/)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')
}

// ---- Dirigeant Adapter ----

function adaptDirigeant(d, index) {
  const nom = safeStr(d.nom)
  const prenoms = safeStr(d.prenoms)
  return {
    id: `dir-${index}-${nom}`,
    nom: nom === '—' ? '' : titleCase(nom),
    prenoms: prenoms === '—' ? '' : titleCase(prenoms),
    fullName:
      prenoms !== '—' && nom !== '—'
        ? `${titleCase(prenoms)} ${titleCase(nom)}`
        : titleCase(nom),
    initials: getInitials(d.nom ?? '', d.prenoms ?? ''),
    qualite: safeStr(d.qualite),
    nationalite: safeStr(d.nationalite),
    linkedinUrl: d.linkedin_url ?? null,
    email: d.email || null,
    telephone: d.telephone || null,
    typeDirigeant: safeStr(d.type_dirigeant),
    age: calculateAge(d.annee_de_naissance),
    anneeNaissance: d.annee_de_naissance ? parseInt(d.annee_de_naissance, 10) : null,
  }
}

function findPrincipalDirigeant(dirigeants) {
  if (dirigeants.length === 0) return null
  for (const prio of QUALITY_PRIORITY) {
    const found = dirigeants.find((d) =>
      d.qualite.toLowerCase().includes(prio.toLowerCase())
    )
    if (found) return found
  }
  return dirigeants[0]
}

// ---- Complétude ----

const COMPLETUDE_FIELDS = [
  'nom', 'siren', 'siret', 'categorie_entreprise', 'taille_entrep',
  'secteur_activite', 'forme_juridique', 'ville', 'code_postal', 'pays',
  'ca', 'nb_locaux', 'telephone', 'adresse_email',
  'date_creation_entreprise', 'date_derniere_modif_site',
]

export function computeCompletude(raw) {
  let filled = 0
  for (const field of COMPLETUDE_FIELDS) {
    const val = raw[field]
    if (val != null && val !== '' && val !== 0) filled++
  }
  const hasDirigeants = raw.dirigeants && raw.dirigeants.length > 0
  const total = COMPLETUDE_FIELDS.length + 1
  return Math.round(((filled + (hasDirigeants ? 1 : 0)) / total) * 100)
}

// ---- Score ----

export function computeScore(raw, completude) {
  // TODO: ML scoring to be implemented later
  return 0
}

// ---- Proba conversion ----

export function computeProbaConversion(score) {
  // TODO: ML scoring to be implemented later
  return 0
}

// ---- Status ----

export function computeStatus(score) {
  // Base database returns all as new initially
  return 'Nouveau'
}

// ---- Main adapter ----

export function adaptLead(raw, index) {
  const dirigeants = (raw.dirigeants ?? []).map((d, i) => adaptDirigeant(d, i))
  const completude = computeCompletude(raw)
  const score = computeScore(raw, completude)
  const probaConversion = computeProbaConversion(score)
  const status = computeStatus(score)

  return {
    id: raw.identifiant ?? raw.siren ?? `lead-${index}`,
    nom: safeStr(raw.nom),
    siren: safeStr(raw.siren),
    siret: safeStr(raw.siret),
    identifiant: safeStr(raw.identifiant),
    segment: mapSegment(raw.categorie_entreprise),
    tailleEntreprise: safeStr(raw.taille_entrep),
    secteurActivite: safeStr(raw.secteur_activite),
    formeJuridique: safeStr(raw.forme_juridique),
    ville: safeStr(raw.ville),
    codePostal: safeStr(raw.code_postal),
    pays: safeStr(raw.pays),
    ca: raw.ca ?? null,
    caFormatted: formatCA(raw.ca),
    nbLocaux: raw.nb_locaux ?? null,
    dateCreation: raw.date_creation_entreprise ?? null,
    dateCreationFormatted: formatDateFR(raw.date_creation_entreprise),
    dateDerniereModif: raw.date_derniere_modif_site ?? null,
    dateDerniereModifFormatted: formatDateFR(raw.date_derniere_modif_site),
    dateScraping: raw.date_scraping ?? null,
    dateScrapingFormatted: formatDateFR(raw.date_scraping),
    telephone: safeStr(raw.telephone),
    email: safeStr(raw.adresse_email),
    linkedin_url: raw.linkedin_url ?? null,
    website_url: raw.website_url ?? null,
    description: raw.description ?? null,
    hasBoamp: raw.info_boamp != null,
    infoBoamp: raw.info_boamp ?? null,
    createdAt: raw.created_at ?? null,
    updatedAt: raw.updated_at ?? null,
    rawLeadId: raw.raw_lead_id ?? null,
    sources: raw.sources ?? null,
    dirigeants,
    nbDirigeants: dirigeants.length,
    dirigeantPrincipal: findPrincipalDirigeant(dirigeants),
    hasLinkedinDirigeant: dirigeants.some((d) => d.linkedinUrl != null),
    hasEmail: raw.adresse_email != null && raw.adresse_email !== '',
    hasTelephone: raw.telephone != null && raw.telephone !== '',
    completude,
    score,
    probaConversion: Math.round(probaConversion),
    status,
  }
}

export function adaptLeadResponse(data) {
  return data.map((raw, i) => adaptLead(raw, i))
}
