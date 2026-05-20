# Digital Maturity, Explainability, and Insights

## Overview

The segmentation feature adds three related enrichment layers after segment prediction:

1. deterministic digital maturity scoring
2. explainability for why a segment differs from the overall portfolio
3. strategic insights and maturity narratives, optionally generated with Gemini

These layers are all attached to the exported JSON and rendered in the frontend dashboard.

## Digital maturity architecture

The maturity computation is hybrid, but the numeric score is deterministic in the current pipeline.

```text
sector baseline
    + bounded internal adjustments
    = numeric maturity dimensions
    -> global maturity score
    -> maturity level
    -> digital gap
    -> maturity distribution + stage
    -> optional Gemini text explanation
```

Main files:

- `digital_maturity.py`
- `digital_maturity_baseline.py`
- `digital_maturity_adjustment.py`
- `digital_maturity_llm.py`

## Deterministic maturity score

### Baseline layer

Function:

- `get_sector_baseline(sector)`

Dimensions:

- `tech`
- `data`
- `process`
- `culture`
- `cx`

Lookup behavior:

- case-insensitive substring matching on the dominant raw sector string
- neutral fallback of `5.0` on all dimensions if nothing matches

Examples of covered sector families:

- energy and utilities
- transport and logistics
- public services
- wholesale and distribution
- retail
- industry and manufacturing
- construction and real estate
- financial services
- technology and IT
- professional services
- agriculture and food
- inspection and certification

### Internal adjustment layer

Function:

- `compute_adjustment(segment)`

Adjustment properties:

- additive per dimension
- single-rule cap: `+/- 1.0`
- per-dimension total cap: `+/- 2.5`

### Adjustment rules

| Signal | Thresholds | Main effect |
|---|---|---|
| average headcount | `>= 1000`, `>= 200`, `>= 50`, `< 10` | raises or lowers `tech`, `process`, sometimes `data` |
| average revenue | `>= 1e9`, `>= 1e8`, `>= 1e7`, `< 1e6` | raises or lowers `tech` and `data`, sometimes `process` |
| average sites | `>= 50`, `>= 10`, `>= 3` | raises `process`, sometimes `tech` |
| average age | `<= 10`, `<= 20`, `>= 40`, `>= 60` | shifts `culture` and `cx` |
| dominant category | GE, ETI, PME, TPE/micro patterns | nudges `tech`, `data`, `process` |
| data completeness | 4 aggregate fields present | adds up to `+0.6` on `data` |

The adjustment function also returns `reasons`, which are meant to be human-readable and CEO-friendly.

## Final maturity fields

Function:

- `compute_maturity(segment)`

Algorithm:

1. read sector baseline
2. compute bounded adjustments
3. add baseline + adjustment per dimension
4. clamp each dimension to `0..10`
5. compute global average score
6. derive level
7. compute `digital_gap = 10 - score`
8. infer maturity distribution from score spread
9. derive maturity stage

### Output fields added to each segment

| Field | Meaning |
|---|---|
| `digital_maturity_score` | global score `0..10`, rounded to 1 decimal |
| `digital_maturity_level` | `Faible`, `Moyen`, or `Eleve` after text repair |
| `digital_gap` | remaining distance to ideal score `10` |
| `maturity_details.dimensions` | `tech`, `data`, `process`, `culture`, `cx` |
| `maturity_details.maturity_distribution` | inferred `% faible / moyen / eleve` |
| `maturity_details.adjustment_reasons` | French explanation strings |
| `maturity_details.maturity_stage` | 5-stage label |

### Level thresholds

| Score | Level |
|---|---|
| `>= 8.0` | `Eleve` |
| `>= 5.0` | `Moyen` |
| `< 5.0` | `Faible` |

### Stage thresholds

| Score | Stage |
|---|---|
| `>= 9.0` | `Optimise` |
| `>= 7.5` | `Avance` |
| `>= 5.5` | `En developpement` |
| `>= 3.5` | `Initial` |
| `< 3.5` | `Absent` |

## Lead-level maturity

Function:

- `compute_lead_maturity(lead, segment_score, segment_level)`

The pipeline does not recompute full maturity per lead.
Instead it propagates the parent segment score with a deterministic Gaussian jitter.

Behavior:

- jitter source: hash derived from `siren`
- standard deviation: `0.4`
- result is clamped to `0..10`
- lead level is recomputed from the jittered score

