"""
Lead Clustering Pipeline — Full Production Code
================================================
Data: entreprise (semicolon-delimited, no header, UTF-8)
Output: cleaned_data.csv, clustered_leads.csv, cluster_summary.csv
"""

# ── 1. IMPORTS ────────────────────────────────────────────────────────────────
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

# ── 2. ROBUST CSV LOADING ─────────────────────────────────────────────────────
COLS = [
    'siren', 'lead_id', 'siren2', 'siret', 'nom_entreprise', 'ville', 'code_postal',
    'pays', 'secteur_activite', 'forme_juridique', 'tranche_effectif',
    'categorie_entreprise', 'nb_locaux', 'chiffre_affaires', 'date_creation',
    'date_modification', 'date_import', 'col17', 'col18', 'col19',
    'dirigeants', 'donnees_source', 'source_lead', 'created_at',
    'updated_at', 'statut', 'score'
]

df = pd.read_csv(
    'entreprise',            # ← change path if needed
    sep=';',
    header=None,
    names=COLS,
    on_bad_lines='skip',     # skip malformed rows
    encoding='utf-8',
    dtype=str                # load everything as str first for safety
)
print(f"Loaded: {df.shape[0]} rows × {df.shape[1]} cols")

# ── 3. DATA CLEANING ──────────────────────────────────────────────────────────
# Convert numeric columns
for col in ['nb_locaux', 'chiffre_affaires', 'code_postal', 'score']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Remove exact duplicates
df = df.drop_duplicates(subset=['siren'])

# Drop noise/irrelevant columns
DROP_COLS = ['col17', 'col18', 'col19', 'dirigeants', 'donnees_source',
             'siren2', 'date_modification', 'date_import', 'statut',
             'source_lead', 'created_at', 'updated_at', 'siret', 'lead_id']
df = df.drop(columns=DROP_COLS)

# Fill missing categorie
df['categorie_entreprise'] = df['categorie_entreprise'].fillna('PME')

# ── 4. FEATURE ENGINEERING ────────────────────────────────────────────────────
# 4a. Employee midpoint from tranche_effectif string
EFFECTIF_MAP = {
    'Unité non employeuse (0 salarié)': 0, '0 salarié': 0,
    '1 à 2 salariés': 1, '3 à 5 salariés': 4, '6 à 9 salariés': 7,
    '10 à 19 salariés': 14, '20 à 49 salariés': 34, '50 à 99 salariés': 74,
    '100 à 199 salariés': 149, '200 à 249 salariés': 224,
    '250 à 499 salariés': 374, '500 à 999 salariés': 749,
    '1 000 à 1 999 salariés': 1499, '2 000 à 4 999 salariés': 3499,
    '5 000 à 9 999 salariés': 7499, '10 000 salariés et plus': 15000,
}
df['nb_employes_mid'] = df['tranche_effectif'].str.strip().map(EFFECTIF_MAP)
df['nb_employes_mid'] = df['nb_employes_mid'].fillna(df['nb_employes_mid'].median())

# 4b. Log-transform CA (heavy right skew) + impute by company category
df['ca_log'] = np.log1p(df['chiffre_affaires'])
med_ca = df.groupby('categorie_entreprise')['ca_log'].transform('median')
df['ca_log'] = df['ca_log'].fillna(med_ca).fillna(df['ca_log'].median())

# 4c. Log-transform nb_locaux (right skew)
df['nb_locaux_log'] = np.log1p(df['nb_locaux'].fillna(1))

# 4d. Company age in years
df['date_creation'] = pd.to_datetime(df['date_creation'], errors='coerce')
df['age_entreprise'] = (pd.Timestamp('2026-04-15') - df['date_creation']).dt.days / 365.25
df['age_entreprise'] = df['age_entreprise'].fillna(df['age_entreprise'].median())

# 4e. Region from code postal (5 broad regions)
def get_region(cp):
    if pd.isna(cp): return 'Inconnu'
    dept = int(cp) // 1000
    if 75 <= dept <= 95: return 'Ile-de-France'
    elif dept <= 30:     return 'Sud'
    elif dept <= 55:     return 'Est'
    elif dept <= 76:     return 'Nord-Ouest'
    else:                return 'Autre'
