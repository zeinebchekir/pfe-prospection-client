# Segmentation Data Pipeline

## Current engine

The active production pipeline is `run_decision_tree_segmentation()` in:

- `ETL_service/ETL_pipeline/market_analysis/decision_tree_segmentation.py`

Entry compatibility path:

- `market_analysis.clustering.run_clustering(db)`

The router still calls `run_clustering(db)`, but that function now delegates to the decision-tree engine.

## Why the docs must say "decision tree", not "KMeans"

The current runtime facts are:

- `DecisionTreeClassifier(max_depth=3, min_samples_leaf=20, random_state=42)` is instantiated in production
- `model_type` is exported as `decision_tree`
- validation is based on accuracy, tree depth, leaves, confusion matrix, and exported text rules
- `cluster` ids are mapped from business segment codes, not discovered KMeans centroids

KMeans still exists in the repository only as historical support material:

- `lead_clustering.py`
- `validation.py::compute_validation`
- older sections of the previous `SEGMENTATION.md`

## Pipeline stages

```text
Entreprise rows from SQLAlchemy
    -> pandas DataFrame creation
    -> type cleaning and deduplication
    -> business feature engineering
    -> deterministic segment_rule creation
    -> shallow decision-tree training on labeled rows
    -> prediction for all rows
    -> validation
    -> segment summary aggregation
    -> explainability
    -> digital maturity
    -> Gemini or fallback enrichment
    -> latest + versioned JSON exports
```

## Source table and loaded columns

The pipeline reads `db.models.Entreprise` and extracts these fields:

| ETL column | DataFrame column | Used for |
|---|---|---|
| `siren` | `siren` | deduplication, export identity, lead maturity jitter seed |
| `nom` | `nom_entreprise` | dashboard display |
| `ville` | `ville` | dashboard display |
| `code_postal` | `code_postal` | region derivation |
| `secteur_activite` | `secteur_activite` | macro-sector mapping, maturity baseline, display |
| `categorie_entreprise` | `categorie_entreprise` | category normalization, rule labeling, training |
| `taille_entrep` | `tranche_effectif` | employee midpoint mapping |
| `nb_locaux` | `nb_locaux` | segment statistics, maturity, drilldown |
| `ca` | `ca` and `chiffre_affaires` | revenue band, training, segment value, display |
| `date_creation_entreprise` | `date_creation` | age derivation |

## Required vs optional fields

There is no strict schema validator before the DataFrame stage. The current logic is tolerant and fills or infers many missing fields.

### Required for any successful run

- at least one row in `entreprise`

### Required for a row to participate in tree training

- `categorie_entreprise` after normalization
- non-null raw `ca`

Rows missing raw `ca` are excluded from the training subset but can still receive a predicted segment using fallback modeling revenue.

### Optional but strongly recommended

- `secteur_activite`
- `taille_entrep`
- `code_postal`
- `date_creation_entreprise`
- `nb_locaux`
- `ville`
- `siren`

## Preprocessing and feature engineering

## 1. Type cleaning

- `ca` -> numeric with `errors="coerce"`
- `nb_locaux` -> numeric with `errors="coerce"`
- `date_creation` -> pandas datetime with `errors="coerce"`
- object columns -> repaired through `fix_mojibake()`

## 2. Deduplication

- dedupe key: `siren`
- behavior: keep first occurrence for duplicated non-null SIREN values
- rows without SIREN are retained

## 3. Company category normalization

Function:

- `normalize_company_category()`

Normalized outcomes:

- any text containing `grande` -> `Grande Entreprise`
- any text containing `interm` or exactly `eti` -> `Entreprise de Taille Intermediaire`
- any text containing `pme`, `petite`, `moyenne`, or `micro` -> `Petite et Moyenne Entreprise`
- empty value -> `Petite et Moyenne Entreprise`

This means the current production logic folds micro-enterprises into the PME family for segmentation purposes.

## 4. Employee range mapping

Functionality:

- `tranche_effectif` text is stripped
- mapped through `EFFECTIF_MAP`
- unknown ranges fall back to the dataset median midpoint
- if the whole column is missing, fallback is `0`

Examples:

- `10 a 19 salaries` -> `14`
- `100 a 199 salaries` -> `149`
- `10 000 salaries et plus` -> `15000`

## 5. Revenue band logic

Function:

- `ca_band(ca)`

Rules:

- `NaN` -> `Unknown`
- `< 10_000_000` -> `Small`
- `< 50_000_000` -> `Mid`
- `>= 50_000_000` -> `Large`

## 6. Sector normalization

Two sector representations coexist:

- `secteur_activite`
  - raw or cleaned ETL sector label used for display and maturity baseline matching
- `macro_sector`
  - simplified family used by segmentation rules and the tree

Macro-sector mapping examples:

| Raw sector label | Macro sector |
|---|---|
| `62.02A` | `IT` |
| `Conseil informatique` | `IT` |
| `Tierce mainten. syst.` | `IT` |
| `Commerce de gros` | `Commerce` |
| `Act. auxil. assurance` | `Finance` |
| `Services de prerogative publique` | `Public` |
| unmapped / unknown | `Other` |

This is an exact dictionary lookup after mojibake repair, not fuzzy classification.

## 7. Region extraction

Function:

- `_get_region(code_postal)`

Rules:

- departments `75..95` -> `Ile-de-France`
- `<= 30` -> `Sud`
- `<= 55` -> `Est`
- `<= 76` -> `Nord-Ouest`
- other parseable values -> `Autre`
- parse failure -> `Inconnu`

This is a coarse dashboard geography, not an official regional mapping.

## 8. Age computation

Formula:

```text
age_entreprise = (today - date_creation).days / 365.25
```

