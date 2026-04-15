import pandas as pd
from datetime import datetime


def _entreprise_to_dict(e) -> dict:
    """Convertit une instance Entreprise en dict plat pour Pandas."""
    if e is None:
        return {}
    return {
        "siret":                  e.siret,
        "siren":                  e.siren,
        "nom":                    e.nom,
        "secteur_activite":       e.secteur_activite,
        "forme_juridique":        e.forme_juridique,
        "taille_entrep":          e.taille_entrep,
        "categorie_entreprise":   e.categorie_entreprise,
        "nb_locaux":              e.nb_locaux,
        "ca":                     e.ca,
        "taux_croissance":        e.taux_croissance,
        "pays":                   e.pays,
        "ville":                  e.ville,
        "code_postal":            e.code_postal,
        "adresse_email":          e.adresse_email,
        "siteweb":                e.siteweb,
        "linkedin":               e.linkedin,
        "source":                 e.sourceEntreprise,
        "date_creation":          e.dateCreation,
        "date_modification":      e.dateDerniereModification,
         "besoin":                 e.besoin,
        "date_limite":            e.date_limite,
        "titulaire":              e.titulaire,
        "nature":                 e.nature,
        "lien_offre":             e.lienOffre,
        "info_complementaire":    e.info_complementaire,
        "dateMAJ":                e.dateMAJ
    }


def export_to_excel(resultats: list[dict], nom_fichier: str = None) -> str:
    """
    Reçoit une liste unifiée de {"entreprise": ..., "lead": ...}
    provenant de n'importe quelle source (BOAMP, DataGouv, etc.)
    et génère un fichier Excel avec deux onglets.

    Retourne le chemin du fichier créé.
    """
    if not nom_fichier:
        horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
        nom_fichier = f"export_crm_{horodatage}.xlsx"


    # 2. Créer les DataFrames
    df_entreprises = pd.DataFrame(resultats)
    # 3. Écrire dans Excel avec deux onglets
    with pd.ExcelWriter(nom_fichier, engine="openpyxl") as writer:
        df_entreprises.to_excel(writer, sheet_name="Entreprises", index=False)

    print(f"✅ Export Excel généré : {nom_fichier}")
    return nom_fichier