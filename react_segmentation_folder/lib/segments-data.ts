// Market segmentation data — derived from clustering output
// Business labels translate raw cluster IDs into executive-friendly segments.

export type SegmentRecommendation =
  | "Enterprise focus"
  | "Scalable offers"
  | "Self-serve"
  | "Vertical niche"
  | "Relationship selling";

export interface MarketSegment {
  id: string;
  clusterId: number;
  name: string;
  shortName: string;
  count: number;
  avgRevenue: number; // €
  avgRevenueLabel: string;
  avgEmployees: number;
  avgAge: number;
  avgLocations: number;
  dominantCategory: string;
  dominantSector: string;
  dominantRegion: string;
  recommendation: SegmentRecommendation;
  color: string; // hex for charts
  tailwindBg: string; // tailwind bg utility for badges
  tailwindText: string;
  tailwindBorder: string;
  description: string;
}

export const TOTAL_LEADS = 1054;

export const SEGMENTS: MarketSegment[] = [
  {
    id: "grands-groupes",
    clusterId: 1,
    name: "Grands groupes matures",
    shortName: "Grands groupes",
    count: 395,
    avgRevenue: 2_919_000_000,
    avgRevenueLabel: "2,9 Md€",
    avgEmployees: 4468,
    avgAge: 44,
    avgLocations: 319,
    dominantCategory: "Grande Entreprise",
    dominantSector: "Multi-sectoriel",
    dominantRegion: "Île-de-France",
    recommendation: "Enterprise focus",
    color: "#303E8C",
    tailwindBg: "bg-[#303E8C]/10",
    tailwindText: "text-[#303E8C]",
    tailwindBorder: "border-l-[#303E8C]",
    description: "Comptes stratégiques à fort potentiel de revenus.",
  },
  {
    id: "eti-etablies",
    clusterId: 2,
    name: "ETI établies diversifiées",
    shortName: "ETI établies",
    count: 378,
    avgRevenue: 292_500_000,
    avgRevenueLabel: "292,5 M€",
    avgEmployees: 1724,
    avgAge: 43,
    avgLocations: 168,
    dominantCategory: "Entreprise de Taille Intermédiaire",
    dominantSector: "Multi-sectoriel",
    dominantRegion: "Île-de-France",
    recommendation: "Relationship selling",
    color: "#04ADBF",
    tailwindBg: "bg-[#04ADBF]/10",
    tailwindText: "text-[#04ADBF]",
    tailwindBorder: "border-l-[#04ADBF]",
    description: "Meilleur équilibre volume / valeur du portefeuille.",
  },
  {
    id: "petites-jeunes",
    clusterId: 3,
    name: "Petites structures jeunes",
    shortName: "Petites structures",
    count: 204,
    avgRevenue: 32_300_000,
    avgRevenueLabel: "32,3 M€",
    avgEmployees: 29,
    avgAge: 25.5,
    avgLocations: 181,
    dominantCategory: "Petite et Moyenne Entreprise",
    dominantSector: "Transport d'électricité",
    dominantRegion: "Île-de-France",
    recommendation: "Self-serve",
    color: "#56A632",
    tailwindBg: "bg-[#56A632]/10",
    tailwindText: "text-[#56A632]",
    tailwindBorder: "border-l-[#56A632]",
    description: "Adaptées à une approche self-serve scalable.",
  },
  {
    id: "pme-energie-retail",
    clusterId: 0,
    name: "PME énergie & retail",
    shortName: "PME énergie",
    count: 46,
    avgRevenue: 182_900_000,
    avgRevenueLabel: "182,9 M€",
    avgEmployees: 163,
    avgAge: 18.8,
    avgLocations: 146,
    dominantCategory: "PME",
    dominantSector: "Transport d'électricité",
    dominantRegion: "Île-de-France",
    recommendation: "Vertical niche",
    color: "#F29F05",
    tailwindBg: "bg-[#F29F05]/10",
    tailwindText: "text-[#F29F05]",
    tailwindBorder: "border-l-[#F29F05]",
    description: "Niche verticale avec un cycle de vente structuré.",
  },
  {
    id: "eti-historiques",
    clusterId: 4,
    name: "ETI historiques – commerce de gros",
    shortName: "ETI commerce gros",
    count: 31,
    avgRevenue: 1_305_900_000,
    avgRevenueLabel: "1,3 Md€",
    avgEmployees: 1350,
    avgAge: 59.6,
    avgLocations: 180,
    dominantCategory: "Entreprise de Taille Intermédiaire",
    dominantSector: "Commerce de gros",
    dominantRegion: "Nord-Ouest",
    recommendation: "Scalable offers",
    color: "#2D3773",
    tailwindBg: "bg-[#2D3773]/10",
    tailwindText: "text-[#2D3773]",
    tailwindBorder: "border-l-[#2D3773]",
    description: "Volume réduit mais valeur unitaire très élevée.",
  },
];

export const RECOMMENDATION_STYLES: Record<SegmentRecommendation, string> = {
  "Enterprise focus": "bg-[#303E8C]/10 text-[#303E8C] border-[#303E8C]/20",
  "Scalable offers": "bg-[#2D3773]/10 text-[#2D3773] border-[#2D3773]/20",
  "Self-serve": "bg-[#56A632]/10 text-[#56A632] border-[#56A632]/20",
  "Vertical niche": "bg-[#F29F05]/10 text-[#F29F05] border-[#F29F05]/20",
  "Relationship selling": "bg-[#04ADBF]/10 text-[#04ADBF] border-[#04ADBF]/20",
};