Behavior:

- invalid or missing creation dates become `NaT`
- missing ages are filled with the dataset median age
- if no usable ages exist, fallback is `0`

## 9. Missing value strategy summary

| Field | Strategy |
|---|---|
| `categorie_entreprise` | normalize, default to PME family |
| `tranche_effectif` | strip text, map, fallback to median employee midpoint |
| `secteur_activite` | fill `Inconnu`, macro-sector fallback `Other` |
| `ville` | fill `Inconnu` |
| `code_postal` | fill empty string, region fallback `Inconnu` |
| `ca` | keep `NaN` for reporting, build `ca_for_model` for prediction fallback |
| `nb_locaux` | leave `NaN` if unknown; later aggregations ignore or tolerate it |
| `date_creation` | convert to age, fallback to median age |

## Rule-based segment labeling

The deterministic first-pass target is `segment_rule`.
This is the label the decision tree learns.

Function:

- `segment_label(row)`

Rules:

### PME family

- `Small` revenue band + `IT` macro sector -> `PME_Small_IT`
- `Small` revenue band + anything else -> `PME_Small_NonIT`
- `Mid` or `Large` revenue band -> `PME_Mid`

### ETI family

- `IT` macro sector -> `ETI_IT`
- otherwise `Large` revenue band -> `ETI_Large`
- otherwise -> `ETI_Mid`

### Grande entreprise

- always -> `GE_Large`

### Unknown category branch

- returns `None`

In practice, category normalization makes `None` rare.

## Model training and prediction

### Training subset

Training rows satisfy:

- `segment_rule` is not null
- raw `ca` is not null

### Tree features

Exported feature list:

- `cat_enc`
- `ca`
- `sec_enc`
- `band_enc`

Displayed validation feature names:

- `Categorie`
- `CA (EUR)`
- `Secteur`
- `CA Band`

### Encoding

Text fields are encoded through `_encode_column()`:

- category fallback: `Petite et Moyenne Entreprise`
- macro-sector fallback: `Other`
- revenue band fallback: `Unknown`

### Model

```python
DecisionTreeClassifier(
    max_depth=3,
    min_samples_leaf=20,
    random_state=42,
)
```

Why this matters:

- shallow depth keeps the rules explainable
- leaf size avoids tiny unstable buckets
- fixed random state keeps training reproducible

### Prediction

Prediction uses `ca_for_model`, not raw `ca`.

Fallback order for `ca_for_model`:

1. raw `ca`
2. median `ca` of same normalized company category
3. global median `ca`
4. `0.0`

Confidence:

- `decision_tree_confidence = max(predict_proba(row))`
- exported at both lead and segment level

## Segment code to frontend cluster id mapping

The frontend still expects a numeric `cluster`.
The current mapping is fixed in `SEGMENT_META`.

| Segment code | Numeric cluster id | Label |
|---|---:|---|
| `PME_Small_IT` | `0` | `PME technologiques` |
| `PME_Small_NonIT` | `1` | `PME operationnelles` |
| `PME_Mid` | `2` | `PME en croissance` |
| `ETI_IT` | `3` | `ETI technologiques` |
| `ETI_Mid` | `4` | `ETI etablies` |
| `ETI_Large` | `5` | `ETI grands comptes` |
| `GE_Large` | `6` | `Grands groupes` |

Segment count is dynamic per run.
The catalog supports 7 ids, but a given dataset may activate fewer.

## Segment summary aggregation

The summary groups by:

- `cluster`
- `segment_code`

Per-segment aggregate fields include:

- `n`
- `employes_moyen`
- `ca_moyen`
- `nb_locaux_moyen`
- `age_moyen`
- `categorie_dominante`
- `secteur_dominant`
- `region_dominante`
- `macro_sector_dominant`
- `decision_tree_confidence_mean`

Additional enrichments are attached later:

- `explainability`
- `digital_maturity_score`
- `digital_maturity_level`
- `digital_gap`
- `maturity_details`
- `llm_analysis`
- `drilldown`

## Validation

Current validation is built by:

- `compute_decision_tree_validation()`

Fields:

- `model_type`
- `k_used`
- `training_accuracy`
- `tree_depth`
- `n_leaves`
- `silhouette`
- `silhouette_score`
- `silhouette_interpretation`
- `elbow`
- `classification_report`
- `confusion_matrix`
- `tree_rules`

Decision-tree behavior:

- `silhouette`, `silhouette_score`, and `elbow` are exported as `None` or "not applicable" compatibility placeholders
- the frontend header badge uses `training_accuracy` when `model_type === "decision_tree"`

## Explainability

Explainability is computed after segment aggregation by:

- `market_analysis/explainability.py`

Compared features:

- `nb_employes_mid`
- `chiffre_affaires`
- `nb_locaux`
- `age_entreprise`

Per feature, the engine computes:

- `cluster_mean`
- `global_mean`
- `ratio`
- `z_score`
- `direction`

Then it selects the top 3 differentiators by absolute `z_score`.

The UI uses these values in:

- `SegmentCard.vue` under "Pourquoi ce segment ?"

## Deprecated and historical pieces

These remain in the repository but are not part of the current runtime path:

| File / function | Status |
|---|---|
| `lead_clustering.py` | historical KMeans pipeline script |
| `validation.py::compute_validation` | historical KMeans silhouette/elbow helper |
| `market_analysis/labeling.py` | older v3 labeling helper, not imported |
| `DecisionTree_Restructured.ipynb` | research notebook |

For maintainers, the safest rule is:

- if you are changing production segmentation behavior, change `decision_tree_segmentation.py`
- do not update the historical KMeans files unless you are intentionally preserving reference material
