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
  0: { name: "PME énergie & retail",               shortName: "PME énergie",      color: "#F29F05", rec: "Vertical niche" },
  1: { name: "Grands groupes matures",              shortName: "Grands groupes",   color: "#303E8C", rec: "Enterprise focus" },
  2: { name: "ETI établies diversifiées",           shortName: "ETI établies",     color: "#04ADBF", rec: "Relationship selling" },
  3: { name: "Petites structures jeunes",           shortName: "Petites struct.",  color: "#56A632", rec: "Self-serve" },
  4: { name: "ETI historiques – commerce de gros",  shortName: "ETI commerce gros",color: "#2D3773", rec: "Scalable offers" },
};

export const runClustering  = ()       => etlApi.post("/segmentation/run");
export const getSummary     = ()       => etlApi.get("/segmentation/summary");
export const getLeads       = (params) => etlApi.get("/segmentation/leads", { params });

export function formatRevenue(v) {
  if (v == null) return "—";
  if (v >= 1e9)  return `${(v / 1e9).toFixed(1)} Md€`;
  if (v >= 1e6)  return `${(v / 1e6).toFixed(1)} M€`;
  if (v >= 1e3)  return `${(v / 1e3).toFixed(0)} k€`;
  return `${v} €`;
}
