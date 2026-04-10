import time
import random
from scrapers.dataGouv import DataGouvService
from extractors.dataGouv.datagouv_extractor import extract_data_from_datagouv


def _lookup_existing_sirens(db, sirens: set) -> set:
    """
    Query the DB for all SIRENs already present in the entreprise table.
    Returns a set of known SIRENs so we can skip the DataGouv API for them.
    """
    if not sirens or db is None:
        return set()
    try:
        from db.models import Entreprise
        rows = db.query(Entreprise.siren).filter(Entreprise.siren.in_(sirens)).all()
        return {row.siren for row in rows if row.siren}
    except Exception as e:
        print(f"[ENRICH BOAMP] Warning: could not query existing SIRENs — {e}")
        return set()


def enrich_boamp_data(boamp_records, db=None):
    """
    Parcourt la liste des entreprises extraites de BOAMP et les enrichit avec DataGouv.

    Logique de comparaison DB :
    - Si le SIREN de l'enregistrement est déjà présent en base de données,
      on NE fait PAS d'appel API DataGouv (les données structurées sont déjà connues).
    - Si l'entreprise est nouvelle (SIREN inconnu en DB), on interroge DataGouv pour
      récupérer dirigeants, CA, forme juridique, taille, etc.

    Args:
        boamp_records : liste de dicts retournés par get_global_information()
        db            : session SQLAlchemy optionnelle (fournie par la task Airflow)
    """
    dg_service = DataGouvService()

    total = len(boamp_records)
    print(f"[ENRICH BOAMP] Démarrage de l'enrichissement (Total: {total} avis)...")

    # ── Pre-fetch known SIRENs from DB to avoid redundant API calls ──────────
    candidate_sirens = set()
    for record in boamp_records:
        siret = record.get("siret") or ""
        siren = record.get("siren") or (siret[:9] if len(siret) >= 9 else None)
        if siren:
            candidate_sirens.add(siren)

    known_sirens = _lookup_existing_sirens(db, candidate_sirens)
    if known_sirens:
        print(
            f"[ENRICH BOAMP] {len(known_sirens)} SIRENs déjà en base — "
            f"appel DataGouv ignoré pour ceux-ci."
        )
    # ─────────────────────────────────────────────────────────────────────────

    new_count      = 0
    existing_count = 0

    for i, record in enumerate(boamp_records):
        siret = record.get("siret") or ""
        siren = record.get("siren") or (siret[:9] if len(siret) >= 9 else None)

        # ── Entreprise already in DB → skip DataGouv API ─────────────────────
        if siren and siren in known_sirens:
            existing_count += 1
            record["_db_status"] = "existing"
            # Ensure siren field is populated on the record
            if not record.get("siren") and siren:
                record["siren"] = siren
            continue
        # ─────────────────────────────────────────────────────────────────────

        # ── New company → call DataGouv API ──────────────────────────────────
        new_count += 1
        record["_db_status"] = "new"
        nom   = record.get("nom")
        ville = record.get("ville")

        api_results = []

        # 1. Recherche par SIRET (s'il est présent)
        if siret:
            data = dg_service.fetch_data(dg_service.base_url, params={"q": siret, "per_page": 1})
            if data and data.get("results"):
                api_results = data.get("results")

        # 2. Si pas de résultat par SIRET, chercher par SIREN
        if not api_results and siren:
            data = dg_service.fetch_data(dg_service.base_url, params={"q": siren, "per_page": 1})
            if data and data.get("results"):
                api_results = data.get("results")

        # 3. Fallback: Nom + Ville
        if not api_results and nom and ville:
            q_str = f"{nom} {ville}"
            data = dg_service.fetch_data(dg_service.base_url, params={"q": q_str, "per_page": 1})
            if data and data.get("results"):
                api_results = data.get("results")

        if api_results:
            parsed_dg_list = extract_data_from_datagouv(api_results)
            if parsed_dg_list:
                dg_data = parsed_dg_list[0]

                if not record.get("siren"):
                    record["siren"] = dg_data.get("siren")

                # Prioritise DataGouv for structural fields (NAF label, legal form)
                record["secteur_activite"] = dg_data.get("secteur_activite") or record.get("secteur_activite")
                record["forme_juridique"]  = dg_data.get("forme_juridique")  or record.get("forme_juridique")

                if not record.get("ville") and dg_data.get("ville"):
                    record["ville"] = dg_data.get("ville")
                if not record.get("code_postal") and dg_data.get("code_postal"):
                    record["code_postal"] = dg_data.get("code_postal")

                # DataGouv-only fields
                record["taille_entrep"]              = dg_data.get("taille_entrep")
                record["categorie_entreprise"]       = dg_data.get("categorie_entreprise")
                record["nb_locaux"]                  = dg_data.get("nb_locaux")
                record["ca"]                         = dg_data.get("ca")
                record["dateCreation"]               = dg_data.get("dateCreation")
                record["dateDerniereModification"]   = dg_data.get("dateDerniereModification")
                record["dirigeants"]                 = dg_data.get("dirigeants")

                if "sources" in record:
                    record["sources"]["dirigeants"]   = "dataGouv"
                    record["sources"]["ca"]           = "dataGouv"
                    record["sources"]["taille_entrep"] = "dataGouv"

        # Rate-limit delay
        time.sleep(random.uniform(1.5, 2.0))

        if (i + 1) % 10 == 0:
            print(f"[ENRICH BOAMP] {i+1}/{total} traités...")

    print(
        f"[ENRICH BOAMP] Terminé. "
        f"Nouvelles entreprises enrichies via DataGouv : {new_count} | "
        f"Existantes (API ignorée) : {existing_count}"
    )
    return boamp_records
