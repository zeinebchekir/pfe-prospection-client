import time
import random
from scrapers.dataGouv import DataGouvService
from extractors.dataGouv.datagouv_extractor import extract_data_from_datagouv


def enrich_boamp_data(boamp_records, db=None):
    """
    Enrichit chaque enregistrement BOAMP avec les données de l'API DataGouv.

    Règle anti-doublons :
    - L'unicité est garantie en aval par le UPSERT (ON CONFLICT DO UPDATE)
      sur la colonne `identifiant` (= idAvis BOAMP) dans crud.insert_clean_leads.
    - Cette fonction n'a donc PAS besoin de vérifier si l'entreprise existe déjà :
      elle enrichit SYSTÉMATIQUEMENT tous les enregistrements, qu'ils soient
      nouveaux ou déjà présents en base.

    Args:
        boamp_records : liste de dicts retournés par get_global_information()
        db            : session SQLAlchemy (ignorée ici, conservée pour compatibilité)
    """
    dg_service = DataGouvService()

    total = len(boamp_records)
    print(f"[ENRICH BOAMP] Démarrage enrichissement DataGouv ({total} avis)...")

    for i, record in enumerate(boamp_records):
        siret = record.get("siret") or ""
        siren = record.get("siren") or (siret[:9] if len(siret) >= 9 else None)
        nom   = record.get("nom")
        ville = record.get("ville")

        api_results = []

        # 1. Recherche par SIRET
        if siret:
            data = dg_service.fetch_data(dg_service.base_url, params={"q": siret, "per_page": 1})
            if data and data.get("results"):
                api_results = data.get("results")

        # 2. Recherche par SIREN (9 premiers caractères du SIRET)
        if not api_results and siren:
            data = dg_service.fetch_data(dg_service.base_url, params={"q": siren, "per_page": 1})
            if data and data.get("results"):
                api_results = data.get("results")

        # 3. Fallback : nom + ville
        if not api_results and nom and ville:
            q_str = f"{nom} {ville}"
            data = dg_service.fetch_data(dg_service.base_url, params={"q": q_str, "per_page": 1})
            if data and data.get("results"):
                api_results = data.get("results")

        if api_results:
            parsed_dg_list = extract_data_from_datagouv(api_results)
            if parsed_dg_list:
                dg_data = parsed_dg_list[0]

                # Siren manquant sur le record BOAMP → le compléter
                if not record.get("siren"):
                    record["siren"] = dg_data.get("siren")

                # DataGouv est prioritaire pour le secteur et la forme juridique
                # (utilise le label NAF normalisé plutôt que le code brut BOAMP)
                record["secteur_activite"] = dg_data.get("secteur_activite") or record.get("secteur_activite")
                record["forme_juridique"]  = dg_data.get("forme_juridique")  or record.get("forme_juridique")

                # Adresse : complète si manquante sur le record BOAMP
                if not record.get("ville") and dg_data.get("ville"):
                    record["ville"] = dg_data.get("ville")
                if not record.get("code_postal") and dg_data.get("code_postal"):
                    record["code_postal"] = dg_data.get("code_postal")

                # Champs exclusivement DataGouv — toujours mis à jour (fraîcheur)
                record["taille_entrep"]            = dg_data.get("taille_entrep")
                record["categorie_entreprise"]     = dg_data.get("categorie_entreprise")
                record["nb_locaux"]                = dg_data.get("nb_locaux")
                record["ca"]                       = dg_data.get("ca")
                record["dateCreation"]             = dg_data.get("dateCreation")
                record["dateDerniereModification"] = dg_data.get("dateDerniereModification")
                record["dirigeants"]               = dg_data.get("dirigeants")

                if "sources" in record:
                    record["sources"]["dirigeants"]    = "dataGouv"
                    record["sources"]["ca"]            = "dataGouv"
                    record["sources"]["taille_entrep"] = "dataGouv"

        # Délai imposé pour le rate-limit de l'API gouvernementale
        time.sleep(random.uniform(1.5, 2.0))

        if (i + 1) % 10 == 0:
            print(f"[ENRICH BOAMP] {i+1}/{total} traités...")

    print(f"[ENRICH BOAMP] Terminé — {total} enregistrements enrichis.")
    return boamp_records