export function getSegmentById(id: string): MarketSegment | undefined {
  return SEGMENTS.find((s) => s.id === id);
}

// Mock leads explorer rows — representative sample for the table
export interface ExplorerLead {
  id: string;
  nom: string;
  segmentId: string;
  secteur: string;
  ville: string;
  siren: string;
  ca: number | null;
  age: number;
  region: string;
  categorie: string;
  action: string;
}

export const EXPLORER_LEADS: ExplorerLead[] = [
  {
    id: "1",
    nom: "ELECTRICITE DE FRANCE (EDF)",
    segmentId: "grands-groupes",
    secteur: "Transport d'électricité",
    ville: "PARIS",
    siren: "552081317",
    ca: 118_690_000_000,
    age: 71,
    region: "Île-de-France",
    categorie: "Grande Entreprise",
    action: "RDV stratégique",
  },
  {
    id: "2",
    nom: "Université de Strasbourg",
    segmentId: "grands-groupes",
    secteur: "Enseignement",
    ville: "STRASBOURG",
    siren: "130005457",
    ca: null,
    age: 18,
    region: "Nord-Ouest",
    categorie: "Grande Entreprise",
    action: "Compte clé",
  },
  {
    id: "3",
    nom: "Keolis Grand Paris Vallée de la Marne",
    segmentId: "grands-groupes",
    secteur: "Transport voyageurs",
    ville: "CHELLES",
    siren: "922401880",
    ca: null,
    age: 3,
    region: "Île-de-France",
    categorie: "Grande Entreprise",
    action: "Qualification",
  },
  {
    id: "4",
    nom: "Vallée Sud - Grand Paris",
    segmentId: "eti-etablies",
    secteur: "Services publics",
    ville: "FONTENAY-AUX-ROSES",
    siren: "200057966",
    ca: null,
    age: 10,
    region: "Île-de-France",
    categorie: "Entreprise de Taille Intermédiaire",
    action: "Account-based",
  },
  {
    id: "5",
    nom: "Ville d'Antibes",
    segmentId: "eti-etablies",
    secteur: "Services publics",
    ville: "ANTIBES",
    siren: "210600045",
    ca: null,
    age: 125,
    region: "Sud",
    categorie: "Entreprise de Taille Intermédiaire",
    action: "Account-based",
  },
  {
    id: "6",
    nom: "SIAAP",
    segmentId: "eti-etablies",
    secteur: "Gestion déchets",
    ville: "PARIS",
    siren: "257550004",
    ca: null,
    age: 55,
    region: "Île-de-France",
    categorie: "Entreprise de Taille Intermédiaire",
    action: "Nurturing",
  },
  {
    id: "7",
    nom: "ETABLISSEMENTS PAGET",
    segmentId: "petites-jeunes",
    secteur: "Commerce de détail",
    ville: "VALZIN EN PETITE MONTAGNE",
    siren: "646250365",
    ca: 36_668,
    age: 64,
    region: "Est",
    categorie: "PME",
    action: "Self-serve",
  },
  {
    id: "8",
    nom: "Ets Public Sécurité ferroviaire",
    segmentId: "petites-jeunes",
    secteur: "Inspections techniques",
    ville: "AMIENS",
    siren: "130001316",
    ca: null,
    age: 20,
    region: "Île-de-France",
    categorie: "PME",
    action: "Self-serve",
  },
  {
    id: "9",
    nom: "VALEO",
    segmentId: "petites-jeunes",
    secteur: "Restauration rapide",
    ville: "ROUEN",
    siren: "902101864",
    ca: null,
    age: 4,
    region: "Île-de-France",
    categorie: "PME",
    action: "Activation",
  },
  {
    id: "10",
    nom: "Ville de Courbevoie",
    segmentId: "pme-energie-retail",
    secteur: "Services publics",
    ville: "COURBEVOIE",
    siren: "833981889",
    ca: null,
    age: 13,
    region: "Île-de-France",
    categorie: "PME",
    action: "Sectoriel",
  },
  {
    id: "11",
    nom: "SAFRAN",
    segmentId: "pme-energie-retail",
    secteur: "Location immobilière",
    ville: "LA LONDE-LES-MAURES",
    siren: "445337991",
    ca: null,
    age: 23,
    region: "Île-de-France",
    categorie: "PME",
    action: "Sectoriel",
  },
  {
    id: "12",
    nom: "Conseil Départemental Essonne",
    segmentId: "eti-historiques",
    secteur: "Commerce de gros",
    ville: "ÉVRY-COURCOURONNES",
    siren: "514813138",
    ca: null,
    age: 17,
    region: "Île-de-France",
    categorie: "Entreprise de Taille Intermédiaire",
    action: "Vente conseil",
  },
  {
    id: "13",
    nom: "Ville de Toulouse",
    segmentId: "eti-historiques",
    secteur: "Commerce de gros",
    ville: "TOULOUSE",
    siren: "391694064",
    ca: null,
    age: 33,
    region: "Sud",
    categorie: "Entreprise de Taille Intermédiaire",
    action: "Vente conseil",
  },
];

export function formatRevenue(value: number | null): string {
  if (value === null || value === undefined) return "—";
  if (value >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(1)} Md€`;
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)} M€`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(0)} k€`;
  return `${value} €`;
}
