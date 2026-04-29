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
  0: { name: "PME technologiques",  shortName: "PME", color: "#04ADBF", rec: "Offre digitale packagÃ©e" },
  1: { name: "PME opÃ©rationnelles", shortName: "PME", color: "#56A632", rec: "Accompagnement progressif" },
  2: { name: "PME en croissance",   shortName: "PME", color: "#F29F05", rec: "MontÃ©e en gamme" },
  3: { name: "ETI technologiques",  shortName: "ETI", color: "#303E8C", rec: "Co-innovation" },
  4: { name: "ETI Ã©tablies",       shortName: "ETI", color: "#2D3773", rec: "Relationship selling" },
  5: { name: "ETI grands comptes",  shortName: "ETI", color: "#C2410C", rec: "ABM dÃ©diÃ©" },
  6: { name: "Grands groupes",      shortName: "GE",  color: "#8E1C1C", rec: "Vente enterprise" },
};

export const runClustering = () => etlApi.post("/segmentation/run");
export const getSummary = () => etlApi.get("/segmentation/summary");
export const getLeads = (params) => etlApi.get("/segmentation/leads", { params });

export function formatRevenue(v) {
  if (v == null) return "â€”";
  if (v >= 1e9) return `${(v / 1e9).toFixed(1)} Mdâ‚¬`;
  if (v >= 1e6) return `${(v / 1e6).toFixed(1)} Mâ‚¬`;
  if (v >= 1e3) return `${(v / 1e3).toFixed(0)} kâ‚¬`;
  return `${v} â‚¬`;
}
