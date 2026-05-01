from extractors.dataGouv.linkedin_enricher import get_linkedin_url

def extract_data_from_datagouv(results):
    clean_data = []
    """
    Prend le JSON brut de l'API et recrache un dictionnaire propre
    prêt à être injecté dans votre base de données CRM.
    """
    for r in results:
    # --- 1. DATES (Création et Modification) ---
        date_creation = r.get("date_creation",None)
        date_maj = r.get("date_mise_a_jour") or r.get("date_mise_a_jour_insee")

        # --- 2. INFORMATIONS JURIDIQUES ---
        siren = r.get("siren",None)
        nom = r.get("nom_complet",None)
        etat = r.get("etat_administratif",None)
        code_juridique = r.get("nature_juridique",None)

        # --- 3. ADRESSE ET CONTACT (Ciblé sur le siège social) ---
        siege = r.get("siege", {})
        adresse = siege.get("adresse",None)
        code_postal = siege.get("code_postal",None)
        ville = siege.get("libelle_commune",None)
        # SIRET du siège social — disponible dans l'objet `siege` de l'API DataGouv
        siret_siege = siege.get("siret", None)

        # --- 4. SECTEUR D'ACTIVITÉ ET FORME JURIDIQUE ---
        activite = r.get("activite_principale",None)

        # --- 6. EFFECTIFS / TAILLE (Nouveauté !) ---
        taille_globale = r.get("tranche_effectif_salarie",None)
        categorie_entreprise = r.get("categorie_entreprise",None)

        # --- 5. FINANCES (Astuce pour gérer les années dynamiques) ---
        ca = None
        resultat_net = None
        finances = r.get("finances", {})

        if finances:
            derniere_annee = sorted(finances.keys())[-1]
            ca = finances[derniere_annee].get("ca")
            
        # --- 7. NOMBRE DE LOCAUX (Établissements) ---
        nb_locaux_ouverts = r.get("nombre_etablissements_ouverts",None)
        
        # --- SÉCURISATION DU CODE POSTAL ---
        # Ton modèle Django attend un IntegerField, on s'assure que c'est bien un nombre
        try:
            cp_propre = int(code_postal) if code_postal else None
        except ValueError:
            cp_propre = None
        #extract dirigeants 
        liste_brute_dirigeants = r.get("dirigeants") or []
    
    # Filtrer les personnes physiques
        dirigeants_filtres = [
            d for d in liste_brute_dirigeants 
            if d.get("type_dirigeant") == "personne physique"
        ]
        
        # Enrichissement LinkedIn
        for d in dirigeants_filtres:
            nom_dir = d.get("nom")
            prenom_dir = d.get("prenoms")
            link = get_linkedin_url(nom_dir, prenom_dir, nom)
            d["linkedin_url"] = link
        # === CRÉATION DE L'INSTANCE DJANGO ===
        nouvelle_entreprise ={ 
            "siren":siren,
            "siret":siret_siege,        # SIRET du siège extrait de l'objet siege
            "nom":nom,
            "secteur_activite":activite,
            "taille_entrep":taille_globale,
            "categorie_entreprise":categorie_entreprise,
            "nb_locaux":nb_locaux_ouverts,
            "ca":ca,
            "forme_juridique":code_juridique,
            "pays":"France",
            "ville":ville,
            "code_postal":cp_propre,
            "dateCreation":date_creation,
            "dateDerniereModification":date_maj,
            "data_from_boamp":None,
            "sourceEntreprise":"dataGouv",
            "dirigeants":dirigeants_filtres,
            "sources":{
                "siren":"dataGouv" if siren else None,
                "nom":"dataGouv" if nom else None,
                "secteur_activite":"dataGouv" if activite else None,
                "forme_juridique":"dataGouv" if code_juridique else None,
                "ville":"dataGouv" if ville else None,
                "code_postal":"dataGouv" if code_postal else None,
                "pays":"dataGouv",
                "taille_entrep":"dataGouv" if taille_globale else None,
                "categorie_entreprise":"dataGouv" if categorie_entreprise else None,
                "nb_locaux":"dataGouv" if nb_locaux_ouverts else None,
                "ca":"dataGouv" if ca else None,
                "dateCreation":"dataGouv" if date_creation else None,
                "dateDerniereModification":"dataGouv" if date_maj else None,
                "linkedin_url": None,
                "website_url":None,
                "dirigeants":"dataGouv" if dirigeants_filtres else None,
                "description":None
                
            }

            }
           
        clean_data.append(nouvelle_entreprise)
    # Si tu veux garder ton dictionnaire pour d'autres usages, tu peux toujours le créer ici
    # Tu peux renvoyer l'instance Django, le dico, ou même les deux !
    return clean_data

