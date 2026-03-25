from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from db.database import Base


class Entreprise(Base):
    __tablename__ = "entreprises"

    # --- Identifiants ---
    siret = Column(String, primary_key=True, index=True)
    
    siren = Column(String, index=True)
    nom = Column(String, nullable=False)

    # --- Coordonnées ---
    adresse = Column(String)
    code_postal = Column(String)
    ville = Column(String)
    pays = Column(String)
    telephone = Column(String)
    email = Column(String)
    site_web = Column(String)

    # --- Informations légales ---
    forme_juridique = Column(String)
    code_naf = Column(String)
    activite_principale = Column(String)
    capital_social = Column(String)
    date_creation = Column(String)
    tranche_effectif = Column(String)

    # --- Données JSONB ---

    # Liste des dirigeants
    # Chaque élément : {
    #   "nom": str,
    #   "prenom": str,
    #   "poste": str,
    #   "email": str,
    #   "numTel": str,
    #   "profilLinkedin": str
    # }
    dirigeants = Column(JSONB, default=list)

    # Liste des appels d'offres
    # Chaque élément : {
    #   "besoin": str,
    #   "dateLimiteReponse": str,
    #   "titulaire": str,
    #   "nature": str,
    #   "dateDerniereModification": str,
    #   "lienOffre": str
    # }
    appels_offres = Column(JSONB, default=dict)

    # --- Traçabilité des sources ---
    # Exemple : {"nom": "pappers", "telephone": "linkedin", "appels_offres": "boamp"}
    sources = Column(JSONB, default=dict)

    # --- Métadonnées ---
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Entreprise(siret={self.siret}, nom={self.nom})>"
