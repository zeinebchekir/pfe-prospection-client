# Rapport d'Architecture ETL

## Section 1 — Architecture Générale

### Les 3 DAGs Principaux
Le pipeline de données repose sur plusieurs DAGs (Directed Acyclic Graphs) définis dans `dag_initial_load.py`. Les trois flux majeurs sont :

- **`initial_load`** : 
  - **Schedule** : `None` (déclenché manuellement)
  - **Rôle** : Ce DAG a pour rôle d'effectuer le chargement initial de la base de données. Il orchestre la récupération de l'historique depuis les sources BOAMP et DataGouv en parallèle, procède à leur extraction, les enrichit, les nettoie, et les sauvegarde dans la base de données de production.
- **`sync_datagouv`** : 
  - **Schedule** : `0 */6 * * *` (toutes les 6 heures)
  - **Rôle** : Ce DAG gère la synchronisation incrémentale (delta) des données d'entreprises. Il interroge l'API SIRENE de l'INSEE pour détecter les numéros SIREN modifiés depuis la dernière exécution, extrait ces modifications, et met à jour la base de données.
- **`sync_boamp`** : 
  - **Schedule** : `0 6 * * *` (tous les jours à 06:00)
  - **Rôle** : Ce DAG assure la synchronisation incrémentale des nouveaux appels d'offres. Il filtre les annonces BOAMP parues depuis la date de la dernière synchronisation, les enrichit avec les données de l'API DataGouv, et les insère dans le système CRM.

