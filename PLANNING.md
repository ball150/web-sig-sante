# 📅 Planning : WebSIG Sanitaire Parcelles Assainies

Suivi des jalons et échéances du projet. À mettre à jour au fil de l'avancement

---

## Vue d'ensemble

| Semaine | Dates | Tâches clés | Responsable(s) | Livrable attendu | Statut |
|---|---|---|---|---|---|
| Semaine 1 | 11 – 17 août | Nettoyage des données, récupération limites administratives + population, conception MCD/MPD | Sileymane Ball | Schéma MCD/MPD + jeux de données nettoyés |✅|
| Semaine 1 | 11 – 17 août | Préparation en parallèle : installation PostgreSQL/PostGIS/pgRouting, lecture doc GeoDjango/Leaflet | Code Diaw, Aziz Dione, Awa Dione | Environnements prêts | ✅ |
| Semaine 1 → 2 | 15 – 20 août | Création du schéma final PostGIS, import des données (LayerMapping), indexation spatiale | Code Diaw | Base `my_sante` opérationnelle | ✅ |
| Semaine 2 | 20 – 27 août | Modèles spatiaux Django, migrations, vues GeoJSON, configuration admin géographique | Aziz Dione | API GeoJSON fonctionnelle | ✅ |
| Semaine 2 → 3 | 25 – 28 août | Construction topologie de routage (pgRouting) + endpoints itinéraire | Aziz Dione | API itinéraire fonctionnelle | ✅ |
| Semaine 3 | 27 – 31 août | Carte interactive Leaflet, recherche/filtres, fiches d'info, légende, responsive | Awa Dione | Frontend fonctionnel connecté à l'API | ✅ |
| Semaine 3 | 27 – 31 août | Intégration fonctionnalité bonus (itinéraire) côté carte | Aziz Dione + Awa Dione | Calcul d'itinéraire visible sur la carte | ✅ |
| Transversal | 11 – 31 août | Gestion Git (branches, merges), suivi cohérence globale, rédaction continue du rapport, README | Aby Niang | README finalisé, rapport rédigé au fil de l'eau | 🟡 en cours |
| Fin de projet | 31 août | Relecture finale, tests bout-en-bout, finalisation cahier des charges/rapport, préparation soutenance | Toute l'équipe | Livrable complet | ✅ |

**Légende :** ⬜ à faire · 🟡 en cours · ✅ terminé · 🔴 bloqué

---

## Points de vigilance ouverts

- [ ] Confirmer avec Rôle 1 : SRID d'origine des données (32628) vs SRID de la base (4326) reprojection à documenter
- [ ] Confirmer la source précise du réseau routier (GADM ?) dans le cahier des charges
- [ ] Vérifier le nom exact du script de topologie dans `docs/` (référencé comme `setup_routing.sql` dans le README, à confirmer)
- [ ] Décider de la stratégie de merge Git : au fil de l'eau vers `main`, ou tout à la fin ?

