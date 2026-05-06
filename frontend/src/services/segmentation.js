/**
 * segmentation.js
 * Axios service for the Segmentation & Market Analysis feature.
 * Points to the FastAPI ETL service.
 */
import etlApi from '@/api/etlAxios'

/* ─────────────────────────────────────────────
 * SEGMENT META
 * ───────────────────────────────────────────── */
export const SEGMENT_META = {
  0: { name: "PME énergie & retail", shortName: "PME", color: "#F29F05", rec: "Vertical niche" },
  1: { name: "Grands groupes matures", shortName: "GE", color: "#303E8C", rec: "Enterprise focus" },
  2: { name: "ETI établies diversifiées", shortName: "ETI", color: "#04ADBF", rec: "Relationship selling" },
  3: { name: "Petites structures jeunes", shortName: "PME", color: "#56A632", rec: "Self-serve" },
  4: { name: "ETI historiques – commerce de gros", shortName: "ETI", color: "#2D3773", rec: "Scalable offers" },
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
 * API CALLS
 * ───────────────────────────────────────────── */
export const runClustering = () => {
  return etlApi.post("/segmentation/run");
};

export const getSummary = () => {
  return etlApi.get("/segmentation/summary");
};

export const getLeads = (params) => {
  return etlApi.get("/segmentation/leads", { params });
};
