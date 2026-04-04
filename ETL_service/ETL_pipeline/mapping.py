map_juridique = {
            "body-pl": "Organisme de droit public",
            "la": "Autorité locale ou régionale",
            "cga": "Autorité gouvernementale centrale", # C'est votre cas (Ministère/État)
            "eu": "Institution européenne",
            "org-sub": "Organisation subventionnée",
            "def-cont": "Défense"
        }
map_secteurs = {
        # --- Vos nouveaux codes trouvés ---
        "rcr": "Loisirs, culture et culte",
        "education": "Enseignement",
        "soc-pro": "Protection sociale",
        
        # --- Les autres codes fréquents ---
        "health": "Santé",
        "gen-pub": "Services généraux des administrations", # Souvent pour les Mairies
        "hc-am": "Logement et équipements collectifs",    # Housing & Community Amenities
        "pub-os": "Ordre et sécurité publics",            # Public Order & Safety
        "env": "Environnement",
        "def": "Défense",
        "econ-aff": "Affaires économiques et financières",
        
        # Codes complets parfois utilisés
        "general-public-services": "Services généraux des administrations",
        "public-order-and-safety": "Ordre et sécurité publics",
        "environment": "Environnement",
        "housing-and-community-amenities": "Logement et équipements collectifs",
        "recreation-culture-and-religion": "Loisirs, culture et culte"
    }    
effectifs_insee = {
        "NN": "Unité non employeuse (0 salarié)",
        "00": "0 salarié",
        "01": "1 à 2 salariés",
        "02": "3 à 5 salariés",
        "03": "6 à 9 salariés",
        "11": "10 à 19 salariés",
        "12": "20 à 49 salariés",
        "21": "50 à 99 salariés",
        "22": "100 à 199 salariés",
        "31": "200 à 249 salariés",
        "32": "250 à 499 salariés",
        "41": "500 à 999 salariés",
        "42": "1 000 à 1 999 salariés",
        "51": "2 000 à 4 999 salariés",
        "52": "5 000 à 9 999 salariés",
        "53": "10 000 salariés et plus"
    }
categories_entreprise={
    "MIC": "Microentreprise",
    "PME": "Petite et Moyenne Entreprise",
    "ETI": "Entreprise de Taille Intermédiaire",
    "GE": "Grande Entreprise",
}  
formes_juridiques = {
        "1000": "Entrepreneur individuel",
        "5498": "EURL (SARL à associé unique)",
        "5499": "SARL",
        "5599": "SA (Société Anonyme)",
        "5710": "SAS (Société par Actions Simplifiée)",
        "5720": "SASU (SAS à associé unique)",
        "6540": "SCI (Société Civile Immobilière)"
    }  