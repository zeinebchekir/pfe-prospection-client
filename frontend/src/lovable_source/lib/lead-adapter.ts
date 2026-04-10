// ============================================================
// Lead Adapter — transforms raw API data into UI-ready shape
// ============================================================

import type { RawLead, RawDirigeant, UILead, UIDirigeant, LeadSegment, LeadStatus } from "@/types/lead";

// ---- Helpers ----

const CURRENT_YEAR = new Date().getFullYear();

const QUALITY_PRIORITY: string[] = [
  "Président",
  "Président Directeur Général",
  "PDG",
  "Directeur général",
  "Gérant",
  "Président du conseil d'administration",
  "Directeur",
  "Administrateur",
  "Commissaire aux comptes titulaire",
  "Commissaire aux comptes suppléant",
];

export function mapSegment(cat: string | null): LeadSegment {
  if (!cat) return "Inconnu";
  const lower = cat.toLowerCase();
  if (lower.includes("petite") || lower.includes("pme")) return "PME";
  if (lower.includes("intermédiaire") || lower.includes("eti")) return "ETI";
  if (lower.includes("grande")) return "GE";
  if (lower.includes("micro")) return "Micro";
  return "Inconnu";
}

export function formatCA(ca: number | null): string {
  if (ca == null) return "—";
  if (ca >= 1_000_000_000) return `${(ca / 1_000_000_000).toFixed(1).replace(".0", "")} Md€`;
  if (ca >= 1_000_000) return `${(ca / 1_000_000).toFixed(1).replace(".0", "")} M€`;
  if (ca >= 1_000) return `${(ca / 1_000).toFixed(0)} k€`;
  return `${ca} €`;
}

export function formatDateFR(dateStr: string | null): string {
  if (!dateStr) return "—";
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return "—";
    return d.toLocaleDateString("fr-FR", { day: "numeric", month: "short", year: "numeric" });
  } catch {
    return "—";
  }
}

function safeStr(val: unknown): string {
  if (val == null || val === "") return "—";
  return String(val);
}

function calculateAge(annee: string | null): number | null {
  if (!annee) return null;
  const y = parseInt(annee, 10);
  if (isNaN(y)) return null;
  return CURRENT_YEAR - y;
}

function getInitials(nom: string, prenoms: string): string {
  const first = prenoms ? prenoms.charAt(0).toUpperCase() : "";
  const last = nom ? nom.charAt(0).toUpperCase() : "";
  return `${first}${last}` || "?";
}

