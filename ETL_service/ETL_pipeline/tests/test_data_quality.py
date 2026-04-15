"""
test_data_quality.py — Audit Qualité des Données pour le pipeline ETL CRM.

Se connecte à PostgreSQL pour auditer les tables `entreprise` et `raw_leads`.
Évalue les 5 dimensions DQ :
  1. Complétude    — % de champs renseignés par colonne
  2. Unicité       — doublons sur SIREN, SIRET, (nom+code_postal)
  3. Validité      — format SIREN/SIRET (+ Luhn), email, téléphone, code postal,
                     CA positif, NAF mapping, forme juridique mapping
  4. Cohérence     — SIRET[:9]==SIREN, date_creation <= today, CP[:2]==département
  5. Fraîcheur     — âge moyen, dernière MAJ, raw → clean drop-rate

Usage :
  python tests/test_data_quality.py                     # mode DB (défaut)
  python tests/test_data_quality.py --mode synthetic    # mode démo

Requires : pip install pandas numpy psycopg2-binary  (ou sqlalchemy déjà installé)
"""

import argparse
import json
import os
import re
import sys
import io
from datetime import datetime, date, timedelta
from pathlib import Path
from dataclasses import dataclass, field, asdict

# Force UTF-8 on Windows consoles
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import pandas as pd
import numpy as np


# ══════════════════════════════════════════════════════════════
#  CONFIGURATION — colonnes de la table `entreprise`
# ══════════════════════════════════════════════════════════════

# Toutes les colonnes de la table entreprise (SQLAlchemy model)
ENTREPRISE_COLUMNS = [
    "identifiant", "raw_lead_id",
    "siren", "siret", "nom",
    "ville", "code_postal", "pays",
    "secteur_activite", "forme_juridique", "taille_entrep",
    "categorie_entreprise", "nb_locaux", "ca",
    "date_creation_entreprise", "date_derniere_modif_site", "date_scraping",
    "telephone", "adresse_email",
    "info_boamp", "dirigeants", "statut",
    "sources", "taux_completude", "dag_run_id",
    "created_at", "updated_at",
]

# Classification par criticité pour la complétude
CRITICAL_FIELDS = ["siren", "nom"]
IMPORTANT_FIELDS = ["siret", "code_postal", "ville", "secteur_activite",
                    "ca", "telephone", "forme_juridique"]
OPTIONAL_FIELDS = ["adresse_email", "taille_entrep", "categorie_entreprise",
                   "nb_locaux", "dirigeants", "date_creation_entreprise"]

ALL_COMPLETENESS_FIELDS = CRITICAL_FIELDS + IMPORTANT_FIELDS + OPTIONAL_FIELDS

# ── Regex patterns (basés sur les standards INSEE / RFC 5322) ──
SIREN_RE  = re.compile(r"^\d{9}$")
SIRET_RE  = re.compile(r"^\d{14}$")
CP_RE     = re.compile(r"^\d{5}$")
EMAIL_RE  = re.compile(r"^[\w.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$")
PHONE_E164_RE = re.compile(r"^\+33\d{9}$")   # format E.164 France normalisé
NAF_RE = re.compile(r"^\d{2}\.?\d{2}[A-Za-z]$")  # NAF Rev.2 : 62.01Z ou 6201Z
LINKEDIN_RE = re.compile(r"^https?://(www\.)?linkedin\.com/in/.+$", re.IGNORECASE)

# ── Valeurs des codes de mapping connus ──
# On importera les dicts depuis le pipeline pour vérifier si les valeurs en base
# correspondent à des labels mappés ou à des codes bruts non-résolus.

# ── Helper : Extract employee count from taille_entrep label ──
TAILLE_TO_EMPLOYEES = {
    "Unité non employeuse (0 salarié)": 0,
    "0 salarié": 0,
    "1 à 2 salariés": 1.5,
    "3 à 5 salariés": 4,
    "6 à 9 salariés": 7.5,
    "10 à 19 salariés": 14.5,
    "20 à 49 salariés": 34.5,
    "50 à 99 salariés": 74.5,
    "100 à 199 salariés": 149.5,
    "200 à 249 salariés": 224.5,
    "250 à 499 salariés": 374.5,
    "500 à 999 salariés": 749.5,
    "1 000 à 1 999 salariés": 1499.5,
    "2 000 à 4 999 salariés": 3499.5,
    "5 000 à 9 999 salariés": 7499.5,
    "10 000 salariés et plus": 15000,
}

# ── Statuts autorisés dans le CRM ──
STATUTS_AUTORISES = {"Nouveau", "Contacte", "Qualifie", "Perdu", "Gagne", "En cours",
                     "NOUVEAU", "CONTACTE", "QUALIFIE", "PERDU", "GAGNE", "EN_COURS",
                     "nouveau", "contacte", "qualifie", "perdu", "gagne", "en_cours"}

# ── Secteurs réglementés qui exigent des localisations spécifiques ──
SECTEURS_REGLEMENTES = {
    "Activités financières": True,
    "Assurance": True,
    "Activités juridiques": True,
    "Santé": True,
    "Fabrication de préparations pharmaceutiques": True,
}



# ══════════════════════════════════════════════════════════════
#  LUHN ALGORITHM — validation officielle SIREN/SIRET
# ══════════════════════════════════════════════════════════════

def luhn_checksum(number_str: str) -> bool:
    """
    Vérifie la validité d'un numéro via l'algorithme de Luhn.
    Utilisé par l'INSEE pour SIREN (9 chiffres) et SIRET (14 chiffres).
    Retourne True si le checksum est valide.
    """
    if not number_str or not number_str.isdigit():
        return False
    digits = [int(d) for d in number_str]
    # Double every second digit from the right
    for i in range(len(digits) - 2, -1, -2):
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9
    return sum(digits) % 10 == 0


# ══════════════════════════════════════════════════════════════
#  DATA SOURCE LOADERS
# ══════════════════════════════════════════════════════════════

