import requests
import json
import pandas as pd 



def extraire_donnees_mapa(json_data):
    """
    Extrait les informations clés d'un dictionnaire JSON de marché public (MAPA).
    Retourne un dictionnaire plat, idéal pour l'export Excel avec Pandas.
    """
    # 1. On accède aux blocs principaux en toute sécurité
    mapa = json_data.get("MAPA", {})
    organisme = mapa.get("organisme", {})
    initial = mapa.get("initial", {})
    
    # 2. Extraction des sous-blocs
    contact = organisme.get("correspondantPRM", {})
    coord = organisme.get("coord", {})
    adresse = organisme.get("adr", {})
    description = initial.get("description", {})
    delais = initial.get("delais", {})
    
    # 3. Construction de l'adresse et du contact proprement
    nom_contact = f"{contact.get('civilite', '')} {contact.get('pren', '')} {contact.get('nom', '')}".strip()
    
    voie = adresse.get("voie", {})

    # 4. On prépare le dictionnaire final avec les données extraites
    donnees_extraites = {
        # Infos Organisme
        "Client": organisme.get("acheteurPublic", ""),
        "nom_contact": nom_contact,
        "poste": contact.get("fonc", ""),
        "Telephone": coord.get("tel", ""),
        "Email": coord.get("mel", ""),
        "Ville": adresse.get("ville", "").strip(),
        "code_postal": adresse.get("cp", "").strip(),
        "urlProfilAcheteur": organisme.get("urlProfilAcheteur", ""),
        "DateLimite": delais.get("receptionOffres", ""),
        # Délais
    }
    
    return donnees_extraites



def extract_fnsimple_data(json_data):
    fn = json_data.get("FNSimple", {})
    org = fn.get("organisme", {})
    
    # 1. Identification de base
    record = {
        "siret": org.get("codeIdentificationNational"),
        "Ville": org.get("ville"),
        "code_postal": org.get("cp"),
        "forme_juridique": "Non spécifié",
        "secteur": "Non spécifié",
        "nom_contact": None,
        "Email": None,
        "Telephone": None,
        "urlProfilAcheteur":"",
        "info_complementaire":""
    }

    # 2. Exploration du bloc 'initial' ou 'attribution'
    # On priorise 'initial' car c'est là qu'on trouve les contacts
    details = fn.get("initial") or fn.get("attribution", {})
    
    if details:
        # Extraction des contacts (bloc communication)
        comm = details.get("communication", {})
        record["urlProfilAcheteur"]=comm.get("urlProfilAch")
        record["nom_contact"] = comm.get("nomContact")
        record["Email"] = comm.get("adresseMailContact") or comm.get("nomContact") if "@" in str(comm.get("nomContact")) else None
        record["Telephone"] = comm.get("telContact")
        
        # Extraction de la forme juridique (bloc procedure)
        proc = details.get("procedure", {})

        if proc.get("categorieAcheteur"):
            record["forme_juridique"] = proc.get("categorieAcheteur")
        if proc.get("dateReceptionOffres"):
            record["DateLimite"] = proc.get("dateReceptionOffres")    
        infos_node = details.get("informComplementaire", {})
        record["info_complementaire"] = infos_node.get("autresInformComplementaire", "").strip()
        
        nature_marche = details.get("natureMarche") or {}
        valeur_estimee = nature_marche.get("valeurEstimee") or {}

        valeur = valeur_estimee.get("valeur", 0)

        if not valeur:
            fourchette = valeur_estimee.get("fourchette") or {}
            valeur = fourchette.get("valeurHaute") or fourchette.get("valeurBasse")

        record["valeurMarche"] = valeur
    return record