### Infrastructure Partagée
- **PostgreSQL** : Utilisé comme base de données relationnelle principale, il stocke à la fois l'état d'exécution (via `sync_state`) et les données métier (tables `raw_leads` pour l'historisation brute et `entreprise` pour les données nettoyées). L'URL de connexion est configurée par la variable d'environnement `DATABASE_URL`.
- **Redis et CeleryExecutor** : *Non déterminables depuis le code source fourni*, mais ces composants constituent le standard classique de l'architecture distribuée d'Apache Airflow pour gérer la file d'attente et la répartition des tâches sur des *workers* asynchrones.
- **Volume Partagé (`shared_tmp`)** : Un répertoire local (`/opt/airflow/shared_tmp`) est utilisé pour l'échange de fichiers JSON temporaires (comme `raw_boamp.json` et `raw_datagouv.json`) entre les différentes tâches d'un même DAG. Cela permet de transférer de gros volumes de données sans saturer la mémoire interne d'Airflow (XCom).

### Le Décorateur `measure_task`
Le décorateur personnalisé `@measure_task` est appliqué sur les fonctions d'exécution des tâches. Il agit comme un mécanisme transversal de télémétrie :
- **Mesure des ressources** : Il enregistre l'utilisation processeur (`psutil.Process().cpu_percent()`) et la consommation de mémoire vive (`memory_info().rss`) au démarrage et à la fin de la tâche.
- **Poussée XCom** : Il pousse les métriques matérielles (`cpu_used`, `ram_used_mb`, `ram_delta_mb`) dans Airflow XCom.
- **Intégration `etl_logger`** : Il génère de manière transparente des logs standardisés en appelant `log_task_start`, `log_task_success` (qui consigne la durée et les détails métier récupérés de XCom), et `log_task_failure` (qui journalise la stack trace et déclenche une notification SSE en cas de crash).

---

## Section 2 — DAG 1 : initial_load

Voici la description séquentielle du déroulement du DAG de chargement initial, organisé en deux branches parallèles (BOAMP et DataGouv).

### 1. Initialisation
- **Nom et fonction** : `init_db` (`init_db`)
- **Entrée** : Aucune.
- **Traitement** : Invoque l'ORM SQLAlchemy (`Base.metadata.create_all`) pour garantir l'existence de toutes les tables du schéma.
- **Sortie** : Structure relationnelle initialisée dans PostgreSQL.
- **Détail technique clé** : Idempotence parfaite ; l'instruction SQL générée est un `CREATE TABLE IF NOT EXISTS`.

### 2. Branche BOAMP

#### 2.1 Scraping BOAMP
- **Nom et fonction** : `scrape_boamp` (`scrape_boamp`)
- **Entrée** : L'API BOAMP DILA (`https://boamp-datadila.opendatasoft.com/api/explore/v2.1/catalog/datasets/boamp/records`). Filtrage par `descripteur_code` et limitation à la date limite de réponse (`datelimitereponse >= aujourdhui`).
- **Traitement** : Exécute une requête HTTP GET via la méthode mère `BaseScraper.fetch_data()`.
- **Sortie** : Fichier JSON brut généré dans `/opt/airflow/shared_tmp/raw_boamp.json`.
- **Détail technique clé** : *Retry logic* robuste implémentée dans `fetch_data`, gérant l'erreur `429 Too Many Requests` avec une attente exponentielle (10s × tentative) sur 4 tentatives, ainsi qu'une gestion explicite du *timeout* réseau.

#### 2.2 Extraction BOAMP
- **Nom et fonction** : `extract_boamp` (`extract_boamp`)
- **Entrée** : Lecture du fichier `raw_boamp.json`.
- **Traitement** : Analyse approfondie du payload variable `donnees`. Le flux est routé selon la clé `perimetre` (ex: MAPA, FNSimple, DIRECTIVE-24) pour extraire dynamiquement les coordonnées de l'acheteur et les spécificités du marché public.
- **Sortie** : Fichier `raw_boamp.json` écrasé avec une structure d'objet plate et harmonisée.
- **Détail technique clé** : Navigation JSON sécurisée (*defensive programming*) grâce à l'utilisation systématique d'accès par défaut (`.get({}, [])`) pour prévenir les crashs `KeyError`.

#### 2.3 Enrichissement BOAMP
- **Nom et fonction** : `enrich_boamp` (`enrich_boamp`)
- **Entrée** : Fichier `raw_boamp.json` harmonisé.
- **Traitement** : Requête l'API Recherche Entreprises (`https://recherche-entreprises.api.gouv.fr/search`) pour chaque enregistrement afin de lui adjoindre des métadonnées (CA, effectifs). La résolution s'opère par cascade : via le SIRET d'abord, par le SIREN ensuite, puis en *fallback* par le "Nom + Ville".
- **Sortie** : Fichier `raw_boamp.json` mis à jour et enrichi.
- **Détail technique clé** : *Rate Limit* manuel imposé par une pause sémantique (`time.sleep(random.uniform(1.5, 2.0))`) pour protéger la stabilité de l'API gouvernementale et éviter le bannissement d'IP.

#### 2.4 Chargement Brut BOAMP
- **Nom et fonction** : `load_raw_boamp` (`load_raw_boamp`)
- **Entrée** : Fichier `raw_boamp.json`.
- **Traitement** : Préparation des objets ORM `RawLead` conservant la traçabilité d'exécution (ID de DAG, date de scraping) et le blob source.
- **Sortie** : Lignes insérées en masse (*bulk insert*) dans la table de staging `raw_leads`.
- **Détail technique clé** : Récupération intelligente de l'ID primaire généré par PostgreSQL (`_raw_lead_id`) pour le réinjecter dans le flux mémoire, garantissant la liaison relationnelle pour la table finale.

#### 2.5 Nettoyage BOAMP
- **Nom et fonction** : `clean_boamp` (`clean_boamp`)
- **Entrée** : Fichier `raw_boamp.json`.
- **Traitement** : Validation des données par la classe `BoampCleaner` pour s'assurer du formatage (typage, élimination d'anomalies).
- **Sortie** : Données nettoyées réécrites dans `raw_boamp.json`.
- **Détail technique clé** : Génération d'un rapport de validation intégré aux logs de la tâche.

#### 2.6 Chargement Propre BOAMP
- **Nom et fonction** : `load_clean_boamp` (`load_clean_boamp`)
- **Entrée** : Fichier `raw_boamp.json`.
- **Traitement** : Mappe les dictionnaires nettoyés vers le modèle SQLAlchemy `Entreprise` et effectue l'insertion finale.
- **Sortie** : Données consolidées dans la table de production `entreprise`.
- **Détail technique clé** : Opération *UPSERT* (fonctionnalité native PostgreSQL `ON CONFLICT DO UPDATE`). La résolution des conflits est gérée dynamiquement par SIREN, puis SIRET, ou la paire "Nom + Code Postal".

