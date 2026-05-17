# Segmentation API and Data Contracts

## Service base URL

The frontend calls the ETL FastAPI service, not Django.

Local defaults:

- frontend route: `http://localhost:5174/manager/segmentation`
- ETL API base: `http://localhost:8001`

Frontend config source:

- `frontend/src/services/segmentation.js`
- env var: `VITE_ETL_API_URL`

## Endpoint summary

| Method | URL | Purpose |
|---|---|---|
| `POST` | `/segmentation/run` | run the full batch segmentation pipeline and return the new summary |
| `GET` | `/segmentation/summary` | return the latest `cluster_summary.json` |
| `GET` | `/segmentation/leads` | return paginated, optionally filtered rows from `clustered_leads.json` |
| `GET` | `/segmentation/validation` | return the `validation` block from the latest summary |

## POST /segmentation/run

Runs the full segmentation pipeline:

```text
fetch DB rows
-> preprocess
-> rule labeling
-> decision tree training
-> prediction
-> validation
-> explainability
-> digital maturity
-> insights
-> JSON exports
-> summary response
```

### Request

- method: `POST`
- body: none
- query params: none

### Success response

Returns the same payload written to `cluster_summary.json`.

Top-level fields:

- `status`
- `run_at`
- `model_type`
- `k_used`
- `total_rows`
- `total_leads`
- `validation`
- `segments`
- `insights`
- `insights_source`
- `maturity_overview`
- `tree_rules`
- `training_accuracy`

### Example

```json
{
  "status": "ok",
  "run_at": "2026-05-12T19:42:01.123456Z",
  "model_type": "decision_tree",
  "k_used": 6,
  "total_rows": 1244,
  "total_leads": 1231,
  "validation": {
    "model_type": "decision_tree",
    "training_accuracy": 0.9412,
    "tree_depth": 3,
    "n_leaves": 7,
    "silhouette": null,
    "elbow": null
  },
  "segments": [
    {
      "cluster": 0,
      "segment_code": "PME_Small_IT",
      "label": "PME technologiques",
      "label_short": "PME",
      "label_sub": "Petits acteurs IT",
      "n": 143
    }
  ],
  "insights": [],
  "insights_source": "rule-based-fallback",
  "maturity_overview": {
    "avg_maturity": 6.1,
    "avg_gap": 3.9,
    "distribution": {
      "Faible": 1,
      "Moyen": 4,
      "Eleve": 1
    }
  }
}
```

### Error cases

| HTTP code | Condition |
|---|---|
| `400` | no data in `entreprise`, no rows could be prepared, or not enough labeled rows to train |
| `500` | unhandled runtime error inside the pipeline |

Current implementation note:

- `500.detail` includes the traceback text

## GET /segmentation/summary

Returns the latest summary file from disk.

### Request

- method: `GET`
- query params: none

### Behavior details

- reads `cluster_summary.json`
- repairs text through `repair_text_payload()`
- if `summary.insights` is empty and `cluster_insights.json` exists, it backfills insights from that file
- fills backward-compat defaults for:
  - `status`
  - `model_type`
  - `total_rows`

### Success response

Same schema as `POST /segmentation/run`.

### Error cases

| HTTP code | Condition |
|---|---|
| `404` | no segmentation export exists yet |

## GET /segmentation/leads

Returns paginated rows from `clustered_leads.json`.

### Request

- method: `GET`

### Query parameters

| Param | Type | Default | Meaning |
|---|---|---:|---|
| `segment` | integer | none | filter by numeric cluster id |
| `search` | string | none | case-insensitive substring match on `nom_entreprise` |
| `skip` | integer | `0` | zero-based offset |
| `limit` | integer | `20` | page size |

### Response shape

- `total`
- `skip`
- `limit`
- `segment_label`
- `leads`

### Example

```json
{
  "total": 143,
  "skip": 0,
  "limit": 20,
  "segment_label": "PME technologiques",
  "leads": [
    {
      "siren": "123456789",
      "nom_entreprise": "Example SAS",
      "ville": "Paris",
      "secteur_activite": "62.02A",
      "categorie_entreprise": "Petite et Moyenne Entreprise",
      "tranche_effectif": "10 a 19 salaries",
      "chiffre_affaires": 4200000.0,
      "age_entreprise": 8.4,
      "region": "Ile-de-France",
      "cluster": 0,
      "cluster_label": "PME technologiques",
      "cluster_color": "#04ADBF",
      "macro_sector": "IT",
      "ca_band": "Small",
      "decision_tree_confidence": 0.9721,
      "segment_rule": "PME_Small_IT",
      "digital_maturity_score": 6.2,
      "digital_maturity_level": "Moyen",
      "digital_gap": 3.8
    }
  ]
}
```

