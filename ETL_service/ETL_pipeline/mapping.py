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
    # Personnes physiques
    "1000": "Entrepreneur individuel",
    "1100": "Artisan-commerçant",
    "1200": "Commerçant",
    "1300": "Artisan",
    "1400": "Officier public ou ministériel",
    "1500": "Profession libérale",
    "1600": "Exploitant agricole",
    "1700": "Agent commercial",
    "1800": "Associé-gérant de société",
    "1900": "Autre personne physique",

    # Sociétés commerciales - SARL
    "5410": "SARL nationale",
    "5415": "SARL à participation ouvrière",
    "5420": "SARL coopérative de production (SCOP)",
    "5425": "SARL coopérative de consommation",
    "5426": "SARL coopérative d'intérêt collectif",
    "5430": "SARL de presse",
    "5440": "SARL d'attribution",
    "5450": "SARL coopérative construction",
    "5451": "SARL coopérative construction attribution",
    "5452": "SARL coopérative construction location",
    "5453": "SARL coopérative HLM",
    "5454": "SARL immobilière para-hôtelière",
    "5455": "SARL coopérative artisanale",
    "5458": "SARL coopérative de production (SCOP)",
    "5460": "SARL à objet sportif",
    "5485": "SARL unipersonnelle agricole (EARL)",
    "5498": "EURL (SARL à associé unique)",
    "5499": "SARL",

    # SA à conseil d'administration
    "5505": "SA à participation ouvrière à CA",
    "5510": "SA nationale à CA",
    "5515": "SA d'économie mixte à CA",
    "5520": "SICAV à CA",
    "5522": "SA immobilière d'investissement",
    "5525": "SA d'aménagement foncier et d'équipement rural (SAFER) à CA",
    "5530": "SA de presse à CA",
    "5531": "SA de presse à directoire",
    "5532": "SA à objet sportif à CA",
    "5542": "SA coopérative de consommation à CA",
    "5543": "SA coopérative artisanale à CA",
    "5544": "SA coopérative d'intérêt maritime à CA",
    "5545": "SA coopérative de transport à CA",
    "5546": "SA coopérative de production (SCOP) à CA",  # anciennement "ouvrière"
    "5547": "SA coopérative de construction à CA",
    "5548": "SA de crédit agricole à CA",
    "5551": "SA coopérative agricole à CA",
    "5552": "SA d'intérêt collectif agricole (SICA) à CA",
    "5553": "SA d'HLM à CA",
    "5554": "SA coopérative d'HLM à CA",
    "5555": "SA d'attribution à CA",
    "5558": "SA coopérative de production (SCOP) à CA",
    "5560": "SA à CA",
    "5565": "SA de gestion immobilière à CA",
    "5599": "SA (Société Anonyme)",

    # SA à directoire
    "5605": "SA à participation ouvrière à directoire",
    "5610": "SA nationale à directoire",
    "5615": "SA d'économie mixte à directoire",
    "5620": "SICAV à directoire",
    "5622": "SA immobilière d'investissement à directoire",
    "5625": "SA d'aménagement foncier (SAFER) à directoire",
    "5630": "SA de presse à directoire",
    "5632": "SA à objet sportif à directoire",
    "5642": "SA coopérative de consommation à directoire",
    "5643": "SA coopérative artisanale à directoire",
    "5645": "SA coopérative de transport à directoire",
    "5646": "SA coopérative de production (SCOP) à directoire",
    "5647": "SA coopérative de construction à directoire",
    "5648": "SA de crédit agricole à directoire",
    "5651": "SA coopérative agricole à directoire",
    "5652": "SICA à directoire",
    "5653": "SA d'HLM à directoire",
    "5654": "SA coopérative d'HLM à directoire",
    "5655": "SA d'attribution à directoire",
    "5658": "SA coopérative de production (SCOP) à directoire",
    "5660": "SA à directoire",
    "5665": "SA de gestion immobilière à directoire",

    # SAS / SASU
    "5699": "SAS (indéterminé)",
    "5710": "SAS (Société par Actions Simplifiée)",
    "5720": "SASU (SAS à associé unique)",

    # Sociétés civiles
    "6540": "SCI (Société Civile Immobilière)",
    "6316": "SCI de construction-vente",
    "6317": "SCI d'attribution",
    "6318": "SCPI (Société Civile de Placement Immobilier)",
    "6319": "Autre SCI",

    # GIE / autres
    "6220": "GIE (Groupement d'Intérêt Économique)",
    "6230": "GEIE (Groupement Européen d'Intérêt Économique)",

    # Associations / organismes
    "9220": "Association déclarée (loi 1901)",
    "9221": "Association déclarée - entreprises d'insertion",
    "9222": "Association intermédiaire",
    "9223": "Groupement d'employeurs",
    "9224": "Association d'avocats à responsabilité professionnelle individuelle",
    "9230": "Association déclarée, reconnue d'utilité publique",
    "9240": "Congrégation",
    "9260": "Association de droit local (Alsace-Moselle)",
    "9300": "Fondation",

    # Établissements publics
    "7120": "État et collectivités locales",
    "7130": "Établissement public administratif",
    "7210": "Commune et groupement de communes",
    "7220": "Département",
    "7225": "Territoire d'outre-mer",
    "7229": "Autre collectivité territoriale",
    "7230": "Région",
    "7310": "Établissement public local d'enseignement",
    "7340": "Centre hospitalier",
    "7364": "Établissement d'hébergement pour personnes âgées (EHPA)",
    "7381": "Office public HLM",
    "7382": "Office public d'aménagement et construction (OPAC)",
    "7389": "Autre établissement public",

    # Mutuelles / syndicats
    "8110": "Régime général de la Sécurité Sociale",
    "8120": "Mutualité sociale agricole (MSA)",
    "8130": "Caisse de retraite et de prévoyance",
    "8140": "Caisse de retraite interprofessionnelle",
    "8160": "Caisse primaire d'assurance maladie (CPAM)",
    "8190": "Autre organisme social à adhésion obligatoire",
    "8210": "Mutuelle",
    "8250": "Assurance mutuelle agricole",
    "8290": "Autre organisme mutualiste",
    "8310": "Comité central d'entreprise",
    "8311": "Comité d'établissement",
    "8410": "Syndicat de salariés",
    "8420": "Syndicat patronal",
    "8450": "Ordre professionnel ou assimilé",
    "8490": "Autre organisme professionnel",

    # Syndicats de copropriété
    "9110": "Syndicat de copropriété",
    "9150": "Association syndicale libre",
    "9210": "Association non déclarée",
    "9900": "Autre personne morale de droit privé",
}