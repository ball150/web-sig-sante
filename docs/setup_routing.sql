-- ============================================================
-- SETUP ROUTING — Reconstruction de la topologie pgRouting
-- ============================================================
-- Ce script n'est PAS géré par les migrations Django.
-- Raison : le nettoyage topologique (ST_Node) et la construction
-- du graphe de routage (pgr_extractVertices) n'ont pas d'équivalent
-- dans l'ORM Django — ce sont des opérations PostGIS/pgRouting
-- pures, à exécuter manuellement une fois après l'import des
-- données de base (voir import_routes, Phase 6 du backend).
--
-- Pré-requis avant d'exécuter ce script :
--   1. La base my_sante existe, PostGIS et pgRouting sont activés :
--        CREATE EXTENSION IF NOT EXISTS postgis;
--        CREATE EXTENSION IF NOT EXISTS pgrouting;
--   2. Les migrations Django ont été appliquées (python manage.py migrate)
--   3. La commande d'import a été lancée : python manage.py import_routes
--      -> elle remplit la table troncon_route (segments bruts, non nettoyés)
--
-- Testé avec pgRouting 4.0.1 (pgr_createTopology n'existe plus depuis
-- la version 4.0 — ce script utilise donc pgr_extractVertices, son
-- remplaçant officiel).
-- ============================================================


-- ============================================================
-- ÉTAPE 1 : Nettoyage topologique avec ST_Node
-- ============================================================
-- Corrige les croisements de routes non connectés dans les données
-- sources (deux lignes qui se croisent visuellement sans partager
-- de nœud commun). Sur ce jeu de données (route_parcelle.shp),
-- environ 645 croisements de ce type avaient été détectés.

DROP TABLE IF EXISTS troncon_route_clean;

CREATE TABLE troncon_route_clean AS
SELECT
    row_number() OVER () AS id,
    geom
FROM (
    SELECT (ST_Dump(ST_Node(ST_Collect(geom)))).geom AS geom
    FROM troncon_route
) AS lignes_eclatees;

ALTER TABLE troncon_route_clean ADD PRIMARY KEY (id);
ALTER TABLE troncon_route_clean ADD COLUMN source INTEGER;
ALTER TABLE troncon_route_clean ADD COLUMN target INTEGER;
ALTER TABLE troncon_route_clean ADD COLUMN cost DOUBLE PRECISION;

CREATE INDEX idx_troncon_clean_geom ON troncon_route_clean USING GIST(geom);

-- Vérification attendue : le nombre de lignes doit être supérieur
-- au nombre de segments importés par import_routes (le nettoyage
-- scinde les lignes aux croisements réels).
-- SELECT COUNT(*) FROM troncon_route_clean;


-- ============================================================
-- ÉTAPE 2 : Construction du graphe de routage
-- ============================================================
-- pgr_createTopology a été supprimée en pgRouting 4.0.
-- Remplacement officiel : pgr_extractVertices + UPDATE manuel
-- des colonnes source/target.

DROP TABLE IF EXISTS troncon_route_vertices;

CREATE TABLE troncon_route_vertices AS
SELECT * FROM pgr_extractVertices('SELECT id, geom FROM troncon_route_clean ORDER BY id');

ALTER TABLE troncon_route_vertices ADD PRIMARY KEY (id);
CREATE INDEX idx_vertices_geom ON troncon_route_vertices USING GIST(geom);

UPDATE troncon_route_clean AS e
SET source = v.id
FROM troncon_route_vertices AS v
WHERE ST_StartPoint(e.geom) = v.geom;

UPDATE troncon_route_clean AS e
SET target = v.id
FROM troncon_route_vertices AS v
WHERE ST_EndPoint(e.geom) = v.geom;

-- Vérification attendue : total, avec_source et avec_target doivent
-- être identiques (ou très proches).
-- SELECT COUNT(*) AS total, COUNT(source) AS avec_source, COUNT(target) AS avec_target
-- FROM troncon_route_clean;


-- ============================================================
-- ÉTAPE 3 : Calcul du coût (distance réelle en mètres)
-- ============================================================

UPDATE troncon_route_clean
SET cost = ST_Length(geom::geography);


-- ============================================================
-- ÉTAPE 4 (optionnelle) : Vérifier la connectivité du réseau
-- ============================================================
-- Sur les données de Parcelles Assainies, environ 97.7% des nœuds
-- se trouvent dans une seule composante connectée (6189 sur 6332).
-- Le reste est fragmenté en petits îlots isolés — normal, mais à
-- garder en tête : un itinéraire entre deux points dans des îlots
-- différents renverra une erreur 404 côté API (géré proprement,
-- voir /api/itineraire/ dans health/views.py).

-- SELECT component, COUNT(*) AS nb_noeuds
-- FROM pgr_connectedComponents('SELECT id, source, target, cost FROM troncon_route_clean')
-- GROUP BY component
-- ORDER BY nb_noeuds DESC
-- LIMIT 10;


-- ============================================================
-- ÉTAPE 5 (optionnelle) : Test manuel du calcul de plus court chemin
-- ============================================================
-- Exemple validé sur ce jeu de données : PS CAMBERENE (nœud 6274)
-- vers PS NATIONS UNIES (nœud 6305) -> distance ~200.9 m.
-- Remplacer les IDs de nœuds par ceux obtenus via :
--   SELECT id FROM troncon_route_vertices ORDER BY geom <-> <point> LIMIT 1;

-- SELECT * FROM pgr_dijkstra(
--     'SELECT id, source, target, cost FROM troncon_route_clean',
--     6274, 6305,
--     directed => false
-- );

-- ============================================================
-- FIN DU SCRIPT
-- ============================================================
-- Une fois ces étapes exécutées, les endpoints Django suivants
-- deviennent fonctionnels :
--   GET /api/itineraire/etablissements/?id1=&id2=
--   GET /api/itineraire/?lat=&lon=&id=
-- ============================================================
