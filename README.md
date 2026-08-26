# 🏥 Carte Sanitaire Interactive - Commune des Parcelles Assainies

> Une application WebSIG complète permettant de visualiser, interroger et analyser la répartition des infrastructures de santé et la couverture sanitaire dans la commune des Parcelles Assainies.

![Statut du Projet](https://img.shields.io/badge/Statut-En_développement-orange)
![Licence](https://img.shields.io/badge/Licence-Éducative_L3_Géomatique-blue)

---

## 📌 Aperçu / Contexte

Développée dans le cadre du module **Développement WebSIG avec Django** en **Licence 3 Géomatique** à l'Université Iba Der Thiam de Thiès, cette application répond au besoin de cartographier l'offre de soins de santé (postes de santé, centres, pharmacies, secteur privé/public) à l'échelle communale. Elle offre un outil de consultation intuitif pour les citoyens et d'aide à la décision pour les acteurs de santé publique.

<img width="1891" height="920" alt="Capture d&#39;écran 2026-08-25 184011" src="https://github.com/user-attachments/assets/4b1435bb-56f3-4264-a56f-ec5eb8bc5753" />


---

## ✨ Fonctionnalités

### Fonctionnalités de base

* **Fond de carte interactif :** Navigation fluide (zoom, déplacement) avec choix du fond de carte (OpenStreetMap / Imagerie Satellite).
* **Localisation des établissements :** Affichage ponctuel géoréférencé des infrastructures de santé.
* **Fiches d'information (Pop-ups) :** Affichage des attributs détaillés au clic (nom, type, secteur public/privé, capacité, adresse).
* **Recherche et filtres dynamiques :** Recherche textuelle par nom d'établissement et filtrage instantané par catégorie/secteur.
* **Symbologie dynamique :** Classification visuelle des points selon le type de structure.
* **Découpage administratif et démographie :** Intégration des limites de quartiers et des effectifs de population rattachés.

### Fonctionnalité bonus 🌟

* **Calcul d'itinéraire réel (pgRouting) :** Calcul du plus court chemin entre deux établissements de santé, ou entre un point donné et un établissement, en s'appuyant sur un graphe de routage construit à partir du réseau routier (nettoyage topologique + `pgr_dijkstra`). Exposé via les endpoints `/api/itineraire/etablissements/` et `/api/itineraire/`.

---

## 🛠️ Stack Technique

| Composant | Technologie / Outil | Rôle dans l'application |
| :--- | :--- | :--- |
| **Langage Backend** | Python 3.10+ | Traitements serveur et logique métier |
| **Framework Web** | Django 6.1 / GeoDjango | ORM spatial, gestion des vues et API GeoJSON |
| **SGBDR Spatial** | PostgreSQL / PostGIS + pgRouting | Stockage spatial (SRID 4326 - WGS84) et calcul d'itinéraires |
| **Frontend Carto** | Leaflet.js | Rendu de la carte interactive et couches GeoJSON |
| **UI & Styling** | HTML5, CSS3, Bootstrap 5 | Layout responsive, panneaux latéraux et formulaires |
| **Outils SIG** | QGIS 3.x | Préparation et contrôle topologique des données |

---

## 🏗️ Architecture

L'application repose sur un flux de données à 3 tiers :

```text
[ Base PostgreSQL / PostGIS / pgRouting ] 
        │ (Base 'my_sante', SRID 4326)
        ▼
[ Backend GeoDjango ] ──> (Models spatiaux + Vues GeoJSON API + API itinéraire)
        │
        ▼
[ Frontend Leaflet ]  ──> (Carte interactive Web + Interface Bootstrap)
```

---

## ⚙️ Prérequis

Avant de commencer, assure-toi d'avoir installé :

* **Python 3.10+**
* **PostgreSQL** avec les extensions **PostGIS** et **pgRouting**
* **GDAL / GEOS / PROJ** (librairies système requises par GeoDjango)
  * Ubuntu/Debian : `sudo apt install gdal-bin libgdal-dev libgeos-dev libproj-dev`
  * Windows : voir la [documentation officielle GeoDjango](https://docs.djangoproject.com/en/stable/ref/contrib/gis/install/)
* **Git**

---

## 🚀 Installation

1. **Cloner le dépôt** (branche `Backend-GeoDjango`) :
```bash
   git clone -b Backend-GeoDjango https://github.com/ball150/web-sig-sante.git
   cd web-sig-sante
```

2. **Créer un environnement virtuel et l'activer :**
```bash
   python -m venv venv
   source venv/bin/activate      # Linux / Mac
   venv\Scripts\activate         # Windows
```

3. **Installer les dépendances Python :**
```bash
   pip install -r requirements.txt
```

4. **Créer la base de données PostGIS/pgRouting :**
```sql
   CREATE DATABASE my_sante;
   \c my_sante
   CREATE EXTENSION postgis;
   CREATE EXTENSION pgrouting;
```

5. **Configurer les variables d'environnement :**

   Copier `.env.example` en `.env` et renseigner tes propres valeurs :
```bash
   cp .env.example .env
```
```env
   DB_NAME=my_sante
   DB_USER=postgres
   DB_PASSWORD=ton_mot_de_passe
   DB_HOST=localhost
   DB_PORT=5432
   SECRET_KEY=une_cle_secrete_django
   DEBUG=True
```

6. **Appliquer les migrations :**
```bash
   python manage.py migrate
```

7. **Importer les données géographiques et construire le graphe de routage :**

   a. Importer les données de base (établissements, quartiers, routes) :
```bash
      python manage.py import_routes
```
   b. Construire la topologie de routage (script manuel, non géré par les migrations Django) :
```bash
      psql -U postgres -d my_sante -f docs/setup_routing.sql
```
      *(adapter le nom/chemin du fichier si besoin — script de nettoyage topologique `ST_Node` + construction du graphe `pgr_extractVertices`, nécessaire pour que l'API d'itinéraire fonctionne)*

8. **Lancer le serveur de développement :**
```bash
   python manage.py runserver
```
   L'application est accessible sur `http://127.0.0.1:8000/`

---

## 📁 Structure du dépôt

```text
web-sig-sante/
├── config/              # Configuration du projet Django (settings, urls)
├── health/               # App principale : modèles spatiaux, vues, API GeoJSON/itinéraire
├── docs/                 # Documentation technique et scripts (ex. setup_routing.sql)
├── requirements.txt          # Dossier frontend / templates / static si applicable
├── .env.example           # Modèle des variables d'environnement
├── .gitignore
├── manage.py
├── requirements.txt
└── README.md
```


---

## 👥 Organisation de l'équipe

| Rôle | Mission | Responsable |
| :--- | :--- | :--- |
|  Role 1 : Données | Nettoyage des données, récupération des limites administratives et de la population, conception du MCD/MPD | Sileymane Ball |
| Role 2 : Base PostGIS | Création du schéma, import des données, indexation spatiale | Code diaw |
| Role 3 : Backend GeoDjango | Modèles spatiaux, migrations, vues GeoJSON, API itinéraire (pgRouting) | Aziz Dione |
| Role 4 : Frontend Leaflet | Carte interactive, recherche/filtres, fiches d'info, responsive | Awa Dione |
| Role 5 : Coordination & rapport | Cahier des charges, README, gestion du dépôt Git, rédaction du rapport | Aby Niang |

---

## 🗂️ Sources des données

| Jeu de données | Source | Format d'origine | SRID |
| :--- | :--- | :--- | :--- |
| Établissements de santé | GeoSenegal | CSV / LayerMapping SQL | EPSG:32628 |
| Limites administratives (quartiers/commune) | GADM | Shapefile / MultiPolygon | EPSG:32628 |
| Réseau routier | GADM | Shapefile | EPSG:32628 |
| Population | ANSD | CSV attributaire | N/A |

---

## 📄 Licence

Projet réalisé dans un cadre pédagogique Licence 3 Géomatique, Université Iba Der Thiam de Thiès.