Lead fields added:

- `digital_maturity_score`
- `digital_maturity_level`
- `digital_gap`

This makes lead rows feel less identical while staying anchored to the segment-level maturity.

## Gemini maturity explanation layer

Main function:

- `generate_all_maturity_analyses(segments, export_dir, timestamp)`

Per-segment function:

- `generate_maturity_analysis(segment, export_dir, timestamp)`

Gemini model currently used:

- `gemini-1.5-flash`

Expected LLM fields:

- `description`
- `strengths`
- `weaknesses`
- `opportunity`
- `recommended_pitch`
- `score_calibration`

### Important numeric constraint

The code explicitly documents that Gemini should not override the numeric maturity score.
That is true in the current runtime path:

- `compute_maturity()` sets the numeric fields first
- `generate_all_maturity_analyses()` only attaches `segment["llm_analysis"]`
- no later step feeds `llm_analysis.score_calibration` back into `digital_maturity_score`

So even when `MATURITY_LLM_CALIBRATION=true`:

- calibration is stored in `llm_analysis.score_calibration`
- the exported numeric maturity score does not change

### Fallback behavior

Gemini is used only when both are true:

- `google-genai` is installed
- `GEMINI_API_KEY` is present

Otherwise:

- `_rule_based_fallback()` generates deterministic maturity prose
- `score_calibration` is forced to `0.0`

### Cached maturity files

Path pattern:

- `maturity/maturity_analysis_c{cluster}_{timestamp}.json`

These files are optional caches for debugging and auditability.

## Explainability

Main function:

- `compute_explainability(df)`

Purpose:

- explain why a predicted segment differs from the global portfolio average

Compared features:

- `nb_employes_mid`
- `chiffre_affaires`
- `nb_locaux`
- `age_entreprise`

Per-feature metrics:

- `cluster_mean`
- `global_mean`
- `ratio`
- `z_score`
- `direction`

Selection rule:

- sort by absolute `z_score`
- keep top 3 features

### Where it is used

- backend attaches `segment["explainability"]`
- `SegmentCard.vue` renders it as "Pourquoi ce segment ?"

This layer is deterministic and does not depend on Gemini.

## Strategic insights

Main file:

- `llm_service.py`

Function:

- `generate_insights(segments, validation, export_dir, timestamp)`

Output file:

- `cluster_insights.json`
- plus timestamped version

### Gemini mode

When `GEMINI_API_KEY` is present and the client library is installed:

- the backend sends segment summaries and validation metrics to Gemini
- Gemini must return exactly 6 French executive insight cards in JSON

### Fallback mode

If Gemini is unavailable or fails:

- the backend writes a fixed rule-based list of 6 insight cards

Fallback themes include:

- portfolio concentration
- scale opportunity
- high average revenue segments
- geographic diversification
- company age as a signal
- recommendation to re-run after major ETL imports

### Frontend behavior

`InsightsPanel.vue` renders:

- backend `summary.insights`
- `summary.insights_source`

If none of the backend insights mention maturity in the title, the component appends client-side maturity insights for:

- least mature segment
- highest-gap segment
- most mature segment

## Frontend usage of maturity and explainability fields

| Component | Fields used |
|---|---|
| `SegmentCard.vue` | `digital_maturity_score`, `digital_maturity_level`, `digital_gap`, `maturity_details.adjustment_reasons`, `explainability.top_features` |
| `MaturityAnalysisSection.vue` | `digital_maturity_score`, `digital_maturity_level`, `digital_gap`, `maturity_details.maturity_distribution` |
| `OpportunityMatrix.vue` | `digital_maturity_score`, `digital_gap`, `digital_maturity_level` |
| `LeadsExplorerTable.vue` | lead-level `digital_maturity_level`, `digital_gap` |
| `InsightsPanel.vue` | `summary.insights`, `summary.insights_source`, segment maturity fields for local supplements |

## Maintenance guide

Change sector baselines:

- `digital_maturity_baseline.py`

Change deterministic adjustment rules:

- `digital_maturity_adjustment.py`

Change score thresholds or stage labels:

- `digital_maturity.py`

Change Gemini maturity prompt or output sanitization:

- `digital_maturity_llm.py`

Change strategic insight prompt:

- `llm_service.py`

Keep compatibility in mind:

- several frontend components assume maturity fields live directly on each segment
- do not move maturity into a nested namespace unless you also update the dashboard