### Error cases

| HTTP code | Condition |
|---|---|
| `404` | no `clustered_leads.json` exists yet |

### Implementation note

Filtering is done in Python after loading the full JSON file into memory.
This is simple and fine for current data volumes, but it is not a database-backed pagination strategy.

## GET /segmentation/validation

Returns the `validation` block extracted from the latest summary.

### Request

- method: `GET`
- query params: none

### Response shape

- `run_at`
- `k_used`
- `model_type`
- `validation`

### Example

```json
{
  "run_at": "2026-05-12T19:42:01.123456Z",
  "k_used": 6,
  "model_type": "decision_tree",
  "validation": {
    "training_accuracy": 0.9412,
    "tree_depth": 3,
    "n_leaves": 7,
    "classification_report": {},
    "confusion_matrix": {
      "labels": ["ETI_IT", "ETI_Large"],
      "matrix": [[10, 0], [0, 12]]
    },
    "tree_rules": "|--- CA (EUR) <= ..."
  }
}
```

### Error cases

| HTTP code | Condition |
|---|---|
| `404` | no summary exists yet |
| `404` | summary exists but `validation` block is missing |

## JSON export contracts

## cluster_summary.json

Top-level contract:

| Field | Type | Notes |
|---|---|---|
| `status` | string | usually `ok` |
| `run_at` | ISO datetime string | export time |
| `model_type` | string | currently `decision_tree` |
| `k_used` | integer | number of active segments in this run |
| `total_rows` | integer | rows loaded from DB before cleaning/dedup |
| `total_leads` | integer | rows kept in the working DataFrame |
| `validation` | object | model validation payload |
| `segments` | array | segment cards and drilldowns |
| `insights` | array | strategic insight cards |
| `insights_source` | string | `gemini-1.5-flash`, `rule-based-fallback`, or empty |
| `maturity_overview` | object | portfolio maturity summary |
| `tree_rules` | string | convenience copy of `validation.tree_rules` |
| `training_accuracy` | number | convenience copy of `validation.training_accuracy` |

### Segment object contract

| Field | Type | Notes |
|---|---|---|
| `cluster` | integer | frontend-compatible numeric id |
| `segment_code` | string | internal business code |
| `label` | string | business label |
| `label_short` | string | grouped label used in charts |
| `label_sub` | string | sub-segment qualifier |
| `color` | string | hex color |
| `recommendation` | string | business recommendation |
| `n` | integer | company count |
| `employes_moyen` | integer | rounded mean employee midpoint |
| `ca_moyen` | number or null | mean revenue |
| `nb_locaux_moyen` | number or null | mean locations |
| `age_moyen` | number or null | mean age in years |
| `categorie_dominante` | string | mode of normalized category |
| `secteur_dominant` | string | mode of raw sector label |
| `region_dominante` | string | mode of derived region |
| `macro_sector_dominant` | string | mode of macro sector |
| `decision_tree_confidence_mean` | number or null | mean confidence |
| `explainability` | object | segment-vs-global differentiators |
| `digital_maturity_score` | number | `0..10` |
| `digital_maturity_level` | string | `Faible`, `Moyen`, or `Eleve` in repaired UI text |
| `digital_gap` | number | `10 - score` |
| `maturity_details` | object | dimensions, distribution, reasons, stage |
| `llm_analysis` | object | description, strengths, weaknesses, opportunity, recommended pitch, score calibration |
| `drilldown` | object | statistical deep-dive used by the drawer |

### Explainability contract

| Field | Type | Notes |
|---|---|---|
| `top_features` | array | top 3 differentiators by absolute z-score |
| `comparisons` | object | per-feature global comparison |

`top_features[]` item:

- `feature`
- `direction`
- `ratio`
- `description`

`comparisons.<feature>` object:

- `cluster_mean`
- `global_mean`
- `ratio`
- `z_score`
- `direction`

### Maturity details contract

