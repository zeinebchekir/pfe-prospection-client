import json
from datetime import datetime
from .extraction_methods import (
    extraire_infos_fiables,
    recuperer_details_acheteur,
    extract_fnsimple_data,
    extraire_donnees_mapa,
)

def get_global_information(resultats):
    """
    Nettoie les données, crée des objets (Entreprise et Lead) en mémoire
    et les prépare pour l'export Excel.
    """
    prospects_objets = []
    ext_siret = None
    ext_email = None
    ext_ville = None
    ext_cp = None
    ext_secteur = None
    ext_forme_juridique = None
    ext_date_limite = None
    ext_info_complementaire = None,
    ext_num_tel = None
    datemiseajour=None
    nature=None
    url_avis=None
    valeurMarche=None

    print(f"Traitement de {len(resultats)} résultats en objets...")

    for r in resultats:
        # ──────────────────────────────────────────────
        # 1. Champs communs extraits de l'API BOAMP
        # ──────────────────────────────────────────────
        id_avis = r.get("id") or r.get("idweb", "")
        client = r.get("nomacheteur", None)
        objet = r.get("objet", None)
        date_fin = r.get("datelimitereponse", None)
        perimetre = r.get("perimetre", None)
        raw_json_str = r.get("donnees", None)
        url_avis = r.get("url_avis", None)
        nature = r.get("nature", None)
        datemiseajour=r.get("dateparution",None)
        # Gestion propre du titulaire
        titulaire_raw = r.get("titulaire", None)
        if not titulaire_raw:
            nom_titulaire = None
        elif isinstance(titulaire_raw, list):
            nom_titulaire = str(titulaire_raw[0]) if titulaire_raw else None
        elif isinstance(titulaire_raw, dict):
            nom_titulaire = str(titulaire_raw)
        else:
            nom_titulaire = titulaire_raw

        # Conversion du JSON
        if isinstance(raw_json_str, str) and raw_json_str.strip():
            try:
                clean = json.loads(raw_json_str)
            except json.JSONDecodeError:
                clean = {}
        else:
            clean = raw_json_str or {}

        # ──────────────────────────────────────────────
        # 2. Variables temporaires pour le routage
        # ──────────────────────────────────────────────
        
        # --- Routage selon le périmètre ---
        if perimetre in ["DIRECTIVE-24", "DIRECTIVE-25", "AUTRE"]:
            data_fiable = extraire_infos_fiables(clean)
            details = recuperer_details_acheteur(data_fiable.get("root"), data_fiable.get("contract_id"))
            
            ext_siret = details.get("siret",None)
            ext_email = details.get("email",None)
            ext_num_tel = details.get("tel",None)
            ext_ville = details.get("ville",None)
            ext_cp = details.get("cp",None)
            ext_secteur = data_fiable.get("secteur",None)
            ext_forme_juridique = data_fiable.get("forme_juridique", None)
            valeurMarche = data_fiable.get("valeurMarche",None)

        elif perimetre == "FNSimple":
            data_fn = extract_fnsimple_data(clean)
            ext_siret = data_fn.get("siret", None)
            ext_email = data_fn.get("Email", None)
            ext_num_tel = data_fn.get("Telephone", None)
            ext_ville = data_fn.get("Ville", None)
            ext_cp = data_fn.get("code_postal", None)
            ext_secteur = data_fn.get("secteur", None)
            ext_forme_juridique = data_fn.get("forme_juridique", None)
            ext_date_limite = data_fn.get("DateLimite", date_fin)
            ext_info_complementaire = data_fn.get("info_complementaire", None)
            valeurMarche = data_fn.get("valeurMarche",None)
        elif perimetre == "MAPA":
            data_mapa = extraire_donnees_mapa(clean)
            ext_email = data_mapa.get("Email",None)
            ext_num_tel = data_mapa.get("Telephone",None)
            ext_ville = data_mapa.get("Ville",None)
            ext_date_limite = data_mapa.get("DateLimite", date_fin)        

        # ──────────────────────────────────────────────
        # 3. CRÉATION DES OBJETS EN MÉMOIRE (Pas de .save())
        # ──────────────────────────────────────────────
        
        entreprise_obj = {
            "idAvis":id_avis,
            "siret":ext_siret, 
            "nom":client,
            "secteur_activite":ext_secteur,
            "forme_juridique":ext_forme_juridique,
            "ville":ext_ville,
            "code_postal":ext_cp,
            "adresse_email":ext_email,
            "pays":"France",
            "sourceEntreprise":"BOAMP",
            "dateMAJ":datemiseajour,
            "sources":{
                "nom":"BOAMP" if client else None,
                "siret":"BOAMP" if ext_siret else None,
                "secteur":"BOAMP" if ext_secteur else None,
                "forme_juridique":"BOAMP" if ext_forme_juridique else None,
                "ville":"BOAMP" if ext_ville else None,
                "code_postal":"BOAMP" if ext_cp else None,
                "adresse_email":"BOAMP" if ext_email else None,
                "pays":"BOAMP",
                "num_tel":"BOAMP" if ext_num_tel else None,
                "besoin":"BOAMP",
                "date_limite":"BOAMP",
                "titulaire":"BOAMP" ,
                "nature":"BOAMP",
                "lienOffre":"BOAMP" ,
                "info_complementaire":"BOAMP" ,
                "dateMAJ":"BOAMP" if datemiseajour else None,
            },
            
                "num_tel":ext_num_tel,
                "besoin":objet,
                "date_limite":ext_date_limite,
                "titulaire":nom_titulaire,
                "nature":nature,
                "lienOffre":url_avis,
                "info_complementaire":ext_info_complementaire,
                "valeurMarche":valeurMarche,
            }
        # 4. ON STOCKE TOUTE LA LIGNE DANS LA LISTE
      
        prospects_objets.append(entreprise_obj)

    # 4. Envoi de la liste d'OBJETS vers Pandas
    return prospects_objets