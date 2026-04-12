import { useState, useMemo, useCallback } from "react";
import type { UILead, LeadSegment, LeadStatus } from "@/types/lead";
import type { RawLeadResponse } from "@/types/lead";
import { adaptLeadResponse } from "@/lib/lead-adapter";
import mockData from "@/data/mock-leads.json";

// ---- Filter state ----
export interface LeadFilters {
  search: string;
  segments: LeadSegment[];
  statuses: LeadStatus[];
  villes: string[];
  hasBoamp: boolean | null;
  hasEmail: boolean | null;
  hasTelephone: boolean | null;
  hasLinkedin: boolean | null;
  hasDirigeants: boolean | null;
  caMin: number | null;
  caMax: number | null;
  scoreMin: number | null;
  scoreMax: number | null;
}

export const INITIAL_FILTERS: LeadFilters = {
  search: "",
  segments: [],
  statuses: [],
  villes: [],
  hasBoamp: null,
  hasEmail: null,
  hasTelephone: null,
  hasLinkedin: null,
  hasDirigeants: null,
  caMin: null,
  caMax: null,
  scoreMin: null,
  scoreMax: null,
};

export type SortField = "nom" | "segment" | "ca" | "score" | "completude" | "probaConversion" | "nbLocaux" | "ville" | "nbDirigeants";
export type SortDir = "asc" | "desc";

function countActiveFilters(f: LeadFilters): number {
  let c = 0;
  if (f.search) c++;
  if (f.segments.length) c++;
  if (f.statuses.length) c++;
  if (f.villes.length) c++;
  if (f.hasBoamp !== null) c++;
  if (f.hasEmail !== null) c++;
  if (f.hasTelephone !== null) c++;
  if (f.hasLinkedin !== null) c++;
  if (f.hasDirigeants !== null) c++;
  if (f.caMin !== null || f.caMax !== null) c++;
  if (f.scoreMin !== null || f.scoreMax !== null) c++;
  return c;
}