def load_from_database() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Charge les tables `entreprise` et `raw_leads` depuis PostgreSQL.
    Retourne (df_entreprise, df_raw).
    """
    pipeline_root = str(Path(__file__).resolve().parent.parent)
    if pipeline_root not in sys.path:
        sys.path.insert(0, pipeline_root)

    from sqlalchemy import create_engine as _ce
    from db.database import DATABASE_URL

    _engine = _ce(DATABASE_URL)
    raw_conn = _engine.raw_connection()

    try:
        df_ent = pd.read_sql("SELECT * FROM entreprise", raw_conn)
        print(f"  [DB] {len(df_ent)} enregistrements charges depuis 'entreprise'.")

        try:
            df_raw = pd.read_sql("SELECT id, source, dag_run_id, loaded_at, date_scraping FROM raw_leads", raw_conn)
            print(f"  [DB] {len(df_raw)} enregistrements charges depuis 'raw_leads'.")
        except Exception:
            df_raw = pd.DataFrame()
            print("  [DB] Table 'raw_leads' non disponible ou vide.")
    finally:
        raw_conn.close()

    return df_ent, df_raw


def load_mappings() -> tuple[dict, dict, dict, dict]:
    """Charge les dictionnaires de mapping depuis le pipeline."""
    pipeline_root = str(Path(__file__).resolve().parent.parent)
    if pipeline_root not in sys.path:
        sys.path.insert(0, pipeline_root)

    try:
        from mapping_naf import naf_codes
    except ImportError:
        naf_codes = {}

    try:
        from mapping import formes_juridiques, effectifs_insee, categories_entreprise
    except ImportError:
        formes_juridiques = effectifs_insee = categories_entreprise = {}

    return naf_codes, formes_juridiques, effectifs_insee, categories_entreprise


def generate_synthetic_data(n: int = 10_000) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Génère un jeu synthétique pour les démos."""
    rng = np.random.default_rng(42)

    sirens = [f"{rng.integers(100_000_000, 999_999_999)}" for _ in range(n)]
    for i in rng.choice(n, size=int(n * 0.02), replace=False):
        sirens[i] = sirens[i][:7]

    sirets = [f"{s}{rng.integers(10000, 99999)}" for s in sirens]
    for i in rng.choice(n, size=int(n * 0.03), replace=False):
        sirets[i] = f"99999999{rng.integers(100000, 999999)}"

    noms = [f"Entreprise-{i}" for i in range(n)]
    for i in rng.choice(n, size=int(n * 0.01), replace=False):
        noms[i] = None

    cps = [f"{rng.integers(1000, 95999):05d}" for _ in range(n)]
    for i in rng.choice(n, size=int(n * 0.03), replace=False):
        cps[i] = None

    villes = [f"VILLE-{rng.integers(1, 500)}" for _ in range(n)]
    for i in rng.choice(n, size=int(n * 0.02), replace=False):
        villes[i] = None

    cas = rng.exponential(500_000, size=n).round(2).tolist()
    for i in rng.choice(n, size=int(n * 0.20), replace=False):
        cas[i] = None
    for i in rng.choice(n, size=int(n * 0.005), replace=False):
        cas[i] = -abs(cas[i]) if cas[i] else -1000.0

    secteurs = ["Programmation informatique", "BTP", None, "62.01Z", "Commerce de gros"]
    secteur_activite = [rng.choice(secteurs) for _ in range(n)]

    telephones = [f"+33{rng.integers(600000000, 799999999)}" for _ in range(n)]
    for i in rng.choice(n, size=int(n * 0.35), replace=False):
        telephones[i] = None

    emails = [f"contact{i}@ent-{i}.fr" for i in range(n)]
    for i in rng.choice(n, size=int(n * 0.40), replace=False):
        emails[i] = None
    for i in rng.choice(n, size=int(n * 0.01), replace=False):
        emails[i] = "pas-un-email"

    formes = ["SARL", "SAS (Société par Actions Simplifiée)", None, "5710"]
    forme_juridique = [rng.choice(formes) for _ in range(n)]

    tailles = ["PME", "1 à 2 salariés", None, "03"]
    taille_entrep = [rng.choice(tailles) for _ in range(n)]

    categories = ["Microentreprise", "PME", None, "GE"]
    categorie_entreprise = [rng.choice(categories) for _ in range(n)]

    nb_locaux_list = [int(rng.integers(1, 50)) if rng.random() > 0.3 else None for _ in range(n)]

    dirigeants_list = []
    for i in range(n):
        if rng.random() > 0.25:
            ndirs = int(rng.integers(1, 4))
            dirs = []
            for d in range(ndirs):
                entry = {"nom": f"Nom-{i}-{d}", "prenom": f"Prenom-{i}-{d}",
                         "qualite": rng.choice(["PDG", "DG", "Gerant"]),
                         "nationalite": "Francaise"}
                if rng.random() > 0.70:
                    entry["linkedin"] = f"https://www.linkedin.com/in/dir-{i}-{d}"
                else:
                    entry["linkedin"] = None
                dirs.append(entry)
            dirigeants_list.append(dirs)
        else:
            dirigeants_list.append(None)

    base_date = datetime(2020, 1, 1)
    date_creation = [
        (base_date - timedelta(days=int(rng.integers(365, 20000)))).strftime("%Y-%m-%d")
        for _ in range(n)
    ]
    for i in rng.choice(n, size=int(n * 0.003), replace=False):
        date_creation[i] = (datetime.now() + timedelta(days=int(rng.integers(30, 365)))).strftime("%Y-%m-%d")

    now = datetime.now()
    created_at = [(now - timedelta(days=int(rng.integers(0, 90)))).isoformat() for _ in range(n)]
    updated_at = [(now - timedelta(days=int(rng.integers(0, 30)))).isoformat() for _ in range(n)]

    dup_indices = rng.choice(range(100, n), size=4, replace=False)
    for idx in dup_indices:
        sirens[idx] = sirens[0]

    df = pd.DataFrame({
        "identifiant": [f"ID-{i}" for i in range(n)],
        "siren": sirens, "siret": sirets, "nom": noms,
        "ville": villes, "code_postal": cps, "pays": ["France"] * n,
        "secteur_activite": secteur_activite, "forme_juridique": forme_juridique,
        "taille_entrep": taille_entrep, "categorie_entreprise": categorie_entreprise,
        "nb_locaux": nb_locaux_list, "ca": cas,
        "telephone": telephones, "adresse_email": emails,
        "date_creation_entreprise": date_creation,
        "dirigeants": dirigeants_list,
        "created_at": created_at, "updated_at": updated_at,
        "statut": [rng.choice(["Nouveau", "Contacte", "Qualifie", "Perdu"]) for _ in range(n)],
        "taux_completude": [round(rng.uniform(20, 100), 2) for _ in range(n)],
    })

    df_raw = pd.DataFrame({
        "id": range(n + 500),
        "source": [rng.choice(["dataGouv", "BOAMP"]) for _ in range(n + 500)],
        "loaded_at": [(now - timedelta(days=int(rng.integers(0, 90)))).isoformat() for _ in range(n + 500)],
    })

    print(f"  [SYNTHETIC] {len(df)} entreprises + {len(df_raw)} raw_leads generes.")
    return df, df_raw


# ══════════════════════════════════════════════════════════════
#  DQ RESULT MODEL
# ══════════════════════════════════════════════════════════════

@dataclass
class DQResult:
    dimension: str
    rule_name: str
    description: str
    total_records: int
    passing: int
    failing: int
    pass_rate: float
    severity: str = "INFO"
    sample_failures: list = field(default_factory=list)


# ══════════════════════════════════════════════════════════════
#  AUDITOR ENGINE
# ══════════════════════════════════════════════════════════════