df['region'] = df['code_postal'].apply(get_region)

# 4f. Sector grouping: top 8 → keep name, rest → 'Autre'
top_sectors = df['secteur_activite'].value_counts().head(8).index.tolist()
df['secteur_broad'] = df['secteur_activite'].apply(
    lambda x: x if x in top_sectors else 'Autre')

# ── 5. FEATURE MATRIX ─────────────────────────────────────────────────────────
NUM_FEATURES = ['nb_employes_mid', 'ca_log', 'nb_locaux_log', 'age_entreprise']
CAT_FEATURES = ['categorie_entreprise', 'region', 'secteur_broad']

X_num = df[NUM_FEATURES].copy()
X_cat = pd.get_dummies(df[CAT_FEATURES], drop_first=False)
X_raw = pd.concat([X_num, X_cat], axis=1)

scaler = StandardScaler()
X = scaler.fit_transform(X_raw)
print(f"Feature matrix: {X.shape}")

# ── 6. K SELECTION: ELBOW + SILHOUETTE ───────────────────────────────────────
K_RANGE = range(2, 11)
inertias, silhouettes = [], []

for k in K_RANGE:
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(X)
    inertias.append(km.inertia_)
    silhouettes.append(silhouette_score(X, labels))

# Plot Elbow
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
fig.patch.set_facecolor('#0F1117')
COLORS_5 = ['#E63946','#2196F3','#4CAF50','#FF9800','#9C27B0']

for ax in axes: ax.set_facecolor('#1A1D27')
axes[0].plot(list(K_RANGE), inertias, 'o-', color='#2196F3', lw=2, markersize=7)
axes[0].axvline(x=5, color='#FF9800', ls='--', label='K=5 retenu')
axes[0].set_title('Méthode du Coude', color='white', fontweight='bold', fontsize=13)
axes[0].set_xlabel('K', color='#aaa'); axes[0].set_ylabel('Inertie', color='#aaa')
axes[0].tick_params(colors='#888')
axes[0].legend(facecolor='#1A1D27', labelcolor='white')
for sp in axes[0].spines.values(): sp.set_color('#333')

axes[1].plot(list(K_RANGE), silhouettes, 's-', color='#4CAF50', lw=2, markersize=7)
axes[1].axvline(x=5, color='#FF9800', ls='--', label='K=5 retenu')
axes[1].set_title('Score de Silhouette', color='white', fontweight='bold', fontsize=13)
axes[1].set_xlabel('K', color='#aaa'); axes[1].set_ylabel('Silhouette', color='#aaa')
axes[1].tick_params(colors='#888')
axes[1].legend(facecolor='#1A1D27', labelcolor='white')
for sp in axes[1].spines.values(): sp.set_color('#333')

plt.tight_layout()
plt.savefig('elbow_silhouette.png', dpi=150, bbox_inches='tight', facecolor='#0F1117')

# ── 7. FINAL CLUSTERING K=5 ───────────────────────────────────────────────────
K_FINAL = 5
km_final = KMeans(n_clusters=K_FINAL, random_state=42, n_init=20)
df['cluster'] = km_final.fit_predict(X)

print("\nCluster distribution:")
print(df['cluster'].value_counts().sort_index())

# ── 8. PCA VISUALIZATION ──────────────────────────────────────────────────────
pca = PCA(n_components=2, random_state=42)
X_2d = pca.fit_transform(X)
df['pca1'], df['pca2'] = X_2d[:, 0], X_2d[:, 1]
print(f"PCA variance explained: {pca.explained_variance_ratio_.sum():.1%}")

fig2, axes2 = plt.subplots(1, 3, figsize=(18, 6))
fig2.patch.set_facecolor('#0F1117')
for ax in axes2: ax.set_facecolor('#1A1D27')

# PCA scatter
ax = axes2[0]
for c in range(K_FINAL):
    m = df['cluster'] == c
    ax.scatter(df.loc[m,'pca1'], df.loc[m,'pca2'],
               c=COLORS_5[c], alpha=0.7, s=30, label=f'Cluster {c}', zorder=3)