### 3. Branche DataGouv

#### 3.1 Scraping DataGouv
- **Nom et fonction** : `scrape_datagouv` (`scrape_datagouv`)
- **Entrée** : L'API Recherche Entreprises (`https://recherche-entreprises.api.gouv.fr/search`). Le filtre injecte `etat_administratif=A`.
- **Traitement** : Effectue la collecte complète de la population d'entreprises visées via l'algorithme de la classe `DataGouvService`.
- **Sortie** : Fichier JSON brut enregistré sous `/opt/airflow/shared_tmp/raw_datagouv.json`.
- **Détail technique clé** : Stratégie de *pagination itérative* (`_paginer`) s'arrêtant après 40 pages maximum (à raison de 25 éléments/page). Un *retry* spécifique de 3 tentatives est encapsulé sur la requête par page avec un *backoff* de 10s.

#### 3.2 Extraction DataGouv
- **Nom et fonction** : `extract_datagouv` (`extract_datagouv`)
- **Entrée** : Fichier `raw_datagouv.json`.
- **Traitement** : Isole les données du siège social (notamment le SIRET de l'objet imbriqué `siege`), les données de chiffre d'affaires, et pré-filtre les dirigeants sur le type "personne physique".
- **Sortie** : Fichier `raw_datagouv.json` aplati.
- **Détail technique clé** : Les URL de profils LinkedIn sont générées de manière sous-jacente à ce stade par le biais d'appels à l'API externe Serper.

Les étapes suivantes pour DataGouv (chargement brut `load_raw_datagouv`, nettoyage `clean_datagouv` et chargement propre `load_clean_datagouv`) reflètent la même ingénierie de persistance que la branche BOAMP, avec pour subtilité technique l'usage d'un dictionnaire de "cache en mémoire" lors du *UPSERT* final afin d'empêcher les erreurs de doublons au sein d'un même lot non *flushé* (*batch collision avoidance*).

### 4. Étapes de Finalisation (Communes)

- **Nom et fonction** : `rapport_final` (`rapport_final`)
  - **Traitement** : Agrège les volumes (total extraits, total nettoyés) récupérés depuis Airflow XCom. Met à jour la table PostgreSQL `sync_state` fixant ainsi le *watermark* temporel validant le succès pour de futures itérations incrémentales.
- **Nom et fonction** : `cleanup` (`cleanup`)
  - **Traitement** : Détruit définitivement les fichiers d'état transitoire stockés sur disque (`raw_boamp.json`, `raw_datagouv.json`).
  - **Détail technique clé** : Garantit un système de fichiers propre et prévient toute corruption ou fuite de données lors de la prochaine exécution DAG.

---

## Section 3 — DAG 2 : sync_datagouv

Le DAG `sync_datagouv` exécute la synchronisation delta des entreprises en s'appuyant sur l'API SIRENE.

### 1. Scraping SIRENE et DataGouv
- **Nom et fonction** : `scrape_sirene` (`scrape_sirene`)
- **Entrée** : Le *watermark* de dernière synchronisation (`last_sync`) est récupéré depuis la table `sync_state`. L'API INSEE SIRENE (`https://api.insee.fr/api-sirene/3.11/siren`) est ensuite interrogée avec un token d'authentification et le filtre temporel `dateDernierTraitementUniteLegale:[{date_sync} TO *]`.
- **Traitement** : 
  1. **Pagination par curseur (API INSEE)** : La classe `SireneService` utilise le paramètre `curseur` (initialisé à `*`, puis mis à jour via `header.curseurSuivant`) pour naviguer dans les résultats. La limite est fixée à 200 éléments par page pour isoler tous les SIREN récemment modifiés.
  2. **Enrichissement ciblé** : Une fois la liste des SIREN modifiés compilée, `SireneService` délègue l'enrichissement à `DataGouvService.get_data_from_siren()`. Ce dernier effectue une requête individuelle à l'API Recherche Entreprises (`https://recherche-entreprises.api.gouv.fr/search?q={siren}`) pour chaque numéro SIREN extrait.
- **Sortie** : Fichier JSON (`/opt/airflow/shared_tmp/raw_datagouv.json`) contenant les données riches DataGouv des entreprises modifiées.
- **Détail technique clé** : Le flux exact est le suivant : Liste SIREN (INSEE) → Enrichissement DataGouv par SIREN → Extraction globale.

### 2. Extraction DataGouv
- **Nom et fonction** : `extract_datagouv` (`extract_datagouv`)
- **Entrée** : Fichier `raw_datagouv.json`.
- **Traitement** : Aplati le JSON brut, gère la recherche d'URL LinkedIn via Google Serper, et structure les dirigeants et finances.
- **Sortie** : Fichier JSON réécrit et structuré.

### 3. Chargement Brut DataGouv
- **Nom et fonction** : `load_raw_datagouv` (`load_raw_datagouv`)
- **Entrée** : Fichier `raw_datagouv.json`.
- **Traitement** : Historisation des payloads bruts avec le `dag_run_id`.
- **Sortie** : Insertion dans la table PostgreSQL `raw_leads`.

### 4. Nettoyage DataGouv
- **Nom et fonction** : `clean_datagouv` (`clean_datagouv`)
- **Entrée** : Fichier `raw_datagouv.json`.
- **Traitement** : Contrôle qualité et validation typologique.
- **Sortie** : Fichier de données prêtes à l'intégration.

### 5. Chargement Propre SIRENE
- **Nom et fonction** : `load_clean_sirene` (`load_clean_sirene`)
- **Entrée** : Fichier `raw_datagouv.json` nettoyé.
- **Traitement** : Intégration en base via un processus d'UPSERT.
- **Sortie** : Mise à jour ou insertion dans la table PostgreSQL `entreprise`.

### 6. Rapport Final et Cleanup
- **Nom et fonction** : `rapport_final` (`rapport_final`) et `cleanup` (`cleanup`)
- **Traitement** : Le `rapport_final` tire la variable `watermark_start` depuis XCom et met à jour le `last_sync` dans la table PostgreSQL `sync_state`. Le watermark assure la continuité de l'état (Stateful ETL) pour la prochaine itération. La tâche `cleanup` efface les JSON temporaires.

---

## Section 4 — DAG 3 : sync_boamp

Le DAG `sync_boamp` est responsable de la captation quotidienne des nouveaux appels d'offres.

### 1. Scraping BOAMP (Mode Incrémental)
- **Nom et fonction** : `scrape_boamp` (`scrape_boamp` avec `is_incremental=True`)
- **Entrée** : L'API BOAMP (`https://boamp-datadila.opendatasoft.com/api/explore/v2.1/catalog/datasets/boamp/records`). La requête combine les secteurs d'activité cibles (`descripteur_code IN (...)`), un filtre de validité (`datelimitereponse >= aujourdhui`) et le *watermark* temporel issu de la table `sync_state` (`dateparution >= last_sync`).
- **Traitement** : Téléchargement asynchrone des appels d'offres parus depuis le dernier run.
- **Sortie** : Fichier `/opt/airflow/shared_tmp/raw_boamp.json`.

### 2. Extraction BOAMP
- **Nom et fonction** : `extract_boamp` (`extract_boamp`)
- **Entrée** : Fichier `raw_boamp.json`.
- **Traitement** : L'extraction relève le défi du texte français non structuré au sein de la balise `donnees`. 
  - La **deadline (date limite)** est extraite de structures variables selon le périmètre (ex: `procedure.dateReceptionOffres` pour *FNSimple*, ou `delais.receptionOffres` pour *MAPA*).
  - Le **montant du marché** est capté de manière résiliente : le code inspecte `natureMarche.valeurEstimee.valeur`, puis tente un *fallback* sur les fourchettes (`fourchette.valeurHaute` ou `valeurBasse`), ou via le noeud XML/JSON `efbc:OverallMaximumFrameworkContractsAmount` pour la norme *DIRECTIVE-24*.
- **Sortie** : Fichier JSON extrait avec objets normalisés en mémoire.

### 3. Enrichissement BOAMP
- **Nom et fonction** : `enrich_boamp` (`enrich_boamp`)
- **Entrée** : Fichier `raw_boamp.json` extrait.
- **Traitement** : Croisement de données critique : pour compenser le manque de métadonnées d'entreprise (comme la taille ou le CA) dans BOAMP, l'extracteur interroge l'API `https://recherche-entreprises.api.gouv.fr/search` en s'appuyant sur le SIRET extrait, le SIREN déduit, ou le binôme "nom + ville".
- **Sortie** : Fichier `raw_boamp.json` augmenté des données structurelles DataGouv.

### 4. Chargement Brut BOAMP
- **Nom et fonction** : `load_raw_boamp` (`load_raw_boamp`)
- **Entrée** : Fichier `raw_boamp.json`.
- **Traitement** : Sauvegarde des blocs originels `donnees` complets et des traces d'exécution.
- **Sortie** : Table PostgreSQL `raw_leads`.

### 5. Nettoyage BOAMP
- **Nom et fonction** : `clean_boamp` (`clean_boamp`)
- **Entrée** : Fichier `raw_boamp.json`.
- **Traitement** : Traitement de cohérence (formats de téléphone, uniformisation des codes postaux).
- **Sortie** : Fichier prêt au chargement.

### 6. Chargement Propre BOAMP
- **Nom et fonction** : `load_clean_boamp` (`load_clean_boamp`)
- **Entrée** : Fichier nettoyé `raw_boamp.json`.
- **Traitement** : Upsert des données consolidées entreprise + offre commerciale.
- **Sortie** : Enregistrement dans la table PostgreSQL `entreprise`.

### 7. Rapport Final et Cleanup
- **Nom et fonction** : `rapport_final` (`rapport_final`) et `cleanup` (`cleanup`)
- **Traitement** : Mise à jour du curseur d'historisation `last_sync` pour la source `BOAMP` dans la table `sync_state`, et suppression du ficher d'échange temporaire `raw_boamp.json`.

---

## Section 5 — Enrichissement URL LinkedIn

Le processus de récupération automatisée des profils LinkedIn représente une étape clé de l'enrichissement sémantique du pipeline.

- **Tâche déclencheuse** : L'enrichissement est intégré directement à l'étape d'extraction des données DataGouv, au sein de la fonction `extract_data_from_datagouv()` (appelée par la tâche `extract_datagouv`). 
- **Flux de données et recherche Google** : Lorsque le payload DataGouv est reçu, le système filtre la liste des dirigeants pour ne conserver que les profils de type "personne physique". Pour chaque profil qualifié, la fonction `get_linkedin_url(nom, prenom, nom_entreprise)` (définie dans `linkedin_enricher.py`) est invoquée. Cette fonction effectue un appel API HTTP POST vers le service externe Google Serper (`google.serper.dev/search`). La requête de recherche utilisée tire parti d'opérateurs booléens stricts (Google Dorks) : `"{prenom} {nom}" "{entreprise}" site:linkedin.com/in/`.
- **Mécanismes de fallback et résilience** : 
  1. Si le profil n'est pas identifié formellement (par exemple, si le lien contient `/pub/dir/` ou `/search/`, indiquant un annuaire et non un profil direct), la fonction retourne `None` silencieusement pour éviter d'insérer des liens erronés.
  2. Si le quota de requêtes de la clé API Serper est épuisé (code erreur 403), le système déclenche un mécanisme de fallback type "Round-Robin", permutant automatiquement sur la prochaine clé disponible dans une liste de secours prédéfinie, garantissant ainsi la continuité de service.
- **Sortie** : Le dictionnaire de chaque dirigeant est mis à jour avec le champ `linkedin_url`, qui est ensuite sérialisé dans la colonne JSONB `dirigeants` de la table finale `entreprise`.

---

## Section 6 — Mécanismes Transversaux

Le pipeline s'appuie sur des composants transversaux partagés par les trois DAGs pour assurer l'observabilité, la traçabilité et la robustesse globale :

- **Le décorateur `@measure_task`** : Cette fonction générique (dans `dag_initial_load.py`) enveloppe chaque exécution de tâche. Elle capture un cliché des ressources système via la librairie `psutil` (consommation RAM et utilisation CPU) avant et après l'exécution. Ces métriques sont ensuite transmises à Airflow via `ti.xcom_push()`. Elle attrape également les exceptions (`except Exception as exc`) pour appeler la journalisation d'erreur avant d'effectuer un `raise` obligatoire afin que la tâche Airflow soit bien marquée en échec (`FAILED`).
- **Génération de Logs (`etl_logger.py`)** : Le système génère dynamiquement des fichiers de logs physiques quotidiens consolidés par DAG (au format `exports/etl_logs/{dag_id}__{today}.txt`). Les méthodes `log_task_start`, `log_task_success` et `log_task_failure` inscrivent l'horodatage, le résultat et les détails des XComs. Surtout, en cas d'erreur bloquante, `log_task_failure` appelle la méthode `notify_failure()`, qui expédie un événement via une requête HTTP POST non-bloquante au backend FastAPI pour déclencher une notification temps-réel (SSE) sur l'interface de l'administrateur.
- **Validateur `rapport_final`** : Intervenant en bout de chaîne, cette tâche tire l'ensemble des métadonnées des XComs. Si et seulement si toutes les tâches en amont ont réussi, elle consolide les résultats, clôture l'exécution et met à jour le *watermark* d'extraction (`last_sync`) dans la table `sync_state`. Cela empêche la corruption des états delta en cas d'interruption partielle d'un DAG.
- **Tâche `cleanup`** : Agit comme une commande de "ramasse-miettes", supprimant avec la commande `os.remove` les fichiers JSON de staging transitifs situés sur le disque partagé pour libérer de l'espace disque.
- **Gestion Avancée des Erreurs** : L'objet `BaseScraper` protège contre les indisponibilités de réseau externes. Il instaure des tolérances au *timeout* (`timeout=(30, 60)`) lors de l'appel aux API distantes. De plus, il implémente la détection intelligente des `None` consécutifs : si une cible (comme DataGouv) ne répond plus durant plus de 5 appels d'affilée (`MAX_NONE_CONSECUTIFS`), une exception de type `ConnectionError` est déclenchée pour interrompre immédiatement le traitement et alerter les développeurs.

---

## Section 7 — Tableau Récapitulatif des Flux de Données

| DAG | Tâche | Fonction Python | API Source | Table PostgreSQL | Champs Clés Extraits |
|---|---|---|---|---|---|
| `initial_load` | `scrape_boamp` | `scrape_boamp` | API BOAMP | *Fichier JSON* | Payload brut (`donnees`), `descripteur_code`, `dateparution` |
| `initial_load` | `extract_boamp` | `extract_boamp` | *Fichier Local* | *Fichier JSON* | `besoin`, `date_limite`, `valeurMarche`, `titulaire`, `nature` |
| `initial_load` | `enrich_boamp` | `enrich_boamp` | API DataGouv | *Fichier JSON* | CA, Taille de l'entreprise, Dirigeants, SIRET, SIREN |
| `initial_load` | `load_raw_boamp` | `load_raw_boamp` | *Fichier Local* | `raw_leads` | JSON brut complet (sauvegarde historique) |
| `initial_load` | `clean_boamp` | `clean_boamp` | *Fichier Local* | *Fichier JSON* | Codes postaux uniformisés, Emails extraits |
| `initial_load` | `load_clean_boamp` | `load_clean_boamp` | *Fichier Local* | `entreprise` | Upsert final de l'objet complet prospect |
| `initial_load` | `scrape_datagouv` | `scrape_datagouv` | API DataGouv | *Fichier JSON* | Base complète SIREN filtrée sur l'état administratif actif |
| `initial_load` | `extract_datagouv` | `extract_datagouv` | API Google Serper | *Fichier JSON* | Siège (adresse/ville), Secteur, LinkedIn URL, Dirigeants physiques |
| `initial_load` | `load_raw_datagouv` | `load_raw_datagouv` | *Fichier Local* | `raw_leads` | JSON brut (DataGouv complet) |
| `initial_load` | `clean_datagouv` | `clean_datagouv` | *Fichier Local* | *Fichier JSON* | Application des règles de nettoyage |
| `initial_load` | `load_clean_datagouv` | `load_clean_datagouv` | *Fichier Local* | `entreprise` | Upsert final des entreprises DataGouv |
| `sync_datagouv` | `scrape_sirene` | `scrape_sirene` | API INSEE SIRENE & API DataGouv | *Fichier JSON* | SIREN modifiés, puis fetch détaillé du siège DataGouv |
| `sync_datagouv` | `extract_datagouv` | `extract_datagouv` | API Google Serper | *Fichier JSON* | Idem initial : Forme juridique, taille entreprise, CA, LinkedIn |
| `sync_datagouv` | `load_raw_datagouv` | `load_raw_datagouv` | *Fichier Local* | `raw_leads` | Historisation du delta de modification |
| `sync_datagouv` | `clean_datagouv` | `clean_datagouv` | *Fichier Local* | *Fichier JSON* | Données structurées et standardisées |
| `sync_datagouv` | `load_clean_sirene` | `load_clean_sirene` | *Fichier Local* | `entreprise` | Mise à jour conditionnelle (`identifiant`) en BD |
| `sync_boamp` | `scrape_boamp` (inc) | `scrape_boamp` | API BOAMP | *Fichier JSON* | Filtre sur la date d'extraction Delta (depuis `last_sync`) |
| `sync_boamp` | `extract_boamp` | `extract_boamp` | *Fichier Local* | *Fichier JSON* | Nouvelles offres commerciales structurées |
| `sync_boamp` | `enrich_boamp` | `enrich_boamp` | API DataGouv | *Fichier JSON* | Ajout du contexte de l'acheteur via fallback |
| `sync_boamp` | `load_raw_boamp` | `load_raw_boamp` | *Fichier Local* | `raw_leads` | Sauvegarde en staging (blob technique) |
| `sync_boamp` | `clean_boamp` | `clean_boamp` | *Fichier Local* | *Fichier JSON* | Formatage métier |
| `sync_boamp` | `load_clean_boamp` | `load_clean_boamp` | *Fichier Local* | `entreprise` | Ingestion des nouvelles opportunités en base commerciale |

---

## Conclusion de l'Architecture ETL

L'architecture du pipeline ETL mise en place dans le cadre de ce projet démontre une conception modulaire, hautement résiliente et fondamentalement orientée pour la production. L'approche découplée — séparant strictement l'Extraction (scraping asynchrone), la Transformation (nettoyage métier) et le Chargement (upsert PostgreSQL transactionnel) — offre une grande souplesse pour l'évolution de la solution, qu'il s'agisse d'ajouter une nouvelle source gouvernementale ou un nouveau moteur d'enrichissement par l'intelligence artificielle (comme l'intégration LinkedIn Serper). L'utilisation d'Apache Airflow permet de fiabiliser les synchronisations delta au moyen de mécanismes d'orchestration asynchrones basés sur la notion de "Stateful Watermarks" (`sync_state`), garantissant qu'aucune donnée n'est perdue en cas d'interruption du pipeline.

Les points forts techniques de ce système sont multiples : l'adoption rigoureuse de la programmation défensive contre la volatilité des APIs externes (gestion de *rate limit* paramétrable, retentatives exponentielles, isolation des données brutes en base avant tout formatage), le support intégré de l'observabilité par le biais des notifications *Server-Sent Events* et d'un *logging* transversal, ainsi que l'utilisation innovante du SQL UPSERT couplée à un espace temporaire optimisé (*Shared Disk*). Cette architecture assure une qualité de donnée irréprochable au sein du CRM et réduit considérablement l'empreinte opérationnelle nécessaire au maintien d'une veille commerciale fiable.
