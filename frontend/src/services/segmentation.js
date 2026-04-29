/**
 * segmentation.js
 * Axios service for the Segmentation & Market Analysis feature.
 * Points to the FastAPI ETL service (different origin from the Django API).
 */
import axios from "axios";

const ETL_BASE = import.meta.env.VITE_ETL_API_URL || "http://localhost:8001";

const etlApi = axios.create({
  baseURL: ETL_BASE,
  headers: { "Content-Type": "application/json" },
});

export const SEGMENT_META = {
  0: { name: "PME technologiques", shortName: "PME", color: "#04ADBF", rec: "Offre digitale packagée" },
  1: { name: "PME opérationnelles", shortName: "PME", color: "#56A632", rec: "Accompagnement progressif" },
  2: { name: "PME en croissance", shortName: "PME", color: "#F29F05", rec: "Montée en gamme" },
  3: { name: "ETI technologiques", shortName: "ETI", color: "#303E8C", rec: "Co-innovation" },
  4: { name: "ETI établies", shortName: "ETI", color: "#2D3773", rec: "Relationship selling" },
  5: { name: "ETI grands comptes", shortName: "ETI", color: "#C2410C", rec: "ABM dédié" },
  6: { name: "Grands groupes", shortName: "GE", color: "#8E1C1C", rec: "Vente enterprise" },
};

export const SECTOR_LABELS = {
  "62.02A": "Conseil en systèmes et logiciels informatiques",
};

export function formatSector(value) {
  if (value === null || value === undefined || value === "") {
    return "Inconnu";
  }

  const normalized = String(value).trim();
  return SECTOR_LABELS[normalized] || normalized;
}

export const runClustering = () => etlApi.post("/segmentation/run");
export const getSummary = () => etlApi.get("/segmentation/summary");
export const getLeads = (params) => etlApi.get("/segmentation/leads", { params });

export function formatRevenue(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "N/A";
  }

  const amount = Number(value);

  if (Math.abs(amount) >= 1_000_000_000) {
    return `${(amount / 1_000_000_000).toLocaleString("fr-FR", {
      maximumFractionDigits: 1,
    })} Md€`;
  }

  if (Math.abs(amount) >= 1_000_000) {
    return `${(amount / 1_000_000).toLocaleString("fr-FR", {
      maximumFractionDigits: 1,
    })} M€`;
  }

  if (Math.abs(amount) >= 1_000) {
    return `${(amount / 1_000).toLocaleString("fr-FR", {
      maximumFractionDigits: 1,
    })} k€`;
  }

  return `${amount.toLocaleString("fr-FR", {
    maximumFractionDigits: 0,
  })} €`;
}
