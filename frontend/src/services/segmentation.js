/**
 * segmentation.js
 * Axios service for the Segmentation & Market Analysis feature.
 * Points to the FastAPI ETL service.
 */

import axios from "axios";

/**
 * IMPORTANT:
 * - Android emulator → use 10.0.2.2
 * - Browser → use localhost (via .env)
 */
const ETL_BASE =
  import.meta.env.VITE_ETL_API_URL || "http://10.0.2.2:8001";

console.log("[Segmentation] BASE URL:", ETL_BASE);

const etlApi = axios.create({
  baseURL: ETL_BASE,
  headers: { "Content-Type": "application/json" },
});

/* ─────────────────────────────────────────────
 * SEGMENT META
 * ───────────────────────────────────────────── */
export const SEGMENT_META = {
  0: { name: "PME technologiques", shortName: "PME", color: "#04ADBF", rec: "Offre digitale packagée" },
  1: { name: "PME opérationnelles", shortName: "PME", color: "#56A632", rec: "Accompagnement progressif" },
  2: { name: "PME en croissance", shortName: "PME", color: "#F29F05", rec: "Montée en gamme" },
  3: { name: "ETI technologiques", shortName: "ETI", color: "#303E8C", rec: "Co-innovation" },
  4: { name: "ETI établies", shortName: "ETI", color: "#2D3773", rec: "Relationship selling" },
  5: { name: "ETI grands comptes", shortName: "ETI", color: "#C2410C", rec: "ABM dédié" },
  6: { name: "Grands groupes", shortName: "GE", color: "#8E1C1C", rec: "Vente enterprise" },
};

/* ─────────────────────────────────────────────
 * HELPERS
 * ───────────────────────────────────────────── */
export const SECTOR_LABELS = {
  "62.02A": "Conseil en systèmes et logiciels informatiques",
};

export function formatSector(value) {
  if (!value) return "Inconnu";
  const normalized = String(value).trim();
  return SECTOR_LABELS[normalized] || normalized;
}

export function formatRevenue(value) {
  if (value == null || Number.isNaN(Number(value))) return "N/A";

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

/* ─────────────────────────────────────────────
 * API CALLS (WITH DEBUG LOGS)
 * ───────────────────────────────────────────── */
export const runClustering = () => {
  const url = "/segmentation/run";
  console.log("[Segmentation] POST:", `${ETL_BASE}${url}`);
  return etlApi.post(url);
};

export const getSummary = () => {
  const url = "/segmentation/summary";
  console.log("[Segmentation] GET:", `${ETL_BASE}${url}`);
  return etlApi.get(url);
};

export const getLeads = (params) => {
  const url = "/segmentation/leads";
  console.log("[Segmentation] GET:", `${ETL_BASE}${url}`, params);
  return etlApi.get(url, { params });
};