function titleCase(str: string): string {
  if (!str) return "";
  return str
    .toLowerCase()
    .split(/[\s-]+/)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

// ---- Dirigeant Adapter ----

function adaptDirigeant(d: RawDirigeant, index: number): UIDirigeant {
  const nom = safeStr(d.nom);
  const prenoms = safeStr(d.prenoms);
  return {
    id: `dir-${index}-${nom}`,
    nom: nom === "—" ? "" : titleCase(nom),
    prenoms: prenoms === "—" ? "" : titleCase(prenoms),
    fullName: prenoms !== "—" && nom !== "—" ? `${titleCase(prenoms)} ${titleCase(nom)}` : titleCase(nom),
    initials: getInitials(d.nom ?? "", d.prenoms ?? ""),
    qualite: safeStr(d.qualite),
    nationalite: safeStr(d.nationalite),
    linkedinUrl: d.linkedin_url,
    typeDirigeant: safeStr(d.type_dirigeant),
    age: calculateAge(d.annee_de_naissance),
    anneeNaissance: d.annee_de_naissance ? parseInt(d.annee_de_naissance, 10) : null,
  };
}

function findPrincipalDirigeant(dirigeants: UIDirigeant[]): UIDirigeant | null {
  if (dirigeants.length === 0) return null;
  for (const prio of QUALITY_PRIORITY) {
    const found = dirigeants.find(
      (d) => d.qualite.toLowerCase().includes(prio.toLowerCase())
    );
    if (found) return found;
  }
  return dirigeants[0];
}

// ---- Complétude ----

const COMPLETUDE_FIELDS: (keyof RawLead)[] = [
  "nom", "siren", "siret", "categorie_entreprise", "taille_entrep",
  "secteur_activite", "forme_juridique", "ville", "code_postal", "pays",
  "ca", "nb_locaux", "telephone", "adresse_email",
  "date_creation_entreprise", "date_derniere_modif_site",
];

export function computeCompletude(raw: RawLead): number {
  let filled = 0;
  for (const field of COMPLETUDE_FIELDS) {
    const val = raw[field];
    if (val != null && val !== "" && val !== 0) filled++;
  }
  // Bonus for dirigeants
  const hasDirigeants = raw.dirigeants && raw.dirigeants.length > 0;
  const total = COMPLETUDE_FIELDS.length + 1;
  return Math.round(((filled + (hasDirigeants ? 1 : 0)) / total) * 100);
}

// ---- Score ----

export function computeScore(raw: RawLead, completude: number): number {
  let score = 0;
  // Completude weight: 30%
  score += completude * 0.3;

  // Taille: 15%
  const seg = mapSegment(raw.categorie_entreprise);
  if (seg === "GE") score += 15;
  else if (seg === "ETI") score += 12;
  else if (seg === "PME") score += 8;
  else if (seg === "Micro") score += 4;

  // CA: 15%
  if (raw.ca) {
    if (raw.ca >= 1_000_000_000) score += 15;
    else if (raw.ca >= 100_000_000) score += 12;
    else if (raw.ca >= 10_000_000) score += 10;
    else if (raw.ca >= 1_000_000) score += 7;
    else score += 3;
  }

  // Nb locaux: 10%
  if (raw.nb_locaux) {
    if (raw.nb_locaux >= 1000) score += 10;
    else if (raw.nb_locaux >= 100) score += 7;
    else if (raw.nb_locaux >= 10) score += 4;
    else score += 2;
  }

  // Fraîcheur: 10%
  if (raw.date_derniere_modif_site) {
    const daysDiff = (Date.now() - new Date(raw.date_derniere_modif_site).getTime()) / 86400000;
    if (daysDiff < 30) score += 10;
    else if (daysDiff < 90) score += 7;
    else if (daysDiff < 365) score += 4;
    else score += 1;
  }

  // Richesse dirigeants: 10%
  const nbDir = raw.dirigeants?.length ?? 0;
  if (nbDir >= 10) score += 10;
  else if (nbDir >= 5) score += 7;
  else if (nbDir >= 1) score += 4;

  // LinkedIn: 5%
  const hasLinkedin = raw.dirigeants?.some((d) => d.linkedin_url) ?? false;
  if (hasLinkedin) score += 5;

  // Coordonnées: 5%
  if (raw.telephone) score += 2.5;
  if (raw.adresse_email) score += 2.5;

  return Math.min(100, Math.round(score));
}

// ---- Proba conversion ----

export function computeProbaConversion(score: number): number {
  if (score >= 80) return Math.min(95, 60 + (score - 80) * 1.75);
  if (score >= 50) return 30 + (score - 50);
  return Math.max(5, score * 0.6);
}

// ---- Status ----

export function computeStatus(score: number): LeadStatus {
  if (score >= 70) return "Opportunité";
  if (score >= 40) return "Qualifié";
  return "Nouveau";
}

// ---- Main adapter ----

export function adaptLead(raw: RawLead, index: number): UILead {
  const dirigeants = (raw.dirigeants ?? []).map((d, i) => adaptDirigeant(d, i));
  const completude = computeCompletude(raw);
  const score = computeScore(raw, completude);
  const probaConversion = computeProbaConversion(score);
  const status = computeStatus(score);

  return {
    id: raw.siren ?? raw.identifiant ?? `lead-${index}`,
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
    ca: raw.ca,
    caFormatted: formatCA(raw.ca),
    nbLocaux: raw.nb_locaux,
    dateCreation: raw.date_creation_entreprise,
    dateCreationFormatted: formatDateFR(raw.date_creation_entreprise),
    dateDerniereModif: raw.date_derniere_modif_site,
    dateDerniereModifFormatted: formatDateFR(raw.date_derniere_modif_site),
    dateScraping: raw.date_scraping,
    dateScrapingFormatted: formatDateFR(raw.date_scraping),
    telephone: safeStr(raw.telephone),
    email: safeStr(raw.adresse_email),
    hasBoamp: raw.info_boamp != null,
    infoBoamp: raw.info_boamp,
    createdAt: raw.created_at,
    updatedAt: raw.updated_at,
    rawLeadId: raw.raw_lead_id,
    sources: raw.sources as Record<string, unknown> | null,
    dirigeants,
    nbDirigeants: dirigeants.length,
    dirigeantPrincipal: findPrincipalDirigeant(dirigeants),
    hasLinkedinDirigeant: dirigeants.some((d) => d.linkedinUrl != null),
    hasEmail: raw.adresse_email != null && raw.adresse_email !== "",
    hasTelephone: raw.telephone != null && raw.telephone !== "",
    completude,
    score,
    probaConversion,
    status,
  };
}

export function adaptLeadResponse(data: RawLead[]): UILead[] {
  return data.map((raw, i) => adaptLead(raw, i));
}