class DataQualityAuditor:
    """
    Moteur d'audit DQ complet.  Travaille sur les vraies données de la base.
    """

    def __init__(self, df_ent: pd.DataFrame, df_raw: pd.DataFrame,
                 naf_codes: dict, formes_juridiques: dict,
                 effectifs_insee: dict, categories_entreprise: dict):
        self.df = df_ent.copy()
        self.df_raw = df_raw.copy() if not df_raw.empty else pd.DataFrame()
        self.naf_codes = naf_codes
        self.formes_juridiques = formes_juridiques
        self.effectifs_insee = effectifs_insee
        self.categories_entreprise = categories_entreprise
        self.results: list[DQResult] = []
        self.run_date = datetime.now().isoformat()

        # Build a set of all known mapped labels for quick lookup
        self.naf_labels = set(naf_codes.values()) if naf_codes else set()
        self.forme_labels = set(formes_juridiques.values()) if formes_juridiques else set()
        self.effectif_labels = set(effectifs_insee.values()) if effectifs_insee else set()
        self.categorie_labels = set(categories_entreprise.values()) if categories_entreprise else set()

    def _add(self, **kwargs):
        self.results.append(DQResult(**kwargs))

    # ──────────────────────────────────────────
    #  1. COMPLÉTUDE
    # ──────────────────────────────────────────

    def check_completeness(self):
        for field_name in ALL_COMPLETENESS_FIELDS:
            if field_name not in self.df.columns:
                continue
            total = len(self.df)

            if field_name == "dirigeants":
                filled = int(self.df[field_name].apply(
                    lambda x: isinstance(x, list) and len(x) > 0
                ).sum())
            elif self.df[field_name].dtype == "object":
                filled = int(self.df[field_name].apply(
                    lambda x: x is not None and not pd.isna(x) and str(x).strip() not in ("", "None", "nan")
                ).sum())
            else:
                filled = int(self.df[field_name].notna().sum())

            missing = total - filled
            rate = round(filled / total * 100, 2) if total > 0 else 0

            sev = "CRITICAL" if field_name in CRITICAL_FIELDS and rate < 95 else \
                  "WARNING" if rate < 70 else "INFO"

            self._add(dimension="Completude", rule_name=f"completude_{field_name}",
                      description=f"Champ '{field_name}' renseigne",
                      total_records=total, passing=filled, failing=missing,
                      pass_rate=rate, severity=sev)

        # LinkedIn des dirigeants
        if "dirigeants" in self.df.columns:
            total_d, with_li = 0, 0
            for dirs in self.df["dirigeants"].dropna():
                if isinstance(dirs, list):
                    for d in dirs:
                        if isinstance(d, dict):
                            total_d += 1
                            li = d.get("linkedin")
                            if li and str(li).strip() not in ("", "None"):
                                with_li += 1
            rate = round(with_li / total_d * 100, 2) if total_d > 0 else 0
            self._add(dimension="Completude", rule_name="completude_dirigeant_linkedin",
                      description="Profil LinkedIn renseigne par dirigeant",
                      total_records=total_d, passing=with_li, failing=total_d - with_li,
                      pass_rate=rate, severity="INFO")

    # ──────────────────────────────────────────
    #  2. UNICITÉ
    # ──────────────────────────────────────────

    def check_uniqueness(self):
        for col, label, sev in [("siren", "SIREN", "CRITICAL"), ("siret", "SIRET", "WARNING")]:
            if col not in self.df.columns:
                continue
            notna = self.df[self.df[col].notna()][col]
            counts = notna.value_counts()
            dups = counts[counts > 1]
            dup_rows = int(dups.sum() - len(dups))
            samples = [f"{col.upper()}={s} x{counts[s]}" for s in dups.head(5).index]

            self._add(dimension="Unicite", rule_name=f"unicite_{col}",
                      description=f"Chaque {label} doit etre unique",
                      total_records=len(notna), passing=len(notna) - dup_rows,
                      failing=dup_rows,
                      pass_rate=round((1 - dup_rows / len(notna)) * 100, 2) if len(notna) > 0 else 100,
                      severity=sev if dup_rows > 0 else "INFO",
                      sample_failures=samples)

        # Doublons (nom + code_postal)
        if "nom" in self.df.columns and "code_postal" in self.df.columns:
            sub = self.df.dropna(subset=["nom", "code_postal"])
            mask = sub.duplicated(subset=["nom", "code_postal"], keep=False)
            dup_count = int(mask.sum())
            groups = sub[mask].groupby(["nom", "code_postal"]).size()
            samples = [f"{nom} / {cp} x{cnt}" for (nom, cp), cnt in groups.head(5).items()]
            self._add(dimension="Unicite", rule_name="unicite_nom_cp",
                      description="(nom + code_postal) doit etre unique",
                      total_records=len(sub), passing=len(sub) - dup_count,
                      failing=dup_count,
                      pass_rate=round((1 - dup_count / len(sub)) * 100, 2) if len(sub) > 0 else 100,
                      severity="WARNING" if dup_count > 0 else "INFO",
                      sample_failures=samples)

    # ──────────────────────────────────────────
    #  3. VALIDITÉ
    # ──────────────────────────────────────────

    def check_validity(self):
        def _regex(col, pattern, rule, desc, sev="WARNING"):
            if col not in self.df.columns:
                return
            notna = self.df[self.df[col].notna()][col].astype(str)
            valid = notna.apply(lambda x: bool(pattern.match(x.strip())))
            fails = notna[~valid].head(5).tolist()
            self._add(dimension="Validite", rule_name=rule, description=desc,
                      total_records=len(notna), passing=int(valid.sum()),
                      failing=int((~valid).sum()),
                      pass_rate=round(valid.mean() * 100, 2) if len(notna) > 0 else 100,
                      severity=sev, sample_failures=fails)

        # Format SIREN / SIRET
        _regex("siren", SIREN_RE, "validite_siren_format",
               "SIREN = exactement 9 chiffres (standard INSEE)", "CRITICAL")
        _regex("siret", SIRET_RE, "validite_siret_format",
               "SIRET = exactement 14 chiffres (standard INSEE)", "CRITICAL")

        # Luhn checksum sur SIREN
        if "siren" in self.df.columns:
            valid_format = self.df[self.df["siren"].notna()]["siren"].astype(str)
            valid_format = valid_format[valid_format.apply(lambda x: bool(SIREN_RE.match(x)))]
            luhn_ok = valid_format.apply(luhn_checksum)
            fails = valid_format[~luhn_ok].head(5).tolist()
            self._add(dimension="Validite", rule_name="validite_siren_luhn",
                      description="SIREN passe la verification Luhn (checksum INSEE)",
                      total_records=len(valid_format), passing=int(luhn_ok.sum()),
                      failing=int((~luhn_ok).sum()),
                      pass_rate=round(luhn_ok.mean() * 100, 2) if len(valid_format) > 0 else 100,
                      severity="WARNING", sample_failures=fails)

        # Luhn checksum sur SIRET
        if "siret" in self.df.columns:
            valid_format = self.df[self.df["siret"].notna()]["siret"].astype(str)
            valid_format = valid_format[valid_format.apply(lambda x: bool(SIRET_RE.match(x)))]
            luhn_ok = valid_format.apply(luhn_checksum)
            fails = valid_format[~luhn_ok].head(5).tolist()
            self._add(dimension="Validite", rule_name="validite_siret_luhn",
                      description="SIRET passe la verification Luhn (checksum INSEE)",
                      total_records=len(valid_format), passing=int(luhn_ok.sum()),
                      failing=int((~luhn_ok).sum()),
                      pass_rate=round(luhn_ok.mean() * 100, 2) if len(valid_format) > 0 else 100,
                      severity="WARNING", sample_failures=fails)

        # Code postal
        _regex("code_postal", CP_RE, "validite_code_postal",
               "Code postal = 5 chiffres (format La Poste)")

        # Email
        _regex("adresse_email", EMAIL_RE, "validite_email",
               "Email au format RFC (xxx@yyy.zz)")

        # Téléphone E.164
        _regex("telephone", PHONE_E164_RE, "validite_telephone",
               "Telephone au format E.164 (+33XXXXXXXXX)")

        # CA > 0
        if "ca" in self.df.columns:
            ca_notna = self.df[self.df["ca"].notna()]["ca"]
            pos = ca_notna > 0
            fails = [str(v) for v in ca_notna[~pos].head(5)]
            self._add(dimension="Validite", rule_name="validite_ca_positif",
                      description="Chiffre d'affaires strictement positif",
                      total_records=len(ca_notna), passing=int(pos.sum()),
                      failing=int((~pos).sum()),
                      pass_rate=round(pos.mean() * 100, 2) if len(ca_notna) > 0 else 100,
                      severity="WARNING", sample_failures=fails)

        # ── SECTEUR D'ACTIVITÉ — mapping coverage ──
        if "secteur_activite" in self.df.columns and self.naf_labels:
            notna = self.df[self.df["secteur_activite"].notna()]["secteur_activite"].astype(str)
            notna = notna[notna.str.strip() != ""]

            def is_mapped(val):
                val = val.strip()
                # It's a proper label (found in naf_codes values)
                if val in self.naf_labels:
                    return True
                # It still looks like a raw NAF code → NOT mapped
                if NAF_RE.match(val.replace(".", "")):
                    return False
                # It's some text but not in our known labels → could be a label
                # from BOAMP secteur mapping or a raw code we don't know
                return True  # give benefit of the doubt for text labels

            mapped = notna.apply(is_mapped)
            unmapped_samples = notna[~mapped].value_counts().head(10)
            fails = [f"{code} (x{cnt})" for code, cnt in unmapped_samples.items()]

            self._add(dimension="Validite", rule_name="validite_secteur_naf_mapping",
                      description="Secteur d'activite mappe vers un label NAF lisible (pas un code brut)",
                      total_records=len(notna), passing=int(mapped.sum()),
                      failing=int((~mapped).sum()),
                      pass_rate=round(mapped.mean() * 100, 2) if len(notna) > 0 else 100,
                      severity="WARNING" if int((~mapped).sum()) > 0 else "INFO",
                      sample_failures=fails)

        # ── FORME JURIDIQUE — mapping coverage ──
        if "forme_juridique" in self.df.columns and self.forme_labels:
            notna = self.df[self.df["forme_juridique"].notna()]["forme_juridique"].astype(str)
            notna = notna[notna.str.strip() != ""]

            def is_forme_mapped(val):
                val = val.strip()
                if val in self.forme_labels:
                    return True
                # Raw numeric code still present → not mapped
                if val.isdigit():
                    return False
                return True

            mapped = notna.apply(is_forme_mapped)
            unmapped_samples = notna[~mapped].value_counts().head(10)
            fails = [f"code={code} (x{cnt})" for code, cnt in unmapped_samples.items()]

            self._add(dimension="Validite", rule_name="validite_forme_juridique_mapping",
                      description="Forme juridique mappee vers un label lisible (pas un code brut)",
                      total_records=len(notna), passing=int(mapped.sum()),
                      failing=int((~mapped).sum()),
                      pass_rate=round(mapped.mean() * 100, 2) if len(notna) > 0 else 100,
                      severity="WARNING" if int((~mapped).sum()) > 0 else "INFO",
                      sample_failures=fails)

        # ── TAILLE ENTREPRISE — mapping coverage ──
        if "taille_entrep" in self.df.columns and self.effectif_labels:
            notna = self.df[self.df["taille_entrep"].notna()]["taille_entrep"].astype(str)
            notna = notna[notna.str.strip() != ""]

            def is_taille_mapped(val):
                val = val.strip()
                if val in self.effectif_labels:
                    return True
                if len(val) <= 2 and val.isalnum():  # raw INSEE code like "03", "NN"
                    return False
                return True

            mapped = notna.apply(is_taille_mapped)
            fails = [f"code={c} (x{n})" for c, n in notna[~mapped].value_counts().head(10).items()]
            self._add(dimension="Validite", rule_name="validite_taille_mapping",
                      description="Taille entreprise mappee vers un label INSEE lisible",
                      total_records=len(notna), passing=int(mapped.sum()),
                      failing=int((~mapped).sum()),
                      pass_rate=round(mapped.mean() * 100, 2) if len(notna) > 0 else 100,
                      severity="WARNING" if int((~mapped).sum()) > 0 else "INFO",
                      sample_failures=fails)

        # LinkedIn URL valide
        if "dirigeants" in self.df.columns:
            total_li, valid_li = 0, 0
            invalid_samples = []
            for dirs in self.df["dirigeants"].dropna():
                if isinstance(dirs, list):
                    for d in dirs:
                        if isinstance(d, dict):
                            li = d.get("linkedin")
                            if li and str(li).strip() not in ("", "None"):
                                total_li += 1
                                if LINKEDIN_RE.match(str(li)):
                                    valid_li += 1
                                elif len(invalid_samples) < 5:
                                    invalid_samples.append(str(li))
            self._add(dimension="Validite", rule_name="validite_linkedin_url",
                      description="Profil LinkedIn = URL linkedin.com/in/ valide",
                      total_records=total_li, passing=valid_li,
                      failing=total_li - valid_li,
                      pass_rate=round(valid_li / total_li * 100, 2) if total_li > 0 else 100,
                      severity="INFO", sample_failures=invalid_samples)

    # ──────────────────────────────────────────
    #  4. COHÉRENCE
    # ──────────────────────────────────────────

    def check_consistency(self):
        # SIRET[:9] == SIREN
        if "siren" in self.df.columns and "siret" in self.df.columns:
            both = self.df.dropna(subset=["siren", "siret"])
            if len(both) > 0:
                ok = both.apply(lambda r: str(r["siret"])[:9] == str(r["siren"]), axis=1)
                fails = both[~ok][["siren", "siret"]].head(5).to_dict("records")
                self._add(dimension="Coherence", rule_name="coherence_siret_siren",
                          description="SIRET[:9] == SIREN (meme entite legale)",
                          total_records=len(both), passing=int(ok.sum()),
                          failing=int((~ok).sum()),
                          pass_rate=round(ok.mean() * 100, 2),
                          severity="CRITICAL",
                          sample_failures=[f"SIREN={r['siren']} vs SIRET={r['siret']}" for r in fails])

        # Date création <= aujourd'hui
        if "date_creation_entreprise" in self.df.columns:
            dates = pd.to_datetime(self.df["date_creation_entreprise"], errors="coerce")
            valid = dates.dropna()
            today = pd.Timestamp(datetime.now().date())
            ok = valid <= today
            fails = valid[~ok].head(5).dt.strftime("%Y-%m-%d").tolist()
            self._add(dimension="Coherence", rule_name="coherence_date_creation_passee",
                      description="Date de creation <= aujourd'hui (pas dans le futur)",
                      total_records=len(valid), passing=int(ok.sum()),
                      failing=int((~ok).sum()),
                      pass_rate=round(ok.mean() * 100, 2) if len(valid) > 0 else 100,
                      severity="WARNING", sample_failures=fails)

        # Code postal[:2] cohérent avec département (01-95, 97x, 98x)
        if "code_postal" in self.df.columns:
            cp_notna = self.df[self.df["code_postal"].notna()]["code_postal"].astype(str)
            cp_valid = cp_notna[cp_notna.apply(lambda x: bool(CP_RE.match(x.strip())))]

            def cp_dept_valid(cp):
                cp = cp.strip()
                dept = int(cp[:2])
                if dept == 0:
                    return False
                if 1 <= dept <= 95:
                    return True
                if dept in (97, 98):  # DOM-TOM
                    return True
                return False

            ok = cp_valid.apply(cp_dept_valid)
            fails = cp_valid[~ok].head(5).tolist()
            self._add(dimension="Coherence", rule_name="coherence_cp_departement",
                      description="Code postal[:2] = departement valide (01-95, 97x, 98x)",
                      total_records=len(cp_valid), passing=int(ok.sum()),
                      failing=int((~ok).sum()),
                      pass_rate=round(ok.mean() * 100, 2) if len(cp_valid) > 0 else 100,
                      severity="INFO", sample_failures=fails)

        # Identifiant cohérent (doit == siren pour dataGouv)
        if "identifiant" in self.df.columns and "siren" in self.df.columns:
            both = self.df.dropna(subset=["identifiant", "siren"])
            # Identifiant should be siren (9) or siret-based (14+)
            valid_id = both.apply(
                lambda r: str(r["identifiant"]).strip() != "" and len(str(r["identifiant"]).strip()) <= 25,
                axis=1
            )
            self._add(dimension="Coherence", rule_name="coherence_identifiant_length",
                      description="Identifiant est non-vide et <= 25 caracteres (VARCHAR 25)",
                      total_records=len(both), passing=int(valid_id.sum()),
                      failing=int((~valid_id).sum()),
                      pass_rate=round(valid_id.mean() * 100, 2) if len(both) > 0 else 100,
                      severity="INFO")

        # taux_completude est cohérent (entre 0 et 100)
        if "taux_completude" in self.df.columns:
            tc = self.df[self.df["taux_completude"].notna()]["taux_completude"]
            ok = (tc >= 0) & (tc <= 100)
            fails = [str(v) for v in tc[~ok].head(5)]
            self._add(dimension="Coherence", rule_name="coherence_taux_completude",
                      description="taux_completude entre 0 et 100",
                      total_records=len(tc), passing=int(ok.sum()),
                      failing=int((~ok).sum()),
                      pass_rate=round(ok.mean() * 100, 2) if len(tc) > 0 else 100,
                      severity="INFO", sample_failures=fails)

    # ──────────────────────────────────────────
    #  6. COHÉRENCE MÉTIER (business rules)
    # ──────────────────────────────────────────

    def _get_age_years(self, row):
        """Calcule l'âge de l'entreprise en années depuis date_creation_entreprise."""
        try:
            d = pd.to_datetime(row, errors="coerce")
            if pd.isna(d):
                return None
            return round((datetime.now() - d.to_pydatetime()).days / 365.25, 1)
        except Exception:
            return None

    def _get_employees(self, taille):
        """Extrait un nombre estimé d'employés depuis le label taille_entrep."""
        if pd.isna(taille) or not taille:
            return None
        return TAILLE_TO_EMPLOYEES.get(str(taille).strip())

    def check_business_coherence(self):
        """Règles de cohérence métier : Âge/Taille, Taille/CA, Âge/CA, Ratio CA/Employé."""

        # ── Préparer les colonnes dérivées ──
        df = self.df.copy()
        if "date_creation_entreprise" in df.columns:
            df["_age_years"] = df["date_creation_entreprise"].apply(self._get_age_years)
        else:
            df["_age_years"] = None
        if "taille_entrep" in df.columns:
            df["_employees"] = df["taille_entrep"].apply(self._get_employees)
        else:
            df["_employees"] = None

        # ── 6a. Cohérence Âge / Taille ──
        # Une entreprise de moins de 3 ans ne devrait pas avoir > 1000 employés
        sub = df.dropna(subset=["_age_years", "_employees"])
        if len(sub) > 0:
            def age_taille_ok(r):
                if r["_age_years"] < 3 and r["_employees"] > 1000:
                    return False
                return True
            ok = sub.apply(age_taille_ok, axis=1)
            fails = sub[~ok][["nom", "_age_years", "_employees"]].head(5)
            samples = [f"{r['nom']}: age={r['_age_years']}ans, emp={r['_employees']}" for _, r in fails.iterrows()]
            self._add(dimension="Coherence_Metier", rule_name="coherence_age_taille",
                      description="Entreprise < 3 ans ne devrait pas avoir > 1000 employes",
                      total_records=len(sub), passing=int(ok.sum()), failing=int((~ok).sum()),
                      pass_rate=round(ok.mean() * 100, 2),
                      severity="CRITICAL" if int((~ok).sum()) > 0 else "INFO",
                      sample_failures=samples)

        # ── 6b. Cohérence Taille / Chiffre d'Affaires ──
        # Une entreprise > 500 employés ne devrait pas avoir un CA < 1M€
        sub = df.dropna(subset=["_employees", "ca"])
        if len(sub) > 0:
            def taille_ca_ok(r):
                if r["_employees"] > 500 and r["ca"] < 1_000_000:
                    return False
                if r["_employees"] < 5 and r["ca"] > 500_000_000:
                    return False
                return True
            ok = sub.apply(taille_ca_ok, axis=1)
            fails = sub[~ok][["nom", "_employees", "ca"]].head(5)
            samples = [f"{r['nom']}: emp={r['_employees']}, CA={r['ca']:,.0f}EUR" for _, r in fails.iterrows()]
            self._add(dimension="Coherence_Metier", rule_name="coherence_taille_ca",
                      description="Entreprise > 500 emp ne devrait pas avoir CA < 1M. Petite < 5 emp pas CA > 500M",
                      total_records=len(sub), passing=int(ok.sum()), failing=int((~ok).sum()),
                      pass_rate=round(ok.mean() * 100, 2),
                      severity="CRITICAL" if int((~ok).sum()) > 0 else "INFO",
                      sample_failures=samples)

        # ── 6c. Cohérence Âge / CA ──
        # Entreprise < 2 ans : CA ne devrait pas dépasser 100M€
        sub = df.dropna(subset=["_age_years", "ca"])
        if len(sub) > 0:
            def age_ca_ok(r):
                if r["_age_years"] < 2 and r["ca"] > 100_000_000:
                    return False
                return True
            ok = sub.apply(age_ca_ok, axis=1)
            fails = sub[~ok][["nom", "_age_years", "ca"]].head(5)
            samples = [f"{r['nom']}: age={r['_age_years']}ans, CA={r['ca']:,.0f}EUR" for _, r in fails.iterrows()]
            self._add(dimension="Coherence_Metier", rule_name="coherence_age_ca",
                      description="Entreprise < 2 ans ne devrait pas avoir CA > 100M EUR",
                      total_records=len(sub), passing=int(ok.sum()), failing=int((~ok).sum()),
                      pass_rate=round(ok.mean() * 100, 2),
                      severity="CRITICAL" if int((~ok).sum()) > 0 else "INFO",
                      sample_failures=samples)

        # ── 6d. Ratio CA par Employé ──
        # Le ratio doit être réaliste : entre 10K€ et 2M€ par employé
        sub = df.dropna(subset=["_employees", "ca"])
        sub = sub[sub["_employees"] > 0]
        if len(sub) > 0:
            sub = sub.copy()
            sub["_ratio"] = sub["ca"] / sub["_employees"]
            ok = (sub["_ratio"] >= 10_000) & (sub["_ratio"] <= 2_000_000)
            fails = sub[~ok][["nom", "ca", "_employees", "_ratio"]].head(5)
            samples = [f"{r['nom']}: CA={r['ca']:,.0f}, emp={r['_employees']}, ratio={r['_ratio']:,.0f}EUR/emp"
                       for _, r in fails.iterrows()]
            avg_ratio = round(sub["_ratio"].mean(), 0)
            self._add(dimension="Coherence_Metier", rule_name="ratio_ca_par_employe",
                      description=f"Ratio CA/employe doit etre entre 10K et 2M EUR (moyenne: {avg_ratio:,.0f} EUR)",
                      total_records=len(sub), passing=int(ok.sum()), failing=int((~ok).sum()),
                      pass_rate=round(ok.mean() * 100, 2),
                      severity="CRITICAL" if int((~ok).sum()) > 0 else "INFO",
                      sample_failures=samples)

    # ──────────────────────────────────────────
    #  7. STANDARDISATION
    # ──────────────────────────────────────────

    def check_standardization(self):
        """Vérifie que les champs catégoriels utilisent des valeurs prédéfinies (picklists)."""

        # ── 7a. Statut du lead ──
        if "statut" in self.df.columns:
            notna = self.df[self.df["statut"].notna()]["statut"].astype(str)
            notna = notna[notna.str.strip() != ""]
            ok = notna.apply(lambda x: x.strip() in STATUTS_AUTORISES)
            fails = [f"'{v}'" for v in notna[~ok].value_counts().head(5).index]
            self._add(dimension="Standardisation", rule_name="standardisation_statut",
                      description="Le statut du lead doit etre dans la liste predéfinie (Nouveau, Contacte, Qualifie, Perdu, Gagne)",
                      total_records=len(notna), passing=int(ok.sum()), failing=int((~ok).sum()),
                      pass_rate=round(ok.mean() * 100, 2) if len(notna) > 0 else 100,
                      severity="WARNING" if int((~ok).sum()) > 0 else "INFO",
                      sample_failures=fails)

        # ── 7b. Pays ──
        if "pays" in self.df.columns:
            notna = self.df[self.df["pays"].notna()]["pays"].astype(str)
            notna = notna[notna.str.strip() != ""]
            ok = notna.apply(lambda x: x.strip() in ("France", "FRANCE", "france", "FR"))
            fails = [f"'{v}' x{n}" for v, n in notna[~ok].value_counts().head(5).items()]
            self._add(dimension="Standardisation", rule_name="standardisation_pays",
                      description="Le pays doit etre 'France' (valeur standardisee)",
                      total_records=len(notna), passing=int(ok.sum()), failing=int((~ok).sum()),
                      pass_rate=round(ok.mean() * 100, 2) if len(notna) > 0 else 100,
                      severity="INFO", sample_failures=fails)

        # ── 7c. Catégorie entreprise ──
        if "categorie_entreprise" in self.df.columns:
            cats_valides = {"Microentreprise", "Petite et Moyenne Entreprise",
                            "Entreprise de Taille Intermédiaire", "Grande Entreprise",
                            "PME", "ETI", "GE", "MIC"}
            notna = self.df[self.df["categorie_entreprise"].notna()]["categorie_entreprise"].astype(str)
            notna = notna[notna.str.strip() != ""]
            ok = notna.apply(lambda x: x.strip() in cats_valides)
            fails = [f"'{v}' x{n}" for v, n in notna[~ok].value_counts().head(5).items()]
            self._add(dimension="Standardisation", rule_name="standardisation_categorie",
                      description="Categorie entreprise doit etre MIC/PME/ETI/GE ou label INSEE equivalent",
                      total_records=len(notna), passing=int(ok.sum()), failing=int((~ok).sum()),
                      pass_rate=round(ok.mean() * 100, 2) if len(notna) > 0 else 100,
                      severity="WARNING" if int((~ok).sum()) > 0 else "INFO",
                      sample_failures=fails)

    # ──────────────────────────────────────────
    #  8. COHÉRENCE MULTI-SOURCES
    # ──────────────────────────────────────────

    def check_multi_source_coherence(self):
        """Vérifie la cohérence des données provenant de sources multiples (DataGouv + BOAMP)."""

        if "sources" not in self.df.columns:
            return

        # Compter les entreprises avec données de sources multiples
        def has_multiple_sources(sources):
            if not isinstance(sources, dict):
                return False
            src_values = set()
            for v in sources.values():
                if isinstance(v, str):
                    src_values.add(v)
            return len(src_values) > 1

        multi = self.df[self.df["sources"].apply(has_multiple_sources)]
        single = self.df[~self.df.index.isin(multi.index)]

        self._add(dimension="Coherence_MultiSource", rule_name="multi_source_couverture",
                  description=f"Entreprises enrichies par sources multiples (DataGouv + BOAMP). Multi-source = meilleure qualite",
                  total_records=len(self.df), passing=len(multi),
                  failing=len(single),
                  pass_rate=round(len(multi) / len(self.df) * 100, 2) if len(self.df) > 0 else 0,
                  severity="INFO")

        # Vérifier que les entreprises BOAMP ont un SIRET (leur source primaire d'identifiant)
        if "siret" in self.df.columns and "info_boamp" in self.df.columns:
            boamp_rows = self.df[self.df["info_boamp"].notna()]
            if len(boamp_rows) > 0:
                has_siret = boamp_rows["siret"].notna() & (boamp_rows["siret"].astype(str).str.strip() != "")
                fails = boamp_rows[~has_siret]["nom"].head(5).tolist()
                self._add(dimension="Coherence_MultiSource", rule_name="multi_source_boamp_siret",
                          description="Leads BOAMP doivent avoir un SIRET (identifiant source primaire BOAMP)",
                          total_records=len(boamp_rows), passing=int(has_siret.sum()),
                          failing=int((~has_siret).sum()),
                          pass_rate=round(has_siret.mean() * 100, 2),
                          severity="WARNING" if int((~has_siret).sum()) > 0 else "INFO",
                          sample_failures=fails)

    # ──────────────────────────────────────────
    #  9. PERTINENCE DE L'ENRICHISSEMENT
    # ──────────────────────────────────────────

    def check_enrichment_pertinence(self):
        """Vérifie que les données enrichies sont pertinentes pour un CRM B2B."""

        # Les dirigeants doivent avoir au minimum un nom
        if "dirigeants" in self.df.columns:
            total_dirs, valid_dirs = 0, 0
            invalid_samples = []
            for dirs in self.df["dirigeants"].dropna():
                if isinstance(dirs, list):
                    for d in dirs:
                        if isinstance(d, dict):
                            total_dirs += 1
                            nom = d.get("nom", "")
                            prenom = d.get("prenom", "")
                            if nom and str(nom).strip() not in ("", "None", "null"):
                                valid_dirs += 1
                            elif len(invalid_samples) < 5:
                                invalid_samples.append(f"dirigeant sans nom: {d}")
            if total_dirs > 0:
                self._add(dimension="Pertinence", rule_name="pertinence_dirigeant_nom",
                          description="Chaque dirigeant enrichi doit avoir au minimum un nom",
                          total_records=total_dirs, passing=valid_dirs,
                          failing=total_dirs - valid_dirs,
                          pass_rate=round(valid_dirs / total_dirs * 100, 2),
                          severity="WARNING" if total_dirs - valid_dirs > 0 else "INFO",
                          sample_failures=invalid_samples)

        # Les dirigeants doivent avoir une qualité/rôle (PDG, DG, Gérant...)
        if "dirigeants" in self.df.columns:
            total_dirs, with_role = 0, 0
            for dirs in self.df["dirigeants"].dropna():
                if isinstance(dirs, list):
                    for d in dirs:
                        if isinstance(d, dict):
                            total_dirs += 1
                            q = d.get("qualite", "") or d.get("role", "")
                            if q and str(q).strip() not in ("", "None", "null"):
                                with_role += 1
            if total_dirs > 0:
                self._add(dimension="Pertinence", rule_name="pertinence_dirigeant_role",
                          description="Dirigeant doit avoir un role/qualite (PDG, DG, Gerant) pour la prospection",
                          total_records=total_dirs, passing=with_role,
                          failing=total_dirs - with_role,
                          pass_rate=round(with_role / total_dirs * 100, 2),
                          severity="INFO")

    # ──────────────────────────────────────────
    #  10. COHÉRENCE SECTEUR / TAILLE
    # ──────────────────────────────────────────

    def check_sector_coherence(self):
        """Vérifie la cohérence entre le secteur d'activité et d'autres champs."""

        df = self.df.copy()
        if "taille_entrep" in df.columns:
            df["_employees"] = df["taille_entrep"].apply(self._get_employees)
        else:
            return

        # ── 10a. Secteur / Taille Moyenne ──
        # Les secteurs artisanaux/libéraux ne devraient pas avoir > 5000 employés
        if "secteur_activite" in df.columns:
            secteurs_petits = ["Boulangerie", "Pâtisserie", "Coiffure", "Boucherie",
                               "Profession libérale", "Artisan"]
            sub = df.dropna(subset=["secteur_activite", "_employees"])
            if len(sub) > 0:
                def secteur_taille_ok(r):
                    sa = str(r["secteur_activite"]).strip()
                    for s in secteurs_petits:
                        if s.lower() in sa.lower() and r["_employees"] > 5000:
                            return False
                    return True
                ok = sub.apply(secteur_taille_ok, axis=1)
                fails = sub[~ok][["nom", "secteur_activite", "_employees"]].head(5)
                samples = [f"{r['nom']}: secteur={r['secteur_activite']}, emp={r['_employees']}"
                           for _, r in fails.iterrows()]
                self._add(dimension="Coherence_Metier", rule_name="coherence_secteur_taille",
                          description="Secteurs artisanaux/liberaux ne devraient pas avoir > 5000 employes",
                          total_records=len(sub), passing=int(ok.sum()), failing=int((~ok).sum()),
                          pass_rate=round(ok.mean() * 100, 2) if len(sub) > 0 else 100,
                          severity="WARNING" if int((~ok).sum()) > 0 else "INFO",
                          sample_failures=samples)

        # ── 10b. Secteur réglementé / Localisation ──
        if "secteur_activite" in df.columns and "code_postal" in df.columns:
            sub = df.dropna(subset=["secteur_activite", "code_postal"])
            if len(sub) > 0:
                def is_regulated(sa):
                    for s in SECTEURS_REGLEMENTES:
                        if s.lower() in str(sa).lower():
                            return True
                    return False
                regulated = sub[sub["secteur_activite"].apply(is_regulated)]
                if len(regulated) > 0:
                    # Vérifier que les entreprises réglementées sont en France métropolitaine ou DOM-TOM
                    ok = regulated["code_postal"].astype(str).apply(
                        lambda cp: bool(CP_RE.match(cp.strip())) and 1 <= int(cp.strip()[:2]) <= 98
                    )
                    fails = regulated[~ok][["nom", "secteur_activite", "code_postal"]].head(5)
                    samples = [f"{r['nom']}: secteur={r['secteur_activite']}, CP={r['code_postal']}"
                               for _, r in fails.iterrows()]
                    self._add(dimension="Coherence_Metier", rule_name="coherence_localisation_reglementation",
                              description="Entreprises de secteurs reglementes (finance, sante) doivent avoir un CP valide en France",
                              total_records=len(regulated), passing=int(ok.sum()), failing=int((~ok).sum()),
                              pass_rate=round(ok.mean() * 100, 2) if len(regulated) > 0 else 100,
                              severity="IMPORTANT" if int((~ok).sum()) > 0 else "INFO",
                              sample_failures=samples)

    # ──────────────────────────────────────────
    #  11. ORTHOGRAPHE ET GRAMMAIRE
    # ──────────────────────────────────────────

    def check_orthography(self):
        """Vérifie la capitalisation et le formatage des noms propres."""

        # ── 11a. Nom d'entreprise : capitalisation correcte ──
        if "nom" in self.df.columns:
            notna = self.df[self.df["nom"].notna()]["nom"].astype(str)
            notna = notna[notna.str.strip() != ""]

            def nom_capitalisation_ok(nom):
                nom = nom.strip()
                if not nom:
                    return True
                # Tout en minuscules = mauvais
                if nom == nom.lower() and len(nom) > 3:
                    return False
                return True

            ok = notna.apply(nom_capitalisation_ok)
            fails = notna[~ok].head(5).tolist()
            self._add(dimension="Orthographe", rule_name="orthographe_nom_capitalisation",
                      description="Le nom d'entreprise ne doit pas etre tout en minuscules",
                      total_records=len(notna), passing=int(ok.sum()), failing=int((~ok).sum()),
                      pass_rate=round(ok.mean() * 100, 2) if len(notna) > 0 else 100,
                      severity="INFO", sample_failures=fails)

        # ── 11b. Ville : capitalisation correcte ──
        if "ville" in self.df.columns:
            notna = self.df[self.df["ville"].notna()]["ville"].astype(str)
            notna = notna[notna.str.strip() != ""]

            def ville_format_ok(v):
                v = v.strip()
                if not v:
                    return True
                # Les villes françaises sont généralement en MAJUSCULES ou Title Case
                # Tout en minuscules sans aucune majuscule = mauvais
                if v == v.lower() and len(v) > 2:
                    return False
                return True

            ok = notna.apply(ville_format_ok)
            fails = notna[~ok].head(5).tolist()
            self._add(dimension="Orthographe", rule_name="orthographe_ville_capitalisation",
                      description="La ville ne doit pas etre tout en minuscules",
                      total_records=len(notna), passing=int(ok.sum()), failing=int((~ok).sum()),
                      pass_rate=round(ok.mean() * 100, 2) if len(notna) > 0 else 100,
                      severity="INFO", sample_failures=fails)

        # ── 11c. Espaces doubles ──
        all_text_fields = ["nom", "ville", "secteur_activite", "forme_juridique"]
        total, double_space = 0, 0
        samples = []
        for f in all_text_fields:
            if f in self.df.columns:
                for val in self.df[f].dropna().astype(str):
                    val = val.strip()
                    if val:
                        total += 1
                        if "  " in val:
                            double_space += 1
                            if len(samples) < 5:
                                samples.append(f"{f}: '{val}'")
        if total > 0:
            self._add(dimension="Orthographe", rule_name="orthographe_espaces_doubles",
                      description="Les champs texte ne doivent pas contenir d'espaces doubles",
                      total_records=total, passing=total - double_space, failing=double_space,
                      pass_rate=round((1 - double_space / total) * 100, 2),
                      severity="INFO", sample_failures=samples)

    # ──────────────────────────────────────────
    #  FRAÎCHEUR (original section 5)
    # ──────────────────────────────────────────

    def check_freshness(self):
        now = pd.Timestamp.now(tz="UTC")

        if "created_at" in self.df.columns:
            created = pd.to_datetime(self.df["created_at"], errors="coerce").dropna()
            if len(created) > 0:
                ages = (now - created).dt.days
                avg = round(float(ages.mean()), 1)
                mx = int(ages.max())
                fresh = int((ages <= 30).sum())
                self._add(dimension="Fraicheur", rule_name="fraicheur_age_moyen",
                          description=f"Age moyen: {avg}j, max: {mx}j. Enregistrements < 30j",
                          total_records=len(created), passing=fresh,
                          failing=len(created) - fresh,
                          pass_rate=round(fresh / len(created) * 100, 2),
                          severity="INFO")

        if "updated_at" in self.df.columns:
            updated = pd.to_datetime(self.df["updated_at"], errors="coerce").dropna()
            if len(updated) > 0:
                stale = (now - updated).dt.days
                stale_7 = int((stale > 7).sum())
                self._add(dimension="Fraicheur", rule_name="fraicheur_maj_7j",
                          description="Mis a jour dans les 7 derniers jours",
                          total_records=len(updated), passing=len(updated) - stale_7,
                          failing=stale_7,
                          pass_rate=round((1 - stale_7 / len(updated)) * 100, 2),
                          severity="WARNING" if stale_7 / len(updated) > 0.5 else "INFO")

        # Raw → Clean drop rate
        if not self.df_raw.empty:
            n_raw = len(self.df_raw)
            n_clean = len(self.df)
            drop_rate = round((1 - n_clean / n_raw) * 100, 2) if n_raw > 0 else 0
            self._add(dimension="Fraicheur", rule_name="fraicheur_raw_clean_ratio",
                      description=f"raw_leads ({n_raw}) -> entreprise ({n_clean}). Drop-rate = taux de perte au nettoyage",
                      total_records=n_raw, passing=n_clean, failing=n_raw - n_clean,
                      pass_rate=round(n_clean / n_raw * 100, 2) if n_raw > 0 else 100,
                      severity="WARNING" if drop_rate > 30 else "INFO")

    # ══════════════════════════════════════════════════════════════
    #  ORCHESTRATION
    # ══════════════════════════════════════════════════════════════

    def run_all(self) -> list[DQResult]:
        print("\n" + "=" * 72)
        print("  AUDIT QUALITE DES DONNEES -- Pipeline ETL CRM Prospection B2B")
        print("=" * 72 + "\n")

        steps = [
            ("1/11", "Completude",           self.check_completeness),
            ("2/11", "Unicite",              self.check_uniqueness),
            ("3/11", "Validite",             self.check_validity),
            ("4/11", "Coherence",            self.check_consistency),
            ("5/11", "Coherence_Metier",     self.check_business_coherence),
            ("6/11", "Standardisation",      self.check_standardization),
            ("7/11", "Multi-sources",        self.check_multi_source_coherence),
            ("8/11", "Pertinence",           self.check_enrichment_pertinence),
            ("9/11", "Secteur_Coherence",    self.check_sector_coherence),
            ("10/11", "Orthographe",         self.check_orthography),
            ("11/11", "Fraicheur",           self.check_freshness),
        ]
        for step, name, fn in steps:
            print(f"  [{step}] {name} ...")
            fn()

        print(f"\n  => {len(self.results)} regles evaluees.\n")
        return self.results

    def print_report(self):
        total_rules = len(self.results)
        critical = sum(1 for r in self.results if r.severity == "CRITICAL" and r.failing > 0)
        warnings = sum(1 for r in self.results if r.severity == "WARNING" and r.failing > 0)
        passing = sum(1 for r in self.results if r.failing == 0)
        overall = round(sum(r.pass_rate for r in self.results) / total_rules, 2) if total_rules > 0 else 0
        grade = "[PASS]" if overall >= 90 else "[WARN]" if overall >= 75 else "[FAIL]"

        print("+" + "-" * 70 + "+")
        print(f"|{'RESUME EXECUTIF':^70}|")
        print("+" + "-" * 70 + "+")
        print(f"|  Date           : {self.run_date:<50} |")
        print(f"|  Enregistrements: {len(self.df):<50} |")
        print(f"|  Regles         : {total_rules:<50} |")
        print(f"|  Score global   : {grade} {overall}%{'':<43}|")
        print(f"|  CRITICAL       : {critical:<50} |")
        print(f"|  WARNING        : {warnings:<50} |")
        print(f"|  OK             : {passing:<50} |")
        print("+" + "-" * 70 + "+")

        dimensions = ["Completude", "Unicite", "Validite", "Coherence",
                      "Coherence_Metier", "Standardisation", "Coherence_MultiSource",
                      "Pertinence", "Orthographe", "Fraicheur"]
        for dim in dimensions:
            dim_r = [r for r in self.results if r.dimension == dim]
            if not dim_r:
                continue
            print(f"\n--- {dim.upper()} {'---' * 20}")
            print(f"  {'Regle':<40} {'Pass%':>7} {'OK':>7} {'KO':>7} Sev")
            print(f"  {'-' * 40} {'-' * 7} {'-' * 7} {'-' * 7} {'-' * 8}")
            for r in dim_r:
                tag = "[!!]" if r.severity == "CRITICAL" else "[! ]" if r.severity == "WARNING" else "[OK]"
                name = r.rule_name[:40]
                print(f"  {name:<40} {r.pass_rate:>6.1f}% {r.passing:>7} {r.failing:>7} {tag} {r.severity}")
                if r.sample_failures:
                    for s in r.sample_failures[:3]:
                        print(f"    -> ex: {str(s)[:60]}")

    def export_json(self, output_dir: str = "reports") -> str:
        os.makedirs(output_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(output_dir, f"dq_audit_{ts}.json")

        total_rules = len(self.results)
        report = {
            "meta": {
                "run_date": self.run_date,
                "total_records_entreprise": len(self.df),
                "total_records_raw": len(self.df_raw),
                "total_rules": total_rules,
                "overall_pass_rate": round(
                    sum(r.pass_rate for r in self.results) / total_rules, 2
                ) if total_rules > 0 else 0,
                "critical_failures": sum(1 for r in self.results if r.severity == "CRITICAL" and r.failing > 0),
                "warning_failures": sum(1 for r in self.results if r.severity == "WARNING" and r.failing > 0),
            },
            "by_dimension": {},
            "results": [asdict(r) for r in self.results],
        }

        for dim in ["Completude", "Unicite", "Validite", "Coherence",
                    "Coherence_Metier", "Standardisation", "Coherence_MultiSource",
                    "Pertinence", "Orthographe", "Fraicheur"]:
            dim_r = [r for r in self.results if r.dimension == dim]
            if dim_r:
                report["by_dimension"][dim] = {
                    "avg_pass_rate": round(sum(r.pass_rate for r in dim_r) / len(dim_r), 2),
                    "nb_rules": len(dim_r),
                    "nb_failures": sum(1 for r in dim_r if r.failing > 0),
                }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        print(f"\n  Rapport JSON exporte : {path}")
        return path


# ══════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Audit Qualite des Donnees ETL")
    parser.add_argument("--mode", choices=["db", "synthetic"], default="db",
                        help="Source: 'db' (PostgreSQL) ou 'synthetic'")
    parser.add_argument("--n", type=int, default=10_000,
                        help="Nb enregistrements synthetiques")
    args = parser.parse_args()

    # Load mappings
    naf_codes, formes_juridiques, effectifs_insee, categories_entreprise = load_mappings()
    print(f"  [MAPPINGS] NAF: {len(naf_codes)} codes | Formes: {len(formes_juridiques)} | "
          f"Effectifs: {len(effectifs_insee)} | Categories: {len(categories_entreprise)}")

    # Load data
    if args.mode == "db":
        df_ent, df_raw = load_from_database()
    else:
        df_ent, df_raw = generate_synthetic_data(n=args.n)

    if len(df_ent) == 0:
        print("\n  [ERREUR] Aucune donnee trouvee. Verifiez la connexion a la base.")
        sys.exit(1)

    # Run audit
    auditor = DataQualityAuditor(
        df_ent, df_raw,
        naf_codes, formes_juridiques, effectifs_insee, categories_entreprise
    )
    auditor.run_all()
    auditor.print_report()
    auditor.export_json(output_dir=os.path.join(str(Path(__file__).resolve().parent.parent), "reports"))


if __name__ == "__main__":
    main()
