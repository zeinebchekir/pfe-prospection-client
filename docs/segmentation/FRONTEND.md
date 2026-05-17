# Segmentation Frontend

## Access model

Route:

- `/manager/segmentation`

Route definition:

- `frontend/src/router/index.js`

Access control:

- `meta.requiresAuth = true`
- `meta.roles = ["CEO"]`

Navigation exposure:

- `frontend/src/components/AppSidebar.vue`
- shown only when `user.role === "CEO"`

This means the page is intentionally management-only in the UI.

## Service layer

Primary service file:

- `frontend/src/services/segmentation.js`

Responsibilities:

- create a dedicated Axios client for ETL FastAPI
- expose the segmentation endpoints
- expose fallback segment metadata and revenue/sector formatting helpers

Exports:

- `runClustering()`
- `getSummary()`
- `getLeads(params)`
- `SEGMENT_META`
- `SECTOR_LABELS`
- `formatSector(value)`
- `formatRevenue(value)`

Important design detail:

- this file does not use the main Django Axios client
- it talks directly to `VITE_ETL_API_URL`

## Page orchestration

Main page:

- `frontend/src/pages/manager/MarketAnalysisPage.vue`

Page responsibilities:

- load the latest summary on mount via `getSummary()`
- show a validation badge in the header
- trigger a new batch run via `runClustering()`
- pass `summary.segments` down to all market components
- hold the currently selected segment for the drilldown drawer

Reactive state:

- `summary`
- `loading`
- `running`
- `error`
- `selectedSegment`

### Header validation badge

Behavior:

- if `model_type === "decision_tree"`, show `training_accuracy`
- otherwise fall back to historical silhouette logic

Decision-tree badge source fields:

- `validation.training_accuracy`
- `validation.tree_depth`
- `validation.n_leaves`

## Component map

All dashboard components live in:

- `frontend/src/components/market/`

## MarketKPICards.vue

Props:

- `segments`
- `totalLeads`

Displays:

- total leads
- number of active segments
- dominant segment by volume
- weighted average revenue
- weighted average company age
- highest revenue-priority segment

Logic notes:

- all values are derived client-side from `summary.segments`
- no extra API calls

## SegmentBubbleChart.vue

Props:

- `segments`
- `totalLeads`

Displays:

- merged top-level bubbles by `label_short`
- sub-segment drilldown bubbles on click

Logic notes:

- top-level grouping is by `label_short`, not by raw cluster id
- current groups therefore collapse the dashboard into high-level families such as `PME`, `ETI`, and `GE`
- clicking a group reveals its underlying sub-segments using `label_sub`

Data dependencies:

- `cluster`
- `label`
- `label_short`
- `label_sub`
- `n`
- `color`

## SegmentCard.vue

Props:

- `segment`
- `totalLeads`

Events:

- emits `select` with the segment object

Displays:

- label, sub-label, share of portfolio
- average revenue, headcount, age
- dominant category, sector, region
- business recommendation
- maturity score, level, gap, and adjustment reasons
- "Pourquoi ce segment ?" explainability bullets

Logic notes:

- explainability text is generated client-side from backend `explainability.top_features`
- maturity reason expansion uses `segment.maturity_details.adjustment_reasons`

## SegmentDrilldownDrawer.vue

Props:

- `open`
- `segment`
- `totalLeads`

Displays:

- statistical summary blocks
- comparison vs global portfolio
- dominant dimensions
- representative companies
- extreme companies
- ranked top lists
- homogeneity blocks

Important design detail:

- the drawer uses `segment.drilldown` already embedded in the summary response
- no extra detail endpoint exists

## MaturityAnalysisSection.vue

Props:

- `segments`

Displays:

- weighted portfolio maturity average
- stacked maturity distribution bars per segment
- highest-gap segment callout
- top 3 transformation potential cards

Logic notes:

- only segments with `digital_maturity_score != null` are considered
- if `maturity_distribution` is missing, the component derives a coarse fallback distribution from the score
- top potential ranking formula is:

