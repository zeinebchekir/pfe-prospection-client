# Segmentation & Market Analysis

This document is the main entry point for the Segmentation & Market Analysis feature.
It was rewritten against the current repository code, not against historical design notes.

Verified code paths:

- `ETL_service/ETL_pipeline/market_analysis/*`
- `ETL_service/ETL_pipeline/apis/routers/segmentation.py`
- `ETL_service/dags/dag_initial_load.py`
- `frontend/src/pages/manager/MarketAnalysisPage.vue`
- `frontend/src/components/market/*`
- `frontend/src/services/segmentation.js`
- `frontend/src/router/index.js`

## Feature overview

The feature turns the current ETL `entreprise` dataset into a CEO-only segmentation dashboard.
It does not score one lead at a time on demand. Instead, it runs a batch analysis over the full ETL company table, assigns each company to a business segment, computes explainability and digital maturity enrichments, exports JSON files, and serves those files back to the Vue dashboard.

Business purpose:

- give management a portfolio-level view instead of raw lead rows
- group companies into sales-operable segment families
- highlight digital transformation potential
- expose an executive summary, drilldowns, and a paginated lead explorer

Current user-facing entry point:

- role: `CEO`
- route: `/manager/segmentation`
- data service: ETL FastAPI on `VITE_ETL_API_URL` / port `8001` in local Docker

Main outputs:

- `cluster_summary.json`
- `clustered_leads.json`
- `cluster_insights.json`
- optional cached maturity analyses under `maturity/`

## Current model status

The production engine is now a decision-tree segmentation pipeline.
The old KMeans-based implementation is no longer the runtime path.

Important compatibility detail:

- the API and JSON still use the historical word `cluster`
- the runtime meaning is now `frontend-compatible numeric segment id`

This means a `cluster` value is no longer a pure unsupervised cluster index. It is the numeric id mapped from a decision-tree segment code such as `PME_Small_IT` or `GE_Large`.

## End-to-end flow

```text
DataGouv / BOAMP / Sirene
        |
        v
Airflow DAGs load cleaned companies into ETL table `entreprise`
        |
        v
POST /segmentation/run on ETL FastAPI
        |
        v
market_analysis.clustering.run_clustering()
        |
        v
decision_tree_segmentation.run_decision_tree_segmentation()
        |
        +-> preprocessing and rule-based label creation
        +-> shallow DecisionTreeClassifier training + prediction
        +-> validation
        +-> explainability
        +-> digital maturity
        +-> Gemini or fallback insights
        |
        v
latest + versioned JSON exports under /opt/airflow/exports/segmentation
        |
        +-> GET /segmentation/summary
        +-> GET /segmentation/leads
        +-> GET /segmentation/validation
        |
        v
frontend/src/services/segmentation.js
        |
        v
frontend/src/pages/manager/MarketAnalysisPage.vue
        |
        v
market dashboard components
```

## Documentation map

Read these in order if you are onboarding:

1. [docs/segmentation/ARCHITECTURE.md](docs/segmentation/ARCHITECTURE.md)
2. [docs/segmentation/DATA_PIPELINE.md](docs/segmentation/DATA_PIPELINE.md)
3. [docs/segmentation/API.md](docs/segmentation/API.md)
4. [docs/segmentation/FRONTEND.md](docs/segmentation/FRONTEND.md)
5. [docs/segmentation/DIGITAL_MATURITY.md](docs/segmentation/DIGITAL_MATURITY.md)

## What changed vs the old documentation

The previous markdown mixed two generations of the feature. The current codebase differs in several important ways:

- production segmentation uses `DecisionTreeClassifier`, not KMeans
- the active segment catalog supports up to 7 numeric ids, not a fixed 5 clusters
- `market_analysis/clustering.py` is now a compatibility wrapper
- `GET /segmentation/validation` exists and returns the latest validation block
- insights are no longer frontend-only static cards; the backend writes `cluster_insights.json`
- digital maturity is part of the exported summary and lead payloads
- the segment drilldown drawer is powered by embedded `segment.drilldown` data, not an extra API call

## Beginner-friendly walkthrough

### What happens when the CEO clicks "Relancer l'analyse"

1. The Vue page calls `POST /segmentation/run` through `frontend/src/services/segmentation.js`.
2. FastAPI reads every row from the ETL `entreprise` table.
3. The decision-tree pipeline cleans the data, creates features, predicts a segment for each company, computes enrichments, and writes JSON exports.
4. The same HTTP response returns the new summary payload, and the page re-renders immediately from that response.

### How a company becomes a segment

1. The pipeline loads raw company fields such as category, revenue, employee band, sector, postal code, age, and number of sites.
2. It normalizes those fields into model-ready features such as `macro_sector`, `ca_band`, `nb_employes_mid`, and `age_entreprise`.
3. A deterministic business rule assigns an intermediate segment code like `ETI_Large` or `PME_Small_NonIT`.
4. A shallow decision tree learns those rules from the rows that have a real revenue value.
5. The trained tree predicts a segment code for the full dataset and maps that code to a numeric `cluster` id for frontend compatibility.

### How maturity is computed

1. The dominant sector of each segment gets a 5-dimension maturity baseline.
2. Internal segment aggregates such as headcount, revenue, number of sites, company age, and legal category add bounded adjustments.
3. The five dimension scores are clamped to `0..10`, averaged into `digital_maturity_score`, mapped to a level, and converted into `digital_gap = 10 - score`.
4. Gemini may add textual analysis, but it does not currently override the numeric score.

### How the Vue page displays everything

1. `MarketAnalysisPage.vue` loads the latest summary on mount.
2. KPI cards, charts, maturity blocks, insights, and segment cards all render from `summary.segments`.
3. The drilldown drawer uses the precomputed `segment.drilldown` object already embedded in the summary.
4. The leads table makes its own paginated call to `GET /segmentation/leads`.

## Fast maintenance checklist

- change business segment rules: `ETL_service/ETL_pipeline/market_analysis/decision_tree_segmentation.py`
- change maturity baselines: `ETL_service/ETL_pipeline/market_analysis/digital_maturity_baseline.py`
- change maturity adjustment rules: `ETL_service/ETL_pipeline/market_analysis/digital_maturity_adjustment.py`
- change Gemini strategic insights prompt: `ETL_service/ETL_pipeline/market_analysis/llm_service.py`
- change Gemini maturity explanation prompt: `ETL_service/ETL_pipeline/market_analysis/digital_maturity_llm.py`
- change API behavior: `ETL_service/ETL_pipeline/apis/routers/segmentation.py`
- change dashboard orchestration: `frontend/src/pages/manager/MarketAnalysisPage.vue`
- change charts/cards/table rendering: `frontend/src/components/market/*`

## Historical artifacts still in the repo

These files are useful for history, experiments, or migration context, but they are not the active runtime path:

- `lead_clustering.py` - standalone KMeans-era script
- `ETL_service/ETL_pipeline/market_analysis/validation.py::compute_validation` - legacy KMeans validation helper
- `ETL_service/ETL_pipeline/market_analysis/labeling.py` - v3 labeling helper not imported by the current pipeline
- `DecisionTree_Restructured.ipynb` - notebook reference, not production code

## Related docs

- [Architecture](docs/segmentation/ARCHITECTURE.md)
- [Data pipeline and segmentation engine](docs/segmentation/DATA_PIPELINE.md)
- [API and data contracts](docs/segmentation/API.md)
- [Frontend dashboard](docs/segmentation/FRONTEND.md)
- [Digital maturity, explainability, and insights](docs/segmentation/DIGITAL_MATURITY.md)
