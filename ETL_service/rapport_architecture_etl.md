# Rapport d'Architecture : Service ETL (ETL_service)

Ce document décrit la structure de dossiers et l'utilité des composants du répertoire cible `ETL_service`. Ce service hybride repose sur une infrastructure conteneurisée gérant à la fois la couche **Orchestration / Planification** (Apache Airflow), la couche **API/Exposition** (FastAPI) et la couche métallo / **Web Scraping** de récupération des données (Pipeline ETL Python).

---

## 🏗️ 1. Racine du Projet (`/ETL_service/`)
Le dossier racine gère l'infrastructure, l'orchestration principale (Airflow), le déploiement Docker et les dépendances.

*   **`docker-compose.yml`** : Fichier central d'orchestration de conteneurs. Il soulève les services pour Airflow (Webserver, Scheduler, Celery Worker, Triggerer), la base de données PostgreSQL, le cache Redis (pour le broker Celery), ainsi que le service FastAPI en parallèle.
*   **`dockerfile.airflow` & `dockerfile.apis`** : Recettes de construction d'images Docker personnalisées. L'une pour ajouter des dépendances spécifiques à l'image Airflow officielle, l'autre dédiée à construire l'environnement pour FastAPI.
*   **`.env`** : Variables d’environnement secrètes (Credentials Azure, configuration de base de données, JWT, clés d'API (INSEE)).
*   **`requirements.txt` / `requirements.airflow.txt`** : Gestion des bibliothèques et paquets Python.
*   **`venv/`** : L'environnement virtuel de développement Python en local.

---

## ⚙️ 2. Structure Airflow (Orchestration)
Dossiers directement montés (`volumes`) dans les conteneurs Airflow pour configurer l'ordonnanceur.

*   **`dags/`** : (Directed Acyclic Graphs). C’est ici qu’est contenue la logique de planification. Ex: `dag_initial_load.py` qui orchestre l'ordre d'exécution (quand lancer tel scraper, dans quelles dépendances mutuelles, avec quelle fréquence).
*   **`logs/`** : Historique et logs d'exécution de toutes les tâches gérées de manière distribuée par Airflow. Indispensable au monitoring et débogage.
*   **`config/`** : Fichiers permettant de surcharger la configuration d'Airflow (ex: `airflow.cfg`).
*   **`plugins/`** : Répertoire pour rajouter des extensions fonctionnelles à Apache Airflow (opérateurs personnalisés, vues UI additionnelles, macros).
*   **`exports/`** : Un répertoire partagé prévu pour recueillir les fichiers générés par le pipeline (ex: classeurs Excel ou exports `.csv`).

---

## 🚀 3. Cœur Métier : `ETL_pipeline/`
Ce dossier contient la véritable intelligence d'extraction et de traitement (le code métier), déconnectée du moteur d'orchestration, afin que le code puisse être testé, exécuté ou importé par n'importe quelle interface (FastAPI ou Airflow).

### `ETL_pipeline/scrapers/`
L'outil d'extraction "brute".
*   **Rôle** : Scripts purs qui se connectent aux sources distantes (APIs publiques, Web) pour tirer la data.
*   **Contenu** : 
    *   `base_scraper.py` (Classe ou fonctions mères communes)
    *   `boamp.py`, `dataGouv.py`, `sirene.py`, `outlook.py` (Scripts dédiés par source).

### `ETL_pipeline/extractors/`
L'outil de récupération formelle, parsing, et sérialisation.
*   **Rôle** : Reçoit la donnée brute récupérée par les scrapers. Formate, nettoie et consolide l’information pour se préparer à l’insertion en base de données.
*   **Contenu** : Sous-dossiers spécifiques avec des utilitaires modulaires (`Boamp/`, `dataGouv/`, `outlook/`).

### `ETL_pipeline/db/`
La couche de stockage et modèles de données.
*   **Rôle** : ORM (ex: via SQLAlchemy ou des scripts purs psycopg2) modélisant le schéma des données cibles dans PostgreSQL, ainsi que les scripts d'insertion/upsert de la donnée (le "L" de ETL - *Load*).

### `ETL_pipeline/apis/`
L'exposition des données et déclenchement ciblé.
*   **Rôle** : Routes FastAPI qui permettent d'interroger la base de données finalisée ou de déclencher manuellement une tâche de flux.

### `ETL_pipeline/exports/`
*   **Rôle** : Sauvegarde interne, transit en staging avant l'achèvement d'un fichier rapport global.

---

## Synthèse du Workflow
1.  **Airflow (`dags/`)** est planifié, ou une route **FastAPI (`apis/`)** est appelée.
2.  L'outil appelle **`ETL_pipeline/scrapers/`** pour récupérer la donnée fraîche sur internet.
3.  La donnée transite par **`ETL_pipeline/extractors/`** pour subir un nettoyage/renommage (Transformation).
4.  Les scripts dans **`ETL_pipeline/db/`** valident formellement la donnée et l'injectent dans TensorFlow / PostgreSQL de façon pérenne.