```text
(digital_gap / 10) * (segment_volume / total_volume) * (segment_ca_moyen / max_ca)
```

## SegmentComparisonCharts.vue

Props:

- `segments`

Displays:

- average revenue bar chart
- average headcount bar chart

Implementation:

- uses `vue3-apexcharts`
- colors each bar from `segment.color`

## SegmentRadarChart.vue

Props:

- `segments`

Displays:

- up to 3 selected segments on a normalized radar chart

Logic notes:

- initial selection is the first 3 loaded segments
- selecting a fourth segment ejects the oldest selected one
- axes:
  - size
  - revenue value
  - age
  - number of sites
  - geographic concentration
- geographic concentration is currently a coarse rule:
  - `Ile-de-France` -> `90`
  - anything else -> `50`

## OpportunityMatrix.vue

Props:

- `segments`

Displays:

- scatter chart of volume vs average revenue

Encodings:

- x-axis: `n`
- y-axis: `ca_moyen`
- marker size: scaled from segment volume
- marker stroke width/color: derived from `digital_gap`

Tooltip enrichments:

- maturity score
- digital gap
- maturity interpretation string

## InsightsPanel.vue

Props:

- `insights`
- `source`
- `segments`

Displays:

- backend-generated strategic insights
- source indicator (`gemini-1.5-flash` vs data-based fallback)

Important logic:

- if backend insights do not already include maturity-oriented cards, the component adds client-side maturity insights derived from:
  - least mature segment
  - highest digital gap segment
  - most mature segment

## LeadsExplorerTable.vue

Props:

- `segments`

Displays:

- paginated lead explorer
- segment filter
- text search
- rows-per-page control
- maturity badge and digital gap columns

### Data flow

- component owns its own state
- on mount it calls `getLeads()`
- it does not consume lead rows from the summary response

### Query mapping

Frontend state to API params:

- `page * limit` -> `skip`
- `limit` -> `limit`
- `selectedSegment` -> `segment`
- trimmed `search` -> `search`

### Pagination logic

State:

- `page`
- `limit`
- `total`

Derived:

- `totalPages = ceil(total / limit)`
- `visiblePages` keeps:
  - first page
  - last page
  - current page
  - current +/- 1
  - ellipses between gaps

### Filtering behavior

- changing page fetches immediately
- changing segment resets page to `0` and fetches immediately
- changing search resets page to `0` and fetches immediately

Current implementation note:

- there is no debounce on search, so each change triggers a fetch

### Data dependencies

Per lead row the table expects:

- `nom_entreprise`
- `siren`
- `cluster`
- `cluster_label`
- `secteur_activite`
- `ville`
- `chiffre_affaires`
- `digital_maturity_level`
- `digital_gap`
- `region`

It also builds a local `segmentMap` from `props.segments` so it can show the latest labels/colors/sub-labels for each numeric cluster id.

## Role-based integration

Three layers enforce the current role model:

- Vue router meta roles: only `CEO`
- sidebar navigation: only CEO sees the menu entry
- page copy and component design: management-focused, not operator-focused

Current security caveat:

- the ETL API endpoints themselves are not guarded by Django session auth
- role protection is therefore primarily a frontend navigation concern unless the ETL API is network-restricted elsewhere

## Frontend maintenance guide

Change API consumption:

- `frontend/src/services/segmentation.js`

Change page composition or run button flow:

- `frontend/src/pages/manager/MarketAnalysisPage.vue`

Change a chart/card/table:

- `frontend/src/components/market/<ComponentName>.vue`

Change route or role access:

- `frontend/src/router/index.js`

Change sidebar entry:

- `frontend/src/components/AppSidebar.vue`

Keep backward compatibility:

- preserve numeric `cluster` handling unless you update every component that keys by cluster id
- preserve `label_short`, `label_sub`, and `color` because several components rely on them directly
- preserve the embedded `segment.drilldown` contract unless you introduce a new detail endpoint and update the drawer
