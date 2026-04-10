import time
import random
from scrapers.dataGouv import DataGouvService
from extractors.dataGouv.datagouv_extractor import extract_data_from_datagouv

def enrich_boamp_data(boamp_records):
    """
    Parcourt la liste des entreprises brutes extraites de BOAMP (via get_global_information)
    et les enrichit en interrogeant l'API DataGouv.
    Recherche par :
    1. SIRET
    2. SIREN (déduit du SIRET)
    3. Nom + Ville
    """
    dg_service = DataGouvService()
    
    total = len(boamp_records)
    print(f"[ENRICH BOAMP] Démarrage de l'enrichissement (Total: {total} avis)...")
    
    for i, record in enumerate(boamp_records):
        siret = record.get("siret")
        nom = record.get("nom")
        ville = record.get("ville")
        
        api_results = []
        
        # 1. Recherche par SIRET (s'il est présent)
        if siret:
            data = dg_service.fetch_data(dg_service.base_url, params={"q": siret, "per_page": 1})
            if data and data.get("results"):
                api_results = data.get("results")
        
        # 2. Si pas de résultat par siret, chercher par siren (les 9 premiers caractères du SIRET)
        if not api_results and siret and len(siret) >= 9:
            siren = siret[:9]
            data = dg_service.fetch_data(dg_service.base_url, params={"q": siren, "per_page": 1})
            if data and data.get("results"):
                api_results = data.get("results")
                
        # 3. Fallback: Nom + Ville
        if not api_results and nom and ville:
            # L'API accepte le terme de recherche dans 'q'. Ex: "Mairie de Paris Paris"
            q_str = f"{nom} {ville}"
            data = dg_service.fetch_data(dg_service.base_url, params={"q": q_str, "per_page": 1})
            if data and data.get("results"):
                api_results = data.get("results")

        if api_results:
            # Parse using existing DataGouv extractor function
            parsed_dg_list = extract_data_from_datagouv(api_results)
            
            if parsed_dg_list:
                dg_data = parsed_dg_list[0]
                
                # SIREN
                if not record.get("siren"):
                    record["siren"] = dg_data.get("siren")
                
                # Mise à jour avec les informations DataGouv plus précises
                # On priorise DataGouv pour le secteur et forme juridique, 
                # afin d'utiliser la liste NAF unique dans le cleaner
                record["secteur_activite"] = dg_data.get("secteur_activite") or record.get("secteur_activite")
                record["forme_juridique"] = dg_data.get("forme_juridique") or record.get("forme_juridique")
                
                if not record.get("ville") and dg_data.get("ville"):
                    record["ville"] = dg_data.get("ville")
                if not record.get("code_postal") and dg_data.get("code_postal"):
                    record["code_postal"] = dg_data.get("code_postal")
                
                # Ajout des nouveaux champs spécifiques DataGouv
                record["taille_entrep"] = dg_data.get("taille_entrep")
                record["categorie_entreprise"] = dg_data.get("categorie_entreprise")
                record["nb_locaux"] = dg_data.get("nb_locaux")
                record["ca"] = dg_data.get("ca")
                record["dateCreation"] = dg_data.get("dateCreation")
                record["dateDerniereModification"] = dg_data.get("dateDerniereModification")
                record["dirigeants"] = dg_data.get("dirigeants")
                
                # Mettre à jour la source
                if "sources" in record:
                    record["sources"]["dirigeants"] = "dataGouv"
                    record["sources"]["ca"] = "dataGouv"
                    record["sources"]["taille_entrep"] = "dataGouv"
        
        # Délai imposé (1.5s à 2s) pour respecter le Rate Limit de l'API gouvernementale
        time.sleep(random.uniform(1.5, 2.0))
        
        if (i + 1) % 10 == 0:
            print(f"[ENRICH BOAMP] {i+1}/{total} traités...")

    print(f"[ENRICH BOAMP] Terminé.")
    return boamp_records