ax.set_title('PCA 2D — Clusters des Leads', color='white', fontweight='bold', fontsize=12)
ax.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.1%})', color='#aaa')
ax.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.1%})', color='#aaa')
ax.tick_params(colors='#888'); ax.legend(facecolor='#1A1D27', labelcolor='white', fontsize=9)
for sp in ax.spines.values(): sp.set_color('#333')

# Cluster sizes
cluster_counts = df['cluster'].value_counts().sort_index()
bars = axes2[1].bar([f'C{c}' for c in range(K_FINAL)],
                    cluster_counts.values, color=COLORS_5, alpha=0.85, edgecolor='#333')
axes2[1].set_title('Effectif par Cluster', color='white', fontweight='bold', fontsize=12)
axes2[1].set_xlabel('Cluster', color='#aaa'); axes2[1].set_ylabel('Nb Leads', color='#aaa')
axes2[1].tick_params(colors='#888')
for sp in axes2[1].spines.values(): sp.set_color('#333')
for bar, v in zip(bars, cluster_counts.values):
    axes2[1].text(bar.get_x()+bar.get_width()/2, bar.get_height()+3, str(v),
                  ha='center', color='white', fontweight='bold')

# Stacked bar: categorie
cat_pct = pd.crosstab(df['cluster'], df['categorie_entreprise'], normalize='index') * 100
cat_colors_map = ['#E63946','#2196F3','#4CAF50','#FF9800']
bottom = np.zeros(K_FINAL)
for i, col in enumerate(cat_pct.columns):
    axes2[2].bar([f'C{c}' for c in range(K_FINAL)], cat_pct[col].values,
                 bottom=bottom, label=col, color=cat_colors_map[i%4], alpha=0.85, edgecolor='#333')
    bottom += cat_pct[col].values
axes2[2].set_title('Catégorie Entreprise (%)', color='white', fontweight='bold', fontsize=12)
axes2[2].set_xlabel('Cluster', color='#aaa'); axes2[2].set_ylabel('%', color='#aaa')
axes2[2].tick_params(colors='#888')
axes2[2].legend(facecolor='#1A1D27', labelcolor='white', fontsize=7, loc='upper right')
for sp in axes2[2].spines.values(): sp.set_color('#333')

plt.tight_layout()
plt.savefig('clustering_overview.png', dpi=150, bbox_inches='tight', facecolor='#0F1117')
print("Plots saved.")

# ── 9. CLUSTER PROFILING ──────────────────────────────────────────────────────
summary = df.groupby('cluster').agg(
    n=('cluster','count'),
    employes_moyen=('nb_employes_mid','mean'),
    ca_moyen=('chiffre_affaires', lambda x: x.mean()),
    nb_locaux_moyen=('nb_locaux','mean'),
    age_moyen=('age_entreprise','mean'),
    categorie_dominante=('categorie_entreprise', lambda x: x.mode()[0]),
    secteur_dominant=('secteur_broad', lambda x: x.mode()[0]),
    region_dominante=('region', lambda x: x.mode()[0]),
).reset_index()

summary['employes_moyen'] = summary['employes_moyen'].round(0).astype(int)
summary['ca_moyen'] = summary['ca_moyen'].apply(lambda x: f"{x/1e6:.1f}M€" if not pd.isna(x) else 'N/A')
summary['nb_locaux_moyen'] = summary['nb_locaux_moyen'].round(1)
summary['age_moyen'] = summary['age_moyen'].round(1)
print("\n=== CLUSTER PROFILES ===")
print(summary.to_string(index=False))

# ── 10. EXPORT RESULTS ────────────────────────────────────────────────────────
df.drop(columns=['pca1','pca2'], errors='ignore').to_csv('cleaned_data.csv', index=False)

df[['siren','nom_entreprise','ville','secteur_activite','categorie_entreprise',
    'tranche_effectif','chiffre_affaires','age_entreprise','region','cluster']
].to_csv('clustered_leads.csv', index=False)

summary.to_csv('cluster_summary.csv', index=False)
print("\n✓ Exports: cleaned_data.csv | clustered_leads.csv | cluster_summary.csv")
print("✓ Plots: elbow_silhouette.png | clustering_overview.png")