export function useLeads() {
  const rawResponse = mockData as RawLeadResponse;
  const allLeads = useMemo(() => adaptLeadResponse(rawResponse.data), []);

  const [filters, setFilters] = useState<LeadFilters>(INITIAL_FILTERS);
  const [sortField, setSortField] = useState<SortField>("score");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [leadsState, setLeadsState] = useState<UILead[]>(allLeads);

  // Apply filters
  const filteredLeads = useMemo(() => {
    let result = [...leadsState];

    // Search
    if (filters.search) {
      const q = filters.search.toLowerCase();
      result = result.filter((l) => {
        return (
          l.nom.toLowerCase().includes(q) ||
          l.siren.toLowerCase().includes(q) ||
          l.siret.toLowerCase().includes(q) ||
          l.identifiant.toLowerCase().includes(q) ||
          l.ville.toLowerCase().includes(q) ||
          l.codePostal.toLowerCase().includes(q) ||
          l.secteurActivite.toLowerCase().includes(q) ||
          l.formeJuridique.toLowerCase().includes(q) ||
          l.tailleEntreprise.toLowerCase().includes(q) ||
          l.dirigeants.some(
            (d) => d.fullName.toLowerCase().includes(q)
          )
        );
      });
    }

    if (filters.segments.length) result = result.filter((l) => filters.segments.includes(l.segment));
    if (filters.statuses.length) result = result.filter((l) => filters.statuses.includes(l.status));
    if (filters.villes.length) result = result.filter((l) => filters.villes.includes(l.ville));
    if (filters.hasBoamp === true) result = result.filter((l) => l.hasBoamp);
    if (filters.hasBoamp === false) result = result.filter((l) => !l.hasBoamp);
    if (filters.hasEmail === true) result = result.filter((l) => l.hasEmail);
    if (filters.hasEmail === false) result = result.filter((l) => !l.hasEmail);
    if (filters.hasTelephone === true) result = result.filter((l) => l.hasTelephone);
    if (filters.hasTelephone === false) result = result.filter((l) => !l.hasTelephone);
    if (filters.hasLinkedin === true) result = result.filter((l) => l.hasLinkedinDirigeant);
    if (filters.hasLinkedin === false) result = result.filter((l) => !l.hasLinkedinDirigeant);
    if (filters.hasDirigeants === true) result = result.filter((l) => l.nbDirigeants > 0);
    if (filters.hasDirigeants === false) result = result.filter((l) => l.nbDirigeants === 0);
    if (filters.caMin !== null) result = result.filter((l) => l.ca !== null && l.ca >= filters.caMin!);
    if (filters.caMax !== null) result = result.filter((l) => l.ca !== null && l.ca <= filters.caMax!);
    if (filters.scoreMin !== null) result = result.filter((l) => l.score >= filters.scoreMin!);
    if (filters.scoreMax !== null) result = result.filter((l) => l.score <= filters.scoreMax!);

    return result;
  }, [leadsState, filters]);

  // Sort
  const sortedLeads = useMemo(() => {
    const sorted = [...filteredLeads];
    sorted.sort((a, b) => {
      let valA: string | number = 0;
      let valB: string | number = 0;
      switch (sortField) {
        case "nom": valA = a.nom; valB = b.nom; break;
        case "segment": valA = a.segment; valB = b.segment; break;
        case "ca": valA = a.ca ?? 0; valB = b.ca ?? 0; break;
        case "score": valA = a.score; valB = b.score; break;
        case "completude": valA = a.completude; valB = b.completude; break;
        case "probaConversion": valA = a.probaConversion; valB = b.probaConversion; break;
        case "nbLocaux": valA = a.nbLocaux ?? 0; valB = b.nbLocaux ?? 0; break;
        case "ville": valA = a.ville; valB = b.ville; break;
        case "nbDirigeants": valA = a.nbDirigeants; valB = b.nbDirigeants; break;
      }
      if (typeof valA === "string") {
        const cmp = valA.localeCompare(valB as string);
        return sortDir === "asc" ? cmp : -cmp;
      }
      return sortDir === "asc" ? (valA as number) - (valB as number) : (valB as number) - (valA as number);
    });
    return sorted;
  }, [filteredLeads, sortField, sortDir]);

  // Pagination
  const totalPages = Math.ceil(sortedLeads.length / pageSize);
  const paginatedLeads = useMemo(() => {
    const start = (page - 1) * pageSize;
    return sortedLeads.slice(start, start + pageSize);
  }, [sortedLeads, page, pageSize]);

  // KPIs
  const kpis = useMemo(() => {
    const leads = filteredLeads;
    const total = leads.length;
    const avgScore = total ? Math.round(leads.reduce((s, l) => s + l.score, 0) / total) : 0;
    const avgProba = total ? Math.round(leads.reduce((s, l) => s + l.probaConversion, 0) / total) : 0;
    const avgCompletude = total ? Math.round(leads.reduce((s, l) => s + l.completude, 0) / total) : 0;
    const totalCA = leads.reduce((s, l) => s + (l.ca ?? 0), 0);
    const qualified = leads.filter((l) => l.status === "Qualifié").length;
    const opportunities = leads.filter((l) => l.status === "Opportunité").length;
    return { total, avgScore, avgProba, avgCompletude, totalCA, qualified, opportunities };
  }, [filteredLeads]);

  // Unique values for filter dropdowns
  const uniqueVilles = useMemo(() => [...new Set(allLeads.map((l) => l.ville).filter((v) => v !== "—"))].sort(), [allLeads]);
  const uniqueSegments: LeadSegment[] = ["PME", "ETI", "GE", "Micro", "Inconnu"];
  const uniqueStatuses: LeadStatus[] = ["Nouveau", "Qualifié", "Opportunité"];

  const activeFilterCount = countActiveFilters(filters);

  const resetFilters = useCallback(() => {
    setFilters(INITIAL_FILTERS);
    setPage(1);
  }, []);

  const toggleSort = useCallback((field: SortField) => {
    if (sortField === field) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDir("desc");
    }
  }, [sortField]);

  const updateLeadStatus = useCallback((id: string, newStatus: LeadStatus) => {
    setLeadsState((prev) =>
      prev.map((l) => (l.id === id ? { ...l, status: newStatus } : l))
    );
  }, []);

  const updateLead = useCallback((id: string, updates: Partial<UILead>) => {
    setLeadsState((prev) =>
      prev.map((l) => (l.id === id ? { ...l, ...updates } : l))
    );
  }, []);

  return {
    allLeads: leadsState,
    filteredLeads,
    sortedLeads,
    paginatedLeads,
    filters,
    setFilters,
    sortField,
    sortDir,
    toggleSort,
    page,
    setPage,
    pageSize,
    totalPages,
    kpis,
    uniqueVilles,
    uniqueSegments,
    uniqueStatuses,
    activeFilterCount,
    resetFilters,
    updateLeadStatus,
    updateLead,
    totalFromApi: rawResponse.total,
  };
}
