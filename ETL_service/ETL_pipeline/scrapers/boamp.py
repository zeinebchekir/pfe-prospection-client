from datetime import datetime
from .base_scraper import BaseScraper
# Importe tes fonctions d'extraction selon ton arborescence
from extractors.Boamp.data_extraction import get_global_information 

class BoampService(BaseScraper):
    def __init__(self):
        # On initialise la base avec le nom de la source
        super().__init__(nom_source="BOAMP")
        self.base_url = "https://boamp-datadila.opendatasoft.com/api/explore/v2.1/catalog/datasets/boamp/records"

    def defineFilter():
        codes_interet = ["186", "14", "453", "463", "454", "163"]
        codes_formatte = ",".join([f'"{c}"' for c in codes_interet])
        aujourdhui = datetime.now().strftime("%Y-%m-%d")
        
        filtrebomap = f'descripteur_code IN ({codes_formatte}) AND datelimitereponse >= "{aujourdhui}"'
        return filtrebomap  
    
    def source_scraping(self, filtre, limite=20):
        """
        Récupère les prospects bruts depuis l'API en utilisant la session parente.
        """
        
        params = {
            "limit": limite,
            "where": filtre,
            "order_by": "dateparution DESC"
        }

        # 2. APPEL VIA FETCH_DATA (C'est ici la correction principale)
        # On n'utilise plus requests.get() mais la méthode héritée de BaseScraper
        data = self.fetch_data(self.base_url, params=params)

        # 3. Retourne les résultats ou une liste vide si erreur
        if data:
            return data.get("results", [])
        return []


    def data_extraction(self, avis_brut):
        """
        Extrait les données de l'AvisBrut et crée les instances Entreprise et Lead.
        """
        # 2. On utilise tes fonctions d'extraction existantes
        # Note : Assure-toi que get_global_information prend le payload en paramètre
        clean_data = get_global_information(avis_brut)
        
        return clean_data


    