# Segmentation & Market Analysis — Complete Feature Documentation

> **Branch:** `feat/segmentation-market-analysis`  
> **Role required:** `CEO` (blocked for ADMIN and COMMERCIAL)  
> **URL:** `/manager/segmentation`

---

## Table of Contents

1. [Feature Overview](#1-feature-overview)
2. [Architecture & Data Flow](#2-architecture--data-flow)
3. [Python Clustering Pipeline](#3-python-clustering-pipeline)
4. [FastAPI Endpoints](#4-fastapi-endpoints)
5. [Frontend Service Layer](#5-frontend-service-layer)
6. [Vue Components — What Each Does](#6-vue-components--what-each-does)
7. [Insights Panel — Logic Explained](#7-insights-panel--logic-explained)
8. [Pagination Logic](#8-pagination-logic)
9. [Responsiveness Strategy](#9-responsiveness-strategy)
10. [File Map — Every File & Its Role](#10-file-map--every-file--its-role)
11. [API Contract](#11-api-contract)
12. [How to Trigger & Test](#12-how-to-trigger--test)

---

## 1. Feature Overview

The **Segmentation & Market Analysis** page is an executive dashboard for the CEO role. It automatically groups the company's entire lead database into **5 behavioral clusters** using **KMeans machine learning**, then presents each cluster as a named business segment with:

- KPI summary cards
- A bubble chart of segment volume
- Individual segment profile cards
- Bar charts comparing CA and headcount
- A radar chart for multi-dimensional comparison
- A bubble scatter opportunity matrix
- Strategic insight cards
- A searchable, filterable, paginated leads table

**Why this matters:** Instead of looking at 1000+ raw leads, the CEO sees 5 archetypal customer profiles and can make targeted decisions on each.

---

## 2. Architecture & Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│  PostgreSQL (ETL DB)                                                │
│  Table: entreprise (~1000 rows)                                     │
│  Fields used: siren, nom, taille_entrep, ca, date_creation,         │
│               secteur_activite, categorie_entreprise, nb_locaux,    │
│               code_postal, ville                                     │
└────────────────────────┬────────────────────────────────────────────┘
                         │ SQLAlchemy SELECT *
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ETL FastAPI (port 8001)                                            │
│  POST /segmentation/run                                             │
│    → calls run_clustering(db)                                       │
│    → writes cluster_summary.json + clustered_leads.json            │
│    → returns summary JSON in HTTP response body                      │
│                                                                     │
│  GET  /segmentation/summary  → reads cluster_summary.json           │
│  GET  /segmentation/leads    → reads clustered_leads.json + filters │
└────────────────────────┬────────────────────────────────────────────┘
                         │ HTTP (axios, no cookie auth needed)
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Vue 3 Frontend (port 5174)                                         │
│  src/services/segmentation.js  ← axios calls                       │
│  src/pages/manager/MarketAnalysisPage.vue  ← orchestrates page     │
│  src/components/market/*.vue   ← 8 specialized components          │
└─────────────────────────────────────────────────────────────────────┘
```

> **Important:** The segmentation endpoints talk to the ETL FastAPI (port 8001), **not** Django (port 8000). The Django backend is only used for authentication (cookie JWT). This is why there is a **dedicated axios instance** in `segmentation.js`.

---

## 3. Python Clustering Pipeline

**File:** `ETL_service/ETL_pipeline/market_analysis/clustering.py`

### Step-by-step breakdown

#### Step 1 — Load data from DB
```python
rows = db.query(Entreprise).all()
df = pd.DataFrame([{
    "siren":               r.siren,
    "nom_entreprise":      r.nom,
    "categorie_entreprise": r.categorie_entreprise or "PME",
    "tranche_effectif":    r.taille_entrep,   # e.g. "100 à 199 salariés"
    "nb_locaux":           r.nb_locaux,
    "chiffre_affaires":    r.ca,
    "date_creation":       r.date_creation_entreprise,
    "code_postal":         r.code_postal,
    "secteur_activite":    r.secteur_activite,
    "ville":               r.ville,
} for r in rows])
```
This converts the ORM result directly into a pandas DataFrame, mapping ORM column names (e.g., `taille_entrep`) to the clustering script's expected names (e.g., `tranche_effectif`).

#### Step 2 — Data cleaning
- `nb_locaux` and `chiffre_affaires` are coerced to numeric (removes string artifacts)
- Duplicate SIRENs removed (`drop_duplicates`)
- Missing `categorie_entreprise` filled with `"PME"`

#### Step 3 — Feature Engineering
This is the **most important step** — raw fields can't go directly into KMeans because:
- Text categories have no numeric meaning
- Very large numbers (CA in billions) would dominate; we use **log scale**

| Raw field | Engineering | Why |
|-----------|-------------|-----|
| `tranche_effectif` (text) | Mapped to midpoint integer via `EFFECTIF_MAP` dict | KMeans needs numbers |
| `chiffre_affaires` | `np.log1p(ca)` — log scale | Avoids billion-euro outliers |
| `nb_locaux` | `np.log1p(nb_locaux)` | Same reason |
| `date_creation` | `(today - date) / 365.25` → `age_entreprise` in years | Age is more meaningful than date |
| `code_postal` | `_get_region()` → 5 regions | Reduces 96 departments to 5 zones |
| `secteur_activite` | Keep top-8 sectors, rest → `"Autre"` | Prevents too many dummy columns |

#### Step 4 — Feature matrix
```python
NUM_FEATURES = ["nb_employes_mid", "ca_log", "nb_locaux_log", "age_entreprise"]
CAT_FEATURES = ["categorie_entreprise", "region", "secteur_broad"]

X_num = df[NUM_FEATURES]
X_cat = pd.get_dummies(df[CAT_FEATURES])   # One-Hot Encoding
X_raw = pd.concat([X_num, X_cat], axis=1)

X = StandardScaler().fit_transform(X_raw)  # Normalise to N(0,1)
```
**StandardScaler** is critical: without it, `chiffre_affaires` (even log-scaled) would have far more weight than the category dummies.

#### Step 5 — KMeans K=5
```python
km = KMeans(n_clusters=5, random_state=42, n_init=20)
df["cluster"] = km.fit_predict(X)
```
- `random_state=42` → **deterministic**: same data always gives same cluster assignments
- `n_init=20` → runs 20 different initializations, picks the best (avoids local minima)
- K=5 was chosen based on domain knowledge (the 5 business labels match real market segments)

#### Step 6 — Summary aggregation
For each cluster compute:
- `n` = count of leads
- `employes_moyen` = average headcount
- `ca_moyen` = average revenue
- `nb_locaux_moyen` = average sites
- `age_moyen` = average age in years
- `categorie_dominante` = most frequent legal category (mode)
- `secteur_dominant` = most frequent sector
- `region_dominante` = most frequent region

#### Step 7 — Business label mapping
```python
SEGMENT_LABELS = {
    0: {"name": "PME énergie & retail",               "color": "#F29F05", "recommendation": "Vertical niche"},
    1: {"name": "Grands groupes matures",              "color": "#303E8C", "recommendation": "Enterprise focus"},
    2: {"name": "ETI établies diversifiées",           "color": "#04ADBF", "recommendation": "Relationship selling"},
    3: {"name": "Petites structures jeunes",           "color": "#56A632", "recommendation": "Self-serve"},
    4: {"name": "ETI historiques – commerce de gros",  "color": "#2D3773", "recommendation": "Scalable offers"},
}
```
These labels are **fixed by cluster number (0–4)**. Because `random_state=42`, the same cluster number always corresponds to the same group of companies. This makes the labels stable across re-runs.

#### Step 8 — JSON export
Two files written to `/opt/airflow/exports/segmentation/` (Docker volume):
- `cluster_summary.json` — the 5 segment profiles with all stats
- `clustered_leads.json` — every lead with its assigned cluster

---

## 4. FastAPI Endpoints

**File:** `ETL_service/ETL_pipeline/apis/routers/segmentation.py`  
**Registered in:** `ETL_service/ETL_pipeline/apis/main.py` at prefix `/segmentation`

### `POST /segmentation/run`
- **What it does:** Reads all `Entreprise` rows → calls `run_clustering(db)` → saves JSON files → returns summary
- **When to call:** When CEO clicks "Relancer l'analyse" in the UI
- **Duration:** ~3–8 seconds on 1000 rows
- **Returns:** `{ status, run_at, total_rows, segments: [...] }`
- **Error:** `400` if DB is empty; `500` on any runtime error

### `GET /segmentation/summary`
- **What it does:** Opens `cluster_summary.json` and returns it directly
- **Returns:** `{ run_at, total_leads, segments: [...] }`
- **Error:** `404` if clustering has never been run

### `GET /segmentation/leads`
- **Query params:**
  - `segment` (int, optional): filter by cluster number 0–4
  - `search` (str, optional): filter by `nom_entreprise` substring (case-insensitive)
  - `skip` (int, default 0): offset for pagination
  - `limit` (int, default 50): max rows to return
- **Returns:** `{ total, skip, limit, segment_label, leads: [...] }`
- **Note:** Filtering is done in Python (not SQL) because the data is in a JSON file, not in SQL at query time

---

## 5. Frontend Service Layer

**File:** `frontend/src/services/segmentation.js`

```js
// Separate axios instance — points to ETL FastAPI, NOT Django
const etlApi = axios.create({
  baseURL: import.meta.env.VITE_ETL_API_URL || "http://localhost:8001",
});

export const runClustering  = ()       => etlApi.post("/segmentation/run");
export const getSummary     = ()       => etlApi.get("/segmentation/summary");
export const getLeads       = (params) => etlApi.get("/segmentation/leads", { params });
```

**Why a separate axios instance?**
The main `@/api/axios.js` has `baseURL: '/api'` and sends Django CSRF cookies. The ETL service has no Django authentication — it's a standalone FastAPI on port 8001. Mixing them would cause CORS errors and unnecessary auth headers.

**Also exported from this file:**
- `SEGMENT_META` — the 5 segment labels/colors/recommendations (identical to Python's `SEGMENT_LABELS`) — used by **all** Vue components to colorize badges/charts without re-fetching from the API
- `formatRevenue(v)` — shared utility: converts raw euros to `"2.9 Md€"`, `"292 M€"`, `"14 k€"` — used in multiple components

---

## 6. Vue Components — What Each Does

All components live in `frontend/src/components/market/`

### `MarketKPICards.vue`
**Props:** `segments`, `totalLeads`  
**What it does:** Computes 6 KPIs from the `segments` array:
1. **Total leads** — raw count from `totalLeads`
2. **Segments** — always 5
3. **Segment dominant** — the cluster with the most leads (highest `n`)
4. **CA moyen pondéré** — weighted average CA: `Σ(ca_moyen × n) / Σ(n)` — gives a representative "portfolio" revenue average
5. **Âge moyen** — same weighted average for `age_moyen`
6. **Priorité CA** — the segment with the highest (ca_moyen × n) product — highest revenue *opportunity*

All computed with **no external API call** — pure JavaScript from the summary data.

---

### `SegmentBubbleChart.vue`
**Props:** `segments`, `totalLeads`  
**What it does:** Pure SVG chart (no library). Each segment becomes a circle:
- **Radius** proportional to `n / max_n` (between r=6 and r=18 in SVG units)
- **Position** from a hardcoded `POSITIONS` array (largest segment center, others around it)
- **Color** from `SEGMENT_META`
- **Text overlay** positioned with absolute CSS using `left/top` % matching SVG coordinates

Each bubble shows: segment shortname, `%` of total leads, and lead count.

---

### `SegmentCard.vue`
**Props:** `segment`, `totalLeads`  
**What it does:** Detailed profile card for one segment. Key design choice: a **colored left border** (`border-l-4`) using the segment color to give instant visual identity.

Displays:
- Segment name and lead count with `% of total`
- 3 stat boxes: CA moyen, Effectif moyen, Âge moyen
- 3 detail rows: Catégorie dominante, Secteur dominant, Région dominante
- A colored recommendation badge (e.g., "Enterprise focus")

---

### `SegmentComparisonCharts.vue`
**Props:** `segments`  
**What it does:** Two side-by-side ApexCharts bar charts:
1. **CA moyen par segment** — Y-axis formatted with `formatRevenue()`
2. **Effectif moyen par segment** — Y-axis shows raw employee count

Each bar is **distributed** (one color per bar, using the segment color array). X-axis labels are shortened to 2 words.

**Why ApexCharts?** `vue3-apexcharts` is already installed in `package.json`. ECharts (`vue-echarts`) requires a global `app.use()` call in `main.js` that was missing, causing a rendering bug (charts following scroll).

---

### `SegmentRadarChart.vue`
**Props:** `segments`  
**What it does:** Multi-dimensional comparison of up to 3 segments on 5 axes:
1. **Taille** — `employes_moyen / max_employes × 100`
2. **Valeur CA** — `ca_moyen / max_ca × 100`
3. **Ancienneté** — `age_moyen / max_age × 100`
4. **Multi-sites** — `nb_locaux_moyen / max_locaux × 100`
5. **Concentr. géo** — 90 if `region_dominante === "Ile-de-France"`, else 50

All values are **normalized to 0–100%** so the radar is balanced (bigger segments don't dominate visually).

Toggle buttons at the top let the CEO pick which 3 segments to compare (clicking a 4th removes the oldest selection).

---

### `OpportunityMatrix.vue`
**Props:** `segments`  
**What it does:** ApexCharts scatter chart plotting each segment at:
- **X position** = number of leads (`n`) → volume
- **Y position** = `ca_moyen` → value
- **Bubble size** = proportional to `n` (min 8px, max 48px radius)

This is a classic **BCG-style opportunity quadrant**: high in the chart = high value, far right = large volume. The top-right quadrant = highest priority segments.

---

### `InsightsPanel.vue`
**Props:** none  
**What it does:** 6 hardcoded strategic insight cards with icons. See Section 7 for the logic.

---

### `LeadsExplorerTable.vue`
**Props:** `segments`  
**What it does:** Fully paginated, filterable table of all leads. See Section 8 for pagination logic.

---

## 7. Insights Panel — Logic Explained

**File:** `frontend/src/components/market/InsightsPanel.vue`

The 6 insights are **rule-based** and **static** — they are not computed dynamically from the API response. Here is the reasoning behind each:

### Why static instead of dynamic?

The cluster labels are fixed (hardcoded `SEGMENT_LABELS` with `random_state=42`), so the characteristics of each cluster are known in advance. Dynamic insights would require additional statistical work (significance tests, threshold checks) with marginal benefit for a CEO dashboard.

### Insight 1 — Grands groupes: levier principal
- **Rule:** Cluster 1 always contains large enterprises by KMeans construction
- **Data basis:** `n ≈ 395`, `ca_moyen ≈ 2.9 Md€`
- **Insight:** Highest absolute revenue potential → prioritize long-cycle enterprise sales

### Insight 2 — ETI établies: meilleur ROI
- **Rule:** Cluster 2 = mid-range companies with good CA and many leads
- **Data basis:** `n ≈ 378`, `ca_moyen ≈ 292 M€`
- **Insight:** Best volume-value ratio → account-based selling

### Insight 3 — Petites structures: scalabilité
- **Rule:** Cluster 3 = small, young companies with low CA but high count
- **Data basis:** `n ≈ 204`
- **Insight:** Too many to sell to manually → automate with self-serve onboarding

### Insight 4 — PME énergie: niche à fort potentiel
- **Rule:** Cluster 0 = small count but significant CA — niche companies
- **Data basis:** `n ≈ 46`, `ca_moyen ≈ 183 M€`
- **Insight:** Low volume but high value per company → build a vertical sector offer

### Insight 5 — ETI historiques: vente conseil premium
- **Rule:** Cluster 4 = old companies, high CA, few leads
- **Data basis:** `n ≈ 31`, `age_moyen ≈ 59 ans`, `ca_moyen ≈ 1.3 Md€`
- **Insight:** Relationship-driven, long-tenure → consultative sales only

### Insight 6 — Ile-de-France concentration
- **Rule:** Geographic pattern observed in clustering output
- **Basis:** 3 of 5 segments have `region_dominante = "Ile-de-France"`
- **Insight:** Heavy geographic concentration → reinforce Paris-area sales presence

> **To make insights dynamic in the future:** Pass `segments` as a prop, compute thresholds (e.g., `n > 200 → scale` flag, `ca_moyen > 1e9 → enterprise` flag) and generate insight text from computed values.

---

## 8. Pagination Logic

**File:** `frontend/src/components/market/LeadsExplorerTable.vue`

### How it works

All pagination is **API-side** (the backend `GET /segmentation/leads` handles `skip` and `limit`). The frontend only manages the current page number.

```
skip = page × limit          (e.g., page=2, limit=20 → skip=40)
```

### Smart page number display

The `visiblePages` computed property generates numbered buttons with ellipsis:

```js
// Always shows: first page (0), last page (totalPages-1),
// current page (page), and current ± 1
// Inserts "..." between non-adjacent groups
```

**Example (50 pages, currently on page 24):**
```
« ‹  1  …  23  [24]  25  …  50  ›  »
```

### Per-page selector
The user can choose 10, 20, or 50 leads per page. Changing it resets to page 0 and refetches.

### Combined filtering + pagination
When the user changes the **segment filter** or **search text**, `page` is reset to `0` before fetching. This prevents being "stuck" on page 5 after filtering to a segment with only 2 pages.

### Display range
Shows `"Affichage 21–40 sur 1054 résultats"` computed as:
```js
from: page * limit + 1
to:   Math.min((page + 1) * limit, total)
```

---

## 9. Responsiveness Strategy

### Breakpoints used (Tailwind)
| Breakpoint | Width | Changes |
|-----------|-------|---------|
| (default) | < 640px | Single column, compact header |
| `sm:` | ≥ 640px | Header unwraps, 2-col grids appear |
| `md:` | ≥ 768px | Table shows Secteur column, 2-col cards |
| `lg:` | ≥ 1024px | Radar+Matrix side-by-side, 3-col grids |
| `xl:` | ≥ 1280px | 3-col segment cards, table shows Region |

### Key responsive decisions
1. **Sidebar**: The `AppSidebar` becomes a hamburger drawer on `< md` (built-in behavior of the Sheet component)
2. **Header**: On mobile shows only the run button text as "Lancer", full text on `sm+`
3. **Segment cards**: `grid-cols-1 sm:grid-cols-2 xl:grid-cols-3` — never squish 5 cards on one tiny row
4. **Table columns**: Progressive reveal — Entreprise+Segment always visible; Secteur on md+; Ville on lg+; Région on xl+
5. **Charts**: ApexCharts `height` is fixed in px not %, preventing overflow
6. **Table toolbar**: Wraps to second line on mobile (`flex-wrap`)

---

## 10. File Map — Every File & Its Role

```
pfe-prospection-client/
│
├── ETL_service/
│   ├── ETL_pipeline/
│   │   ├── market_analysis/
│   │   │   ├── __init__.py              — Python package marker
│   │   │   └── clustering.py            — ★ KMeans pipeline (DB → JSON)
│   │   └── apis/
│   │       ├── routers/
│   │       │   └── segmentation.py      — ★ 3 FastAPI endpoints
│   │       └── main.py                  — (modified) registers segmentation router
│   ├── requirements.txt                 — (modified) added scikit-learn, numpy
│   └── exports/segmentation/            — JSON output files (Docker volume)
│       ├── cluster_summary.json         — generated by run_clustering()
│       └── clustered_leads.json         — generated by run_clustering()
│
└── frontend/
    ├── .env                             — VITE_ETL_API_URL=http://localhost:8001
    └── src/
        ├── services/
        │   └── segmentation.js          — ★ axios ETL client + SEGMENT_META + formatRevenue
        ├── pages/
        │   └── manager/
        │       └── MarketAnalysisPage.vue — ★ main page, fetches data, renders all components
        ├── components/
        │   └── market/
        │       ├── MarketKPICards.vue         — 6 computed KPI stat cards
        │       ├── SegmentBubbleChart.vue     — pure SVG bubble visualization
        │       ├── SegmentCard.vue            — detailed segment profile card
        │       ├── SegmentComparisonCharts.vue — ApexCharts bar charts (CA + effectif)
        │       ├── SegmentRadarChart.vue      — ApexCharts radar (up to 3 segments)
        │       ├── OpportunityMatrix.vue      — ApexCharts scatter (volume vs value)
        │       ├── InsightsPanel.vue          — 6 strategic insight cards (static)
        │       └── LeadsExplorerTable.vue     — paginated + filterable leads table
        ├── router/index.js              — (modified) /manager/segmentation route (CEO)
        └── components/AppSidebar.vue    — (modified) added "Segmentation & Marché" nav item
```

---

## 11. API Contract

### `POST /segmentation/run`
```json
Response 200:
{
  "status": "ok",
  "run_at": "2026-04-18T01:00:00Z",
  "total_rows": 1054,
  "segments": [
    {
      "cluster": 1,
      "label": "Grands groupes matures",
      "color": "#303E8C",
      "recommendation": "Enterprise focus",
      "n": 395,
      "employes_moyen": 4468,
      "ca_moyen": 2919000000.0,
      "nb_locaux_moyen": 319.0,
      "age_moyen": 44.0,
      "categorie_dominante": "Grande Entreprise",
      "secteur_dominant": "Multi-sectoriel",
      "region_dominante": "Ile-de-France"
    }
    // ... 4 more segments
  ]
}
```

### `GET /segmentation/summary`
Same structure as the run response. Returns `404` if never run.

### `GET /segmentation/leads?segment=1&search=EDF&skip=0&limit=20`
```json
{
  "total": 395,
  "skip": 0,
  "limit": 20,
  "segment_label": "Grands groupes matures",
  "leads": [
    {
      "siren": "552081317",
      "nom_entreprise": "ELECTRICITE DE FRANCE",
      "ville": "PARIS",
      "secteur_activite": "Transport d'électricité",
      "categorie_entreprise": "Grande Entreprise",
      "tranche_effectif": "10000 salariés et plus",
      "chiffre_affaires": 118690000000.0,
      "age_entreprise": 71.0,
      "region": "Ile-de-France",
      "cluster": 1,
      "cluster_label": "Grands groupes matures"
    }
    // ...
  ]
}
```

---

## 12. How to Trigger & Test

### First time setup
```bash
# 1. Make sure VITE_ETL_API_URL is set
cat frontend/.env
# → VITE_ETL_API_URL=http://localhost:8001

# 2. Rebuild FastAPI image (scikit-learn is now in requirements.txt)
cd ETL_service
docker-compose up -d --build fastapi

# 3. Verify FastAPI is alive
curl http://localhost:8001/docs   # → FastAPI Swagger UI

# 4. Check that /segmentation/summary returns 404 (not run yet)
curl http://localhost:8001/segmentation/summary
# → {"detail": "No clustering results found..."}
```

### Running the clustering
```bash
# Via CLI
curl -X POST http://localhost:8001/segmentation/run

# Or via the UI: log in as CEO → /manager/segmentation → click "Relancer l'analyse"
```

### Verify the output files
```bash
docker-compose exec fastapi ls /opt/airflow/exports/segmentation/
# → cluster_summary.json  clustered_leads.json

docker-compose exec fastapi python -c "
import json
with open('/opt/airflow/exports/segmentation/cluster_summary.json') as f:
    d = json.load(f)
print(f'Total leads: {d[\"total_leads\"]}')
print(f'Segments: {[s[\"label\"] for s in d[\"segments\"]]}')
"
```

### Test CEO login
- **Email:** `ceo@qualifix.com`
- **Password:** `admin`
- Navigate to `http://localhost:5174/manager/segmentation`

---

## Key Design Decisions

| Decision | Reason |
|----------|--------|
| FastAPI, not Django, serves segmentation | Company data lives in ETL DB (Postgres/SQLAlchemy); Django has no access |
| JSON files, not DB tables | Fast reads, no schema migration, easy to inspect |
| Synchronous `/run` endpoint | 1000 rows clusters in <5s; no need for background tasks |
| `random_state=42` in KMeans | Ensures cluster 0–4 always map to the same business segments |
| ApexCharts (not ECharts) | `vue3-apexcharts` is already installed; `vue-echarts v8` needed global app.use() setup that was missing |
| Dynamic insights (v2) | Cluster labels are now dynamic → static insights would be wrong |
| Separate axios instance | ETL API is on a different origin, no Django auth/CSRF needed |

---

## v2 Upgrades — Model Validation

**File:** `ETL_service/ETL_pipeline/market_analysis/validation.py`

### Silhouette Score
After KMeans runs, `compute_validation()` computes `sklearn.metrics.silhouette_score(X, labels)`:

| Score | Interpretation |
|-------|----------------|
| ≥ 0.5 | Excellent — clusters very cohesive |
| ≥ 0.3 | Acceptable — identifiable structure |
| ≥ 0.1 | Weak — partial overlap |
| < 0.1 | Poor — clusters not distinct |

### Elbow Curve
Runs KMeans for K = 2 → 10, records **inertia (WCSS)** at each step. Then applies the **Kneedle algorithm** (normalise both axes, pick point with max perpendicular distance from first→last line) to auto-select the optimal K.

Stored in JSON:
```json
"elbow": {
  "k_values": [2, 3, 4, 5, 6, 7, 8, 9, 10],
  "inertias": [2100.2, 1750.4, ...],
  "best_k": 5
}
```

The silhouette score appears in the **header bar** of the Vue page as a colored badge (green ≥ 0.5, amber ≥ 0.3, red < 0.3).

---

## v2 Upgrades — Cluster Explainability

**File:** `ETL_service/ETL_pipeline/market_analysis/explainability.py`

For each cluster, compares the cluster's mean on 4 features vs the **global dataset mean**:
- `nb_employes_mid` → Effectif moyen
- `chiffre_affaires` → CA réel
- `nb_locaux` → Nombre de sites
- `age_entreprise` → Ancienneté

**Algorithm:**
1. Compute `global_mean` and `global_std` for each feature
2. For each cluster: `cluster_mean`, `ratio = cluster_mean / global_mean`, `z_score = (cluster_mean - global_mean) / global_std`
3. Sort by `|z_score|` descending → top 3 = most differentiating features

Stored per segment in `cluster_summary.json`:
```json
"explainability": {
  "top_features": [
    {"feature": "nb_employes_mid", "direction": "above", "ratio": 14.3,
     "description": "Effectif moyen 14.3× supérieur à la moyenne globale"}
  ],
  "comparisons": {
    "chiffre_affaires": {"cluster_mean": 2.9e9, "global_mean": 3.2e8, "ratio": 9.1, "z_score": 3.4, "direction": "above"}
  }
}
```

---

## v2 Upgrades — Gemini LLM Insights

**File:** `ETL_service/ETL_pipeline/market_analysis/llm_service.py`

### Architecture
```
run_clustering() → generate_insights(segments, validation) → Gemini API
                                                             ↕ (if key missing or error)
                                                         fallback (6 static rules)
```

### Prompt Strategy
The prompt sends:
- Each segment's label, lead count, CA moyen, effectif, age, region, secteur
- Silhouette score + elbow best_k
- Instructions to generate **6 insights in French**, covering revenue opportunity, segmentation quality, sales strategy, automation, geographic risk, and anomalies

### JSON Output Mode
Uses `generation_config=GenerationConfig(response_mime_type="application/json")` to force structured output from Gemini 1.5 Flash — no prompt-injection risk.

### Fallback Chain
1. **GEMINI_API_KEY set + library installed** → Gemini call
2. **Call fails** (timeout, quota, etc.) → 6 rule-based fallback insights
3. **Library not installed** → 6 rule-based fallback insights

The Vue badge shows `✦ Gemini AI` if `source === "gemini-1.5-flash"`, otherwise `Analyse basée sur les données`.

### Configuration
```bash
# ETL_service/.env
GEMINI_API_KEY=your-key-here

# Get a free key at:
# https://aistudio.google.com/app/apikey
```

---

## v2 Upgrades — Versioning

### Files written per run
```
/opt/airflow/exports/segmentation/
├── cluster_summary.json              ← always latest (overwritten)
├── cluster_summary_20260418_2100.json ← versioned (never overwritten)
├── clustered_leads.json              ← always latest
├── clustered_leads_20260418_2100.json ← versioned
├── cluster_insights.json             ← always latest
└── cluster_insights_20260418_2100.json ← versioned
```

The timestamp format is `YYYYMMDD_HHMM` (UTC). All versioned files are safe to archive or compare across runs. The `cluster_summary.json` always contains `run_at` and `k_used` as metadata.

---

## v2 Upgrades — Dynamic Segment Labeling

**File:** `ETL_service/ETL_pipeline/market_analysis/labeling.py`

Replaces the old fixed `SEGMENT_LABELS = {0: ..., 1: ...}` dictionary.

**Rule tree** (based on percentile position in full dataset):

```
CA ≥ p66 OR employees ≥ p66:
  age ≥ p50 → "Grands groupes matures"
  age < p50 → "Grands groupes croissants"
CA ≥ p33 OR employees ≥ p33:
  age ≥ p50 → "ETI établies diversifiées"
  age < p50 → "ETI en développement"
Low size:
  employees ≥ p33*0.5 AND ca ≥ p33*0.3 → "PME spécialisées"
  mature → "Microentreprises historiques"
  else → "Petites structures actives"
```

Each label has a paired recommendation (e.g., `"ETI établies diversifiées"` → `"Relationship selling — account-based marketing"`). Colors are assigned by position index from a fixed 10-color palette, ensuring visual distinction.

**Why this is better:** Labels adapt automatically when the dataset distribution changes (new ETL runs bring in more data). The fixed mapping would misclassify clusters if their composition shifts.


---

## v3 UX Improvements — Segment Naming

### Problem with previous approach

Before this fix, when multiple clusters received the same base label, the system appended parenthetical qualifiers directly into `label`:
```
"Grands groupes matures (Grand)"
"Grands groupes matures (Moyen)"
"Grands groupes matures (Émergent)"
```
For a CEO this is noisy, hard to scan, and meaningless on small screens.

### New label hierarchy

The labeling produces **two separate fields** per segment:

| Field | Example | Where it appears |
|-------|---------|-----------------|
| `label` / `label_short` | `"Grands groupes"` | Card title, badge, chart axis, bubble |
| `label_sub` | `"Segment élevé"` | Small colored pill under title, filter dropdown |

**Before → After:**
```
Before: "Grands groupes matures (Grand)"

After:
  Title:    Grands groupes
  Sub-pill: [Segment élevé]
```

### How collision resolution works

**Pass 1** — short label from CA + employee percentiles:
```
CA or employees ≥ p66  → "Grands groupes"
CA or employees ≥ p33  → "ETI"
small but notable      → "PME"
old & tiny             → "Microentreprises"
default                → "Petites structures"
```

**Pass 2** — if two clusters share the same primary label, rank by CA and assign `label_sub`:
```
Rank 1 (highest CA) → "Segment élevé"
Rank 2              → "Segment intermédiaire"
Rank 3              → "Segment émergent"
```
`label` is **never** modified in Pass 2 — the CEO always reads a clean, short primary word.

---

## v3 UX Improvements — Bubble Chart Layout

### Problem

The original chart used a **hardcoded `POSITIONS` array** of 5 fixed coordinates. When bubble radii grew large, bubbles overlapped. It also broke with < 5 or > 5 segments.

### New layout: spiral non-overlapping placement

**Algorithm (pure JavaScript, no D3):**

1. Sort segments by count descending — largest goes first.
2. Place the largest at the viewport **centre** (`W/2, H/2`).
3. For each remaining segment, run a **spiral search**:
   - Start at distance = `r_largest + r_current + GAP` from centre
   - Step outward by 1.5 SVG units per ring
   - Try 24 candidate angles (0°–345° in 15° steps)
   - Accept first candidate that: (a) does not overlap any placed bubble, (b) stays within viewport bounds
4. Fallback: stack to the right if no valid position was found.

**GAP** = 1.8 SVG units — enough breathing room without wasting space.

### Label placement rule

- `r ≥ 9` → label rendered **inside** the bubble as `<text>` element
- `r < 9` → label rendered **outside** with a dashed connector line from the bubble edge

---

## Beginner Explanation — How the Whole System Works

> Written for someone who has never used machine learning.

### What is the goal?

You have 1064 companies. You want to understand them in groups instead of row by row. An ML algorithm finds the natural groups automatically — we just name them.

### Data flow

```
[PostgreSQL]  →  [Python clustering]  →  [5 Groups]  →  [Labels]  →  [JSON files]
                                                                           ↓
                                           [CEO Dashboard] ← Vue reads JSON via FastAPI
```

### What is clustering?

Think of sorting fruits by look and taste — apples together, bananas together, lemons together.

KMeans does exactly that with numbers:
1. Pick 5 random centre points
2. Assign every company to the nearest centre
3. Recalculate each centre as the group average
4. Repeat until stable

Result: 5 stable groups where companies inside each group are similar to each other.

### What are features?

Features are the numbers we feed to the algorithm:

| Feature | Raw | Transformed | Why |
|---------|-----|-------------|-----|
| Revenue | 2.9b€ | log(2.9b) | Compress huge numbers |
| Employees | "10000+" | 15000 | Text → number |
| Age | founded 1946 | 80 years | Meaningful metric |
| Location | postcode | Region (5 zones) | Group 96 departments |
| Sector | text | 0/1 columns | Text → number |

All features are then **normalised** (StandardScaler) so no single feature dominates.

### Worked example

```
Company A: Revenue=2.9Md€, Employees=15000, Age=44, Region=IdF
→ Algorithm: "closest to cluster 1 centre"
→ Cluster 1 stats: large, mature, Paris-heavy
→ Label assigned: "Grands groupes"

Company B: Revenue=150k€, Employees=8, Age=3, Region=Bretagne
→ Algorithm: "closest to cluster 0 centre"
→ Cluster 0 stats: tiny, young
→ Label assigned: "Petites structures"
```

### Why labels change between runs

Every run recalculates **percentile thresholds (p33, p66, p50)** on the current dataset. If the ETL pipeline imports 200 new large companies next month, the p66 threshold rises and some clusters that were "ETI" may now qualify as "Grands groupes". This is intentional — labels reflect your **real data distribution**, not a static assumption.

---

## Beginner Explanation — Cluster Explainability

### The question being answered

> "Why is Company X in 'Grands groupes' and not 'ETI'?"

### How it works – step by step

**1. Global average**
```
All 1064 companies → average revenue = €280M, average employees = 312
```

**2. Cluster average**
```
"Grands groupes" cluster → avg revenue = €2.9B, avg employees = 4468
```

**3. Ratio**
```
Revenue ratio  = 2.9B / 280M = 10.3×  → "10× above average"
Employee ratio = 4468 / 312  = 14.3×  → "14× above average"
```

**4. Z-score ranking**

Z-score = (cluster_mean − global_mean) / standard_deviation

The 3 features with the highest z-score are the "top differentiators" — what makes this cluster unique.

### Analogy

Your class of 30 students has average height 1.70m. One group of 5 has average height 1.95m.

- Ratio = 1.95 / 1.70 = 1.15×
- Z-score = high (they are noticeably taller)
- Conclusion: "Height" is this group's defining feature

The system applies the same logic to companies.

### What the CEO sees

Instead of just "Grands groupes — 408 leads", the CEO can read:

> *"This segment has 14× more employees and 10× higher revenue than the average company. They are mature (older than average) and concentrated in Île-de-France."*

This makes the segment **actionable** — no data scientist needed to interpret it.

---

## Digital Maturity Hybrid Model (v4)

> **Files added:**
> - `market_analysis/digital_maturity_baseline.py`
> - `market_analysis/digital_maturity_adjustment.py`
> - `market_analysis/digital_maturity.py`
> - `market_analysis/digital_maturity_llm.py`
>
> **Files modified:**
> - `market_analysis/clustering.py` — injects maturity after labeling
> - `apis/routers/segmentation.py` — maturity fields flow through automatically
> - `components/market/MaturityAnalysisSection.vue` — NEW Vue component
> - `components/market/SegmentCard.vue` — maturity block added
> - `components/market/OpportunityMatrix.vue` — gap-aware tooltip and markers
> - `components/market/LeadsExplorerTable.vue` — Maturité + Écart columns
> - `components/market/InsightsPanel.vue` — 3 maturity insights appended
> - `pages/manager/MarketAnalysisPage.vue` — MaturityAnalysisSection registered

---

### What is Digital Maturity?

Digital maturity measures **how far an organisation has progressed in adopting digital technologies** across 5 dimensions.

It answers the CEO question:
> "Which of my leads are ready to buy? Which ones still need to transform before they can become a client?"

A **low-maturity** lead has a high "digital gap" = a high transformation opportunity. That is your **priority target**.

---

### Beginner Flow (How a score is born)

```
┌─────────────────────────────────────────┐
│  Secteur dominant (from clustering)     │  ← "Transport d'électricité"
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│  BASELINE (deterministic)               │
│  digital_maturity_baseline.py           │
│                                         │
│  tech:    6.5  data:   5.5              │
│  process: 7.0  culture: 5.5  cx: 4.5   │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│  ADJUSTMENT (deterministic)             │
│  digital_maturity_adjustment.py         │
│                                         │
│  employes_moyen = 4468 → +0.8 tech      │
│  ca_moyen = 2.9 Md€   → +0.8 tech      │
│  nb_locaux = 319       → +0.8 process   │
│  Grande Entreprise     → +0.5 tech      │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│  FINAL SCORES per dimension             │
│  digital_maturity.py                    │
│                                         │
│  tech:    8.6  ← clamped to [0-10]      │
│  data:    6.9                           │
│  process: 8.3                           │
│  culture: 5.5                           │
│  cx:      4.5                           │
│                                         │
│  global = mean(5 dims) = 6.8            │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│  LEVEL + GAP                            │
│                                         │
│  Level: "Moyen" (5.0 ≤ 6.8 < 8.0)      │
│  digital_gap = 10 - 6.8 = 3.2          │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│  LLM EXPLANATION (optional)             │
│  digital_maturity_llm.py               │
│                                         │
│  description: "..."                     │
│  strengths: ["...", "..."]              │
│  weaknesses: ["...", "..."]             │
│  opportunity: "..."                     │
│  recommended_pitch: "..."               │
│                                         │
│  ⚠ Gemini NEVER sets the score          │
│  ⚠ calibration bounded to ±0.5          │
│  ⚠ disabled by default                  │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│  DASHBOARD                              │
│  MaturityAnalysisSection.vue            │
│  SegmentCard.vue (badge + reasons)      │
│  OpportunityMatrix.vue (gap border)     │
│  LeadsExplorerTable.vue (2 columns)     │
│  InsightsPanel.vue (3 maturity cards)   │
└─────────────────────────────────────────┘
```

---

### Layer 1 — Sector Baseline

**File:** `market_analysis/digital_maturity_baseline.py`

Maps a sector string to 5 dimension scores using a keyword substring match.
~40 French B2B sectors covered. Unknown sector → all 5.0 (neutral).

```python
from market_analysis.digital_maturity_baseline import get_sector_baseline

get_sector_baseline("Transport d'électricité")
# → {"tech": 6.5, "data": 5.5, "process": 7.0, "culture": 5.5, "cx": 4.5}

get_sector_baseline("Banque")
# → {"tech": 8.0, "data": 8.0, "process": 7.5, "culture": 7.0, "cx": 8.0}

get_sector_baseline("Secteur inconnu")
# → {"tech": 5.0, "data": 5.0, "process": 5.0, "culture": 5.0, "cx": 5.0}
```

**Why sector matters:** A fintech company is structurally more digital than a construction firm — the baseline captures this structural expectation before looking at any company-specific data.

---

### Layer 2 — Internal Data Adjustment

**File:** `market_analysis/digital_maturity_adjustment.py`

Computes per-dimension deltas using the cluster's aggregate fields.

| Signal | Rule | Delta example |
|---|---|---|
| `employes_moyen ≥ 1000` | Large org = structured IT | +0.8 tech, +0.7 process |
| `ca_moyen ≥ 1 Md€` | Budget for digital investment | +0.8 tech, +0.7 data |
| `nb_locaux_moyen ≥ 50` | Multi-site = central IT needed | +0.8 process |
| `age_moyen ≤ 10 ans` | Digital-native startup culture | +0.6 culture |
| `categorie = Grande Entreprise` | Formal IT governance | +0.5 tech, +0.4 data |
| Data completeness | 4 fields filled → structured data | +0.6 data max |

All deltas are bounded per rule (`max ±1.0`) and per dimension total (`max ±2.5`).

Human-readable reasons are stored and displayed in the SegmentCard:
```
→ Effectif très élevé (4468 salariés) → +tech +process +data
→ CA très élevé (2.9 Md€) → fort investissement digital → +tech +data
→ Organisation multi-sites (319 locaux) → systèmes centralisés → +process +tech
```

---

### Layer 3 — Final Score

**File:** `market_analysis/digital_maturity.py`

```python
dim_scores[dim] = clamp(baseline[dim] + adjustment[dim], 0, 10)
global_score    = mean(dim_scores.values())  # 1 decimal
```

**Level mapping:**

| Score | Level | What it means |
|---|---|---|
| ≥ 8.0 | Élevé | Already digitally advanced |
| ≥ 5.0 | Moyen | Partially transformed |
| < 5.0 | Faible | Early stage, high opportunity |

**Gap:** `digital_gap = 10 - global_score`
High gap = transformation opportunity. This is what the CEO uses to prioritise.

**Stage labels** (internal, extended view):
Optimisé → Avancé → En développement → Initial → Absent

---

### Layer 4 — LLM Explanation (Gemini)

**File:** `market_analysis/digital_maturity_llm.py`

```
MATURITY_LLM_CALIBRATION=false  (default — calibration OFF)
GEMINI_API_KEY=...              (from ETL_service/.env)
```

Gemini generates a **structured JSON explanation** per segment:
- `description` — 2–3 sentences for the CEO
- `strengths` — 2 digital strengths observed
- `weaknesses` — 2 digital blockers
- `opportunity` — 1-line transformation opportunity
- `recommended_pitch` — the commercial pitch adapted to maturity level

Gemini **NEVER generates or overrides the numeric score**.

Optional bounded calibration (`MATURITY_LLM_CALIBRATION=true`):
- Max allowed delta: `±0.5`
- Used only when LLM identifies strong sector context not captured by internal data
- Must be explicitly enabled — disabled by default to preserve determinism

Full rule-based fallback when Gemini is unavailable (no key, timeout, quota).

---

### JSON Schema Changes

#### `cluster_summary.json` — each segment now includes:

```json
{
  "cluster": 1,
  "label": "Grands groupes",
  "digital_maturity_score": 6.8,
  "digital_maturity_level": "Moyen",
  "digital_gap": 3.2,
  "maturity_details": {
    "dimensions": {
      "tech": 8.6,
      "data": 6.9,
      "process": 8.3,
      "culture": 5.5,
      "cx": 4.5
    },
    "maturity_distribution": { "faible": 18, "moyen": 52, "eleve": 30 },
    "adjustment_reasons": [
      "Effectif très élevé (4468 salariés) → +tech +process +data",
      "CA très élevé (2.9 Md€) → fort investissement digital → +tech +data",
      "Organisation multi-sites (319 locaux) → systèmes centralisés → +process"
    ],
    "maturity_stage": "En développement"
  },
  "llm_analysis": {
    "description": "Le segment Grands groupes affiche un niveau de maturité digitale de 6.8/10...",
    "strengths": ["Infrastructure IT consolidée", "Processus métier largement digitalisés"],
    "weaknesses": ["Dette technique sur systèmes anciens", "Résistance culturelle au changement"],
    "opportunity": "Cibler les offres d'IA et d'automatisation avancée.",
    "recommended_pitch": "Positionnez-vous en partenaire d'optimisation...",
    "score_calibration": 0.0
  }
}
```

#### `cluster_summary.json` — top level now includes:

```json
{
  "maturity_overview": {
    "avg_maturity": 6.2,
    "avg_gap": 3.8,
    "distribution": { "Faible": 1, "Moyen": 3, "Élevé": 1 }
  }
}
```

#### `clustered_leads.json` — each lead now includes:

```json
{
  "siren": "552081317",
  "nom_entreprise": "ELECTRICITE DE FRANCE",
  "digital_maturity_score": 7.1,
  "digital_maturity_level": "Moyen",
  "digital_gap": 2.9
}
```
*(Score is segment-level score + small deterministic jitter, seeded by SIREN)*

---

### UI Integration

The maturity layer is integrated into the Vue dashboard **without redesigning** any existing component.

#### Page hierarchy (unchanged):
```
KPI cards
  → Bubble chart (segments overview)
    → Segment profile cards  [NEW: maturity badge + gap + reasons in each card]
      → Maturity Analysis section  [NEW component: distribution bars + top-3]
        → Comparison bar charts
          → Radar + Opportunity Matrix  [UPGRADED: gap-width borders on bubbles]
            → Strategic insights  [UPGRADED: 3 maturity insights appended]
              → Leads table  [UPGRADED: Maturité + Écart columns at lg+]
```

#### New component: `MaturityAnalysisSection.vue`

Adapted from the React reference `MaturityAnalysisSection.tsx` (see below).

**Left panel (5/8 columns):** Stacked distribution bars per segment
- Segment name + level badge + score/10
- Stacked bar: amber (Faible) · blue (Moyen) · green (Élevé)
- Bottom: "Segment à fort potentiel" alert strip

**Right panel (3/8 columns):** Top-3 transformation opportunities
- Ranked by composite score: gap × volume × value
- Gap progress bar with Fort/Modéré/Faible label

---

### React Reference → Vue Adaptation Note

The folder `pfe-prospection-client/react/` contains a UI reference built in **React TypeScript**:
- `react/components/MaturityAnalysisSection.tsx`
- `react/pages/MarketAnalysisPage (1).tsx`
- `react/lib/segments-data (1).ts`

This React code was used **exclusively as a design reference** and **is NOT executed at runtime**.

**What was taken from the React reference:**
- Two-panel layout (distribution stacked bars + top-3 opportunities)
- Top-3 ranking formula: `gap × volume × value`
- Gap label system (Fort / Modéré / Faible)
- Section placement (between Segment Cards and Comparison Charts)

**What was adapted for Vue:**
- Removed all React hooks (`useMemo`, `useState`) → Vue `computed()`
- Removed all TypeScript types → plain JavaScript props
- Replaced Tailwind HSL custom vars (`tacir-yellow`, `tacir-blue`, `tacir-green`) → existing Vue class system
- Score scale changed from **0–100** (React mock) to **0–10** (real API)
- `digitalGap` interpretation changed: React used `sectorPotential - maturityScore` (raw 0–40); Vue uses `10 - global_score` (bounded 0–10)
- All data now comes from live FastAPI → no static mock data
- Component is integrated into the existing `v-if="summary"` block

**Why the React code is not used in production:**
The existing frontend is Vue 3. Embedding a React component would require a separate React root, Shadow DOM isolation, and bundle duplication — introducing fragility and maintenance overhead with no benefit. The Vue implementation is functionally equivalent and visually consistent with the existing tacir design system.

---

### Example Output

**CEO view for "PME énergie" segment (gap = 3.8/10):**

```
┌──────────────────────────────────────────────┐
│ PME énergie                              C0  │
│ 46 leads · 12% du portefeuille               │
│                                              │
│ CA moyen: 182 M€  Effectif: 163  Âge: 18 ans│
│ Catégorie: PME                               │
│ [Vertical niche — offre sectorielle dédiée]  │
│                                              │
│ ── Maturité ────────────────────────────────│
│ Maturité [Moyen]   Score: 6.2/10  Écart: 3.8│
│ → CA significatif (182 M€) → +tech +data    │
│ → Entreprise récente (18 ans) → +culture    │
│ → PME — infrastructure IT partielle         │
└──────────────────────────────────────────────┘
```

**MaturityAnalysisSection bar (same segment):**
```
PME énergie  [Moyen]           6.2/10
[████████████████░░░░░░░░░░░░░░░░░░░]
 Faible: 22%   Moyen: 54%   Élevé: 24%
```

**OpportunityMatrix tooltip (same segment):**
```
PME énergie
Leads: 46
CA moy: 182 M€
Âge: 18 ans
─────────────────
Maturité: 6.2/10 · Écart: 3.8  ○ Potentiel modéré
```

**InsightsPanel (maturity insight, auto-generated):**
```
[📈 Priorité haute]
Plus grand potentiel de transformation : PME énergie
Écart numérique de 3.8/10 — combinant un volume de leads
élevé et une maturité encore faible. Priorité d'investissement
commercial immédiate.
```

---

### Configuration Reference

| Env variable | Default | Description |
|---|---|---|
| `GEMINI_API_KEY` | *(empty)* | Enables Gemini calls for both strategic insights and maturity explanations |
| `MATURITY_LLM_CALIBRATION` | `false` | Enables optional bounded score calibration by LLM (max ±0.5) |
| `SEGMENTATION_EXPORT_DIR` | `/opt/airflow/exports/segmentation` | Export directory for all JSON outputs |

---

### Notes for Developers

1. **Maturity is always computed** — even if Gemini key is missing. Only the `llm_analysis` text fields degrade to rule-based fallback.
2. **Re-run required** — existing `cluster_summary.json` files do not have maturity fields. Run `POST /segmentation/run` once after deploying to backfill.
3. **Per-lead scores** use deterministic jitter seeded by SIREN — same SIREN always gets the same jitter offset, making results consistent across pagination.
4. **No new database tables** — all maturity data is stored in the existing JSON export files.
5. **Zero breaking changes** — all existing component props are unchanged; maturity fields are additive.