def extraire_infos_fiables(json_data):
    lead = {}
    root = None
    try: 
        eforms = json_data.get("EFORMS", {})
       
        # On cherche d'abord dans ContractNotice, sinon dans ContractAwardNotice
        if "ContractNotice" in eforms:
           
            root = eforms["ContractNotice"]
        elif "ContractAwardNotice" in eforms:
            
            root = eforms["ContractAwardNotice"]
        else:
            # Si aucun des deux, on passe au suivant
           
            return {"root": None, "contract_id": None, "forme_juridique": "Non spécifiée", "secteur": "Non spécifié"}
        
        # --- NAVIGATION SÉCURISÉE VERS LES EXTENSIONS ---
        # Utilisation de listes vides par défaut pour éviter les crashs
        ext_content = root.get("ext:UBLExtensions", {}).get("ext:UBLExtension", {}).get("ext:ExtensionContent", {}).get("efext:EformsExtension", {})
        valeurMarche=ext_content.get("efac:NoticeResult", {}).get("efbc:OverallMaximumFrameworkContractsAmount", {}).get("#text", "")
        organisations_wrapper = ext_content.get("efac:Organizations", {}).get("efac:Organization", [])
        # Si c'est un dictionnaire unique au lieu d'une liste, on le met dans une liste
        if isinstance(organisations_wrapper, dict):
            organisations = [organisations_wrapper]
        else:
            organisations = organisations_wrapper
        # --- RECUPERATION DE L'ID DU CONTRAT (Le point de crash) ---
        # On descend prudemment
        # --- 8. RECUPERATION DE L'ACHETEUR (Gestion List vs Dict) ---
        raw_contract_party = root.get("cac:ContractingParty", {})
        
        # On force en liste pour traiter tout le monde de la même façon
        if isinstance(raw_contract_party, list):
            liste_contract_parties = raw_contract_party
        elif isinstance(raw_contract_party, dict):
            liste_contract_parties = [raw_contract_party]
        else:
            liste_contract_parties = []

        # On prend par défaut le premier acheteur de la liste pour extraire les IDs
        # (Dans 99% des cas, c'est l'acheteur principal)
        contract_party = liste_contract_parties[0] if liste_contract_parties else {}


        # --- EXTRACTION DE LA FORME JURIDIQUE ---
        raw_types = contract_party.get("cac:ContractingPartyType")
        code_trouve = "Non spécifié"
        
        # On sécurise aussi ici car ContractingPartyType peut être une liste
        liste_types = []
        if isinstance(raw_types, list):
            liste_types = raw_types
        elif isinstance(raw_types, dict):
            liste_types = [raw_types]

        for item in liste_types:
            type_code_obj = item.get("cbc:PartyTypeCode", {})
            if isinstance(type_code_obj, dict):
                if type_code_obj.get("@listName") == "buyer-legal-type":
                    code_trouve = type_code_obj.get("#text", "Non spécifié")
                    break

        
        # --- EXTRACTION DE L'ID DE L'ORGANISATION ---
        # Note : On cherche dans cac:Party / cac:PartyIdentification / cbc:ID
        party_id_obj = contract_party.get("cac:Party", {}).get("cac:PartyIdentification", {}).get("cbc:ID", {})
        
        if isinstance(party_id_obj, dict):
            contract_id = party_id_obj.get("#text", "NON_TROUVE")
        elif isinstance(party_id_obj, str):
            contract_id = party_id_obj
        else:
            contract_id = "NON_TROUVE"


        # --- EXTRACTION DU SECTEUR D'ACTIVITÉ ---
        secteur_obj = contract_party.get("cac:ContractingActivity", {}).get("cbc:ActivityTypeCode", {})
        if isinstance(secteur_obj, dict):
            secteur = secteur_obj.get("#text", "Non spécifié")
        else:
            secteur = secteur_obj if secteur_obj else "Non spécifié"

        lead = {
            "secteur": secteur,
            "contract_id": contract_id,
            "forme_juridique": code_trouve,
            "valeurMarche": valeurMarche,
            "root": root
        }
    except json.JSONDecodeError:
        print("Erreur : Impossible de décoder le JSON 'donnees'")
    except Exception as e:
        print(f"Erreur générique sur ce dossier : {e}")
        
    return lead

def recuperer_details_acheteur(root, id_acheteur_recherche):
    """
    Parcourt les organisations pour trouver l'acheteur et 
    récupère : Email, Tel, Nom, VILLE et CODE POSTAL.
    """
    # Valeurs par défaut
    infos = {
        "email": "Non trouvé",
        "tel": "Non trouvé",
        "contact": "Non trouvé",
        "ville": "Non trouvée",     # <--- Nouveau champ
        "cp": "" ,
        "siret": "",
                      # <--- Nouveau champ
    }

    if root is None:
        return infos

    try:
        # 1. Accès à la liste (comme avant)
        extensions = root.get("ext:UBLExtensions", {}).get("ext:UBLExtension", {})
        content = extensions.get("ext:ExtensionContent", {}).get("efext:EformsExtension", {})
        orgs_wrapper = content.get("efac:Organizations", {}).get("efac:Organization", [])
        # Sécurité pour liste vs dict unique
        liste_orgs = [orgs_wrapper] if isinstance(orgs_wrapper, dict) else orgs_wrapper
        # 2. La boucle
        for org in liste_orgs:
            company = org.get("efac:Company", {})
            # Vérif ID
           
            # --- DÉBUT BLOC DE SÉCURITÉ ---
        
        # 1. Récupérer 'cac:PartyIdentification' sans planter
            raw_party = company.get("cac:PartyIdentification")
            # Si c'est une liste (plusieurs identifiants), on prend le premier élément
            
            if isinstance(raw_party, dict):
                # C'est un dictionnaire, tout va bien
                party_ident = raw_party
            else:
                # C'est vide ou None
                party_ident = {}

            # 2. Maintenant on peut faire .get() sans peur
            id_obj = party_ident.get("cbc:ID")
            # 3. Extraction de la valeur (String ou Dict {"#text": ...})
            id_courant = "NON_TROUVE"
            if isinstance(id_obj, dict):
                id_courant = id_obj.get("#text", "NON_TROUVE")
            elif isinstance(id_obj, str):
                id_courant = id_obj
            
            # --- FIN BLOC DE SÉCURITÉ ---

            print(id_courant)
            if id_courant == id_acheteur_recherche:
                # --- A. CONTACTS (Ce qu'on avait déjà) ---
                contact = company.get("cac:Contact", {})
                infos["email"] = contact.get("cbc:ElectronicMail", "Non renseigné")
                infos["tel"] = contact.get("cbc:Telephone", "Non renseigné")
                infos["contact"] = contact.get("cbc:Name", "Service Achat")
                # --- B. ADRESSE (LA VILLE) ---
                adresse = company.get("cac:PostalAddress", {})
                
                # Extraction Ville
                ville_raw = adresse.get("cbc:CityName", "Inconnue")
                infos["ville"] = ville_raw.get("#text") if isinstance(ville_raw, dict) else ville_raw
                # Extraction Code Postal (Bonus)
                cp_raw = adresse.get("cbc:PostalZone", "")
                infos["cp"] = cp_raw.get("#text") if isinstance(cp_raw, dict) else cp_raw
                # Extraction SIRET
                siret_raw = company.get("cac:PartyLegalEntity", {}).get("cbc:CompanyID", "")
                infos["siret"] = siret_raw.get("#text") if isinstance(siret_raw, dict) else siret_raw
                break # On a trouvé, on sort

    except Exception as e:
        print(f"Erreur extraction détails : {e}")

    return infos



