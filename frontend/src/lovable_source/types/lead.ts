// ============================================================
// Lead Types — Raw API shape & enriched UI shape
// ============================================================

export interface RawDirigeant {
  nom: string | null;
  prenoms: string | null;
  qualite: string | null;
  nationalite: string | null;
  linkedin_url: string | null;
  type_dirigeant: string | null;
  date_de_naissance: string | null;
  annee_de_naissance: string | null;
}

export interface RawLead {
  nom: string | null;
  siren: string | null;
  siret: string | null;
  identifiant: string | null;
  categorie_entreprise: string | null;
  taille_entrep: string | null;
  secteur_activite: string | null;
  forme_juridique: string | null;
  ville: string | null;
  code_postal: number | string | null;
  pays: string | null;
  ca: number | null;
  nb_locaux: number | null;
  date_creation_entreprise: string | null;
  date_derniere_modif_site: string | null;
  date_scraping: string | null;
  telephone: string | null;
  adresse_email: string | null;
  info_boamp: unknown | null;
  created_at: string | null;
  updated_at: string | null;
  raw_lead_id: string | null;
  sources: Record<string, unknown> | null;
  dirigeants: RawDirigeant[] | null;
  dag_run_id?: string | null;
}

export interface RawLeadResponse {
  total: number;
  skip: number;
  limit: number;
  data: RawLead[];
}

// ---- UI Enriched types ----

export type LeadSegment = "PME" | "ETI" | "GE" | "Micro" | "Inconnu";
export type LeadStatus = "Nouveau" | "Qualifié" | "Opportunité";

export interface UIDirigeant {
  id: string;
  nom: string;
  prenoms: string;
  fullName: string;
  initials: string;
  qualite: string;
  nationalite: string;
  linkedinUrl: string | null;
  typeDirigeant: string;
  age: number | null;
  anneeNaissance: number | null;
}

export interface UILead {
  id: string;
  nom: string;
  siren: string;
  siret: string;
  identifiant: string;
  segment: LeadSegment;
  tailleEntreprise: string;
  secteurActivite: string;
  formeJuridique: string;
  ville: string;
  codePostal: string;
  pays: string;
  ca: number | null;
  caFormatted: string;
  nbLocaux: number | null;
  dateCreation: string | null;
  dateCreationFormatted: string;
  dateDerniereModif: string | null;
  dateDerniereModifFormatted: string;
  dateScraping: string | null;
  dateScrapingFormatted: string;
  telephone: string;
  email: string;
  hasBoamp: boolean;
  infoBoamp: unknown | null;
  createdAt: string | null;
  updatedAt: string | null;
  rawLeadId: string | null;
  sources: Record<string, unknown> | null;
  dirigeants: UIDirigeant[];
  nbDirigeants: number;
  dirigeantPrincipal: UIDirigeant | null;
  hasLinkedinDirigeant: boolean;
  hasEmail: boolean;
  hasTelephone: boolean;
  // Computed metrics
  completude: number;
  score: number;
  probaConversion: number;
  status: LeadStatus;
  // For status editing
  _rawStatus?: LeadStatus;
}