| Field | Type | Notes |
|---|---|---|
| `dimensions` | object | `tech`, `data`, `process`, `culture`, `cx` |
| `maturity_distribution` | object | `faible`, `moyen`, `eleve` percentages |
| `adjustment_reasons` | array of strings | human-readable rule explanations |
| `maturity_stage` | string | `Optimise`, `Avance`, `En developpement`, `Initial`, `Absent` |

### Drilldown contract

| Field | Type | Notes |
|---|---|---|
| `summary_stats` | object | mean, median, min, max, std-like stats by metric |
| `dominant_dimensions` | object | dominant category, sector, region |
| `extremes` | object | highest/lowest CA, effectif, youngest/oldest company |
| `representative_companies` | array | 5 most representative rows |
| `top_lists` | object | ranked subsets such as top CA |
| `global_comparison` | object | delta vs portfolio mean |
| `homogeneity` | object | coefficients of variation and warning |

## clustered_leads.json

Each item is a JSON-ready company row with segmentation and maturity enrichments.

Core fields:

- `siren`
- `nom_entreprise`
- `ville`
- `secteur_activite`
- `categorie_entreprise`
- `tranche_effectif`
- `chiffre_affaires`
- `age_entreprise`
- `region`
- `cluster`
- `cluster_label`
- `cluster_color`
- `macro_sector`
- `ca_band`
- `decision_tree_confidence`
- `segment_rule`
- `digital_maturity_score`
- `digital_maturity_level`
- `digital_gap`

## cluster_insights.json

Top-level fields:

- `generated_at`
- `source`
- `insights`

Each insight item:

- `title`
- `description`
- `priority`
- `icon`

## maturity/maturity_analysis_c{cluster}_{timestamp}.json

Top-level fields:

- `generated_at`
- `source`
- `cluster`
- `analysis`

`analysis` contains:

- `description`
- `strengths`
- `weaknesses`
- `opportunity`
- `recommended_pitch`
- `score_calibration`

## Run and test guide

## Start the stack

From the repository root:

```bash
docker compose up -d
```

Relevant services:

- `etl-fastapi`
- `airflow-apiserver`
- `airflow-scheduler`
- `airflow-worker`
- `etl-bootstrap`
- `frontend`

## Verify ETL data exists

Check ETL readiness:

```bash
curl http://localhost:8001/etl/status
```

If `initial_load_required` is `true`, either:

- wait for `etl-bootstrap` to finish its automatic first-load behavior
- or trigger manually:

```bash
curl -X POST "http://localhost:8001/etl/trigger-initial-load"
```

## Trigger segmentation

```bash
curl -X POST http://localhost:8001/segmentation/run
```

## Read the latest summary

```bash
curl http://localhost:8001/segmentation/summary
```

## Read a filtered lead page

```bash
curl "http://localhost:8001/segmentation/leads?segment=0&skip=0&limit=20"
curl "http://localhost:8001/segmentation/leads?search=paris&limit=10"
```

## Read validation only

```bash
curl http://localhost:8001/segmentation/validation
```

## Verify export files

Inside the ETL export directory, check for:

- `cluster_summary.json`
- `clustered_leads.json`
- `cluster_insights.json`
- timestamped variants

In Docker, they live under:

- `/opt/airflow/exports/segmentation`

## Test the frontend page

Open:

- `http://localhost:5174/manager/segmentation`

Expected behavior:

- summary loads on page mount if exports already exist
- clicking `Relancer l'analyse` re-runs the backend batch and refreshes the dashboard
- the drilldown drawer opens from a segment card without another HTTP call
- the lead table issues its own paginated `GET /segmentation/leads` requests

## Common errors and fixes

| Symptom | Likely cause | Fix |
|---|---|---|
| `POST /segmentation/run` returns `No data in entreprise table` | ETL has not populated `entreprise` yet | run or inspect ETL readiness and Airflow DAGs |
| `summary` returns `404` | segmentation has never been run | call `POST /segmentation/run` |
| frontend shows ETL connection error | `etl-fastapi` not running or `VITE_ETL_API_URL` wrong | check container health and env |
| insights are empty or fallback-based | `GEMINI_API_KEY` missing or Gemini call failed | inspect ETL logs; fallback is expected behavior |
| maturity explanation exists but score did not change | current pipeline does not apply LLM calibration back into numeric maturity | expected behavior |
| lead table filters feel slow on very large exports | filtering is done in memory on JSON file | expected limitation of current design |
