# API Backend — Carte sanitaire interactive (Parcelles Assainies)

Documentation à destination du membre **Frontend Leaflet**. Toutes les routes sont préfixées par `/api/`.

Base locale de développement : `http://127.0.0.1:8000/api/`

---

## 1. `GET /api/etablissements/`

Liste des établissements de santé, avec filtres combinables.

**Paramètres (tous optionnels, combinables) :**

| Paramètre | Type | Description |
|---|---|---|
| `type` | texte | Filtre par type d'établissement (recherche partielle, insensible à la casse) |
| `quartier` | texte | Filtre par nom de quartier |
| `secteur` | texte | Filtre par secteur (actuellement toujours vide, donnée non disponible) |
| `search` | texte | Recherche libre dans le nom ou l'adresse |

**Exemple de requête :**
```
GET /api/etablissements/?type=Poste de santé&quartier=Camberene
```

**Exemple de réponse :**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": { "type": "Point", "coordinates": [-17.419660175, 14.769881555] },
      "properties": {
        "id": 1,
        "nom": "PS CAMBERENE",
        "adresse": "Poste de santé",
        "capacite": null,
        "type": "Poste de santé",
        "quartier": "Camberene",
        "secteur": null
      }
    }
  ]
}
```

**Erreurs possibles :** aucune — un filtre sans résultat renvoie `"features": []`, jamais d'erreur.

**Notes pour l'intégration Leaflet :**
- Utilisable directement avec `L.geoJSON(data).addTo(map)`.
- `secteur` sera toujours `null` tant que Membre 1 n'a pas fourni cette donnée — prévoir un affichage "Non renseigné" dans les popups plutôt qu'un champ vide.
- `capacite` est également `null` pour tous les établissements actuellement.

---

## 2. `GET /api/quartiers/`

Polygones des 4 quartiers, avec nombre d'établissements par quartier.

**Paramètres :** aucun.

**Exemple de réponse :**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": { "type": "MultiPolygon", "coordinates": [ ... ] },
      "properties": { "id": 1, "nom": "Camberene", "commune": "Parcelles Assainies", "nb_etablissements": 4 }
    }
  ]
}
```

**Usage suggéré :** couche de fond (contours de quartiers), choroplèthe colorée selon `nb_etablissements`.

---

## 3. `GET /api/communes/`

Polygone de la commune (1 seule feature : "Parcelles Assainies").

**Paramètres :** aucun.

**Exemple de réponse :**
```json
{
  "type": "FeatureCollection",
  "features": [
    { "type": "Feature", "geometry": { "type": "MultiPolygon", "coordinates": [ ... ] }, "properties": { "id": 1, "nom": "Parcelles Assainies" } }
  ]
}
```

---

## 4. `GET /api/types-etablissements/`

Liste simple des types d'établissement (pour peupler un menu déroulant de filtre).

**Exemple de réponse :**
```json
{
  "types": [
    { "id_type": 1, "libelle_type": "Centre de santé" },
    { "id_type": 2, "libelle_type": "Hôpital" },
    { "id_type": 3, "libelle_type": "Poste de santé" }
  ]
}
```

---

## 5. `GET /api/secteurs/`

Liste simple des secteurs (actuellement vide, table non peuplée).

**Exemple de réponse :**
```json
{ "secteurs": [] }
```

---

## 6. `GET /api/etablissement-proche/`

Établissement(s) le(s) plus proche(s) d'un point donné, triés par distance réelle.

**Paramètres :**

| Paramètre | Type | Obligatoire | Description |
|---|---|---|---|
| `lat` | nombre | oui | Latitude du point utilisateur |
| `lon` | nombre | oui | Longitude du point utilisateur |
| `limit` | entier | non (défaut : 1) | Nombre de résultats à retourner |

**Exemple de requête :**
```
GET /api/etablissement-proche/?lat=14.755&lon=-17.44&limit=3
```

**Exemple de réponse :**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": { "type": "Point", "coordinates": [-17.438517437, 14.757436615] },
      "properties": {
        "id": 25, "nom": "CS ABDOU AZIZ SY DABAKH", "type": "Centre de santé",
        "quartier": "Parcelles Assainies", "distance_m": 314.4
      }
    }
  ]
}
```

**Erreurs possibles :**
- `400` si `lat`/`lon` manquants ou non numériques.

**Notes :** `distance_m` est une distance réelle à vol d'oiseau en mètres (calcul géodésique PostGIS), pas une distance routière.

---

## 7. `GET /api/zone-desserte/`

Zone de desserte (buffer circulaire) autour d'un établissement.

**Paramètres :**

| Paramètre | Type | Obligatoire | Description |
|---|---|---|---|
| `id` | entier | oui | ID de l'établissement (`id_etablissement`) |
| `rayon` | entier | oui | Rayon en mètres — valeurs acceptées : `500`, `1000`, `2000` uniquement |

**Exemple de requête :**
```
GET /api/zone-desserte/?id=25&rayon=1000
```

**Exemple de réponse :**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": { "type": "Polygon", "coordinates": [ ... ] },
      "properties": { "etablissement_id": 25, "nom": "CS ABDOU AZIZ SY DABAKH", "type": "Centre de santé", "rayon_m": 1000 }
    }
  ]
}
```

**Erreurs possibles :**
- `400` si `rayon` absent ou hors des valeurs autorisées (500/1000/2000).
- `404` si l'établissement n'existe pas.

**Note méthodologique à afficher côté frontend (recommandé) :** ce buffer est un cercle géométrique à vol d'oiseau, pas une isochrone piétonne réelle.

---

## 8. `GET /api/statistiques/`

Statistiques globales pour un tableau de bord.

**Paramètres :** aucun.

**Exemple de réponse :**
```json
{
  "total_etablissements": 26,
  "par_type": [ { "type": "Poste de santé", "total": 18 }, { "type": "Centre de santé", "total": 6 }, { "type": "Hôpital", "total": 2 } ],
  "par_secteur": [ { "secteur": "Non renseigné", "total": 26 } ],
  "par_quartier": [ { "quartier": "Grand Yoff", "total": 10 }, { "quartier": "Parcelles Assainies", "total": 8 }, { "quartier": "Camberene", "total": 4 }, { "quartier": "Patte D'Oie", "total": 4 } ],
  "population": { "disponible": false, "totale": 0, "masculine": 0, "feminine": 0 }
}
```

**Important pour le frontend :** toujours vérifier `population.disponible` avant d'afficher les chiffres de population — actuellement `false` (donnée en attente côté Membre 1).

---

## 9. `GET /api/accessibilite/`

Indicateur simplifié (population / nombre d'établissements) par quartier.

**Paramètres :** aucun.

**Exemple de réponse :**
```json
{
  "avertissement": "Indicateur spatial simplifié (population / nombre d'établissements). Ne tient pas compte de la distance réelle, de la capacité des établissements, des spécialités offertes, du temps de trajet ni de la qualité des infrastructures. Ce n'est pas un indicateur médical officiel.",
  "quartiers": [
    { "quartier": "Camberene", "population": null, "nb_etablissements": 4, "habitants_par_etablissement": null }
  ]
}
```

**Important pour le frontend :** afficher le champ `avertissement` quelque part visible dans l'interface (bandeau, tooltip). Gérer proprement `habitants_par_etablissement: null` (afficher "Donnée population manquante", pas un blanc ou "NaN").

---

## 10. `GET /api/export/etablissements/`

Identique à `/api/etablissements/` (mêmes filtres, même format), mais force un téléchargement de fichier `.geojson` plutôt qu'un affichage.

**Exemple :**
```
GET /api/export/etablissements/?type=Hôpital
```

---

## Récapitulatif — schéma de flux

```
Backend (Django/PostGIS)
        ↓ GeoJSON
GET /api/etablissements/, /api/quartiers/, /api/communes/
        ↓
Leaflet : L.geoJSON(data).addTo(map)
        ↓
Markers / polygones + popups (via feature.properties)
```

## Limites connues à ce jour (transparence pour le rapport de groupe)

- `secteur` (public/privé) : aucune donnée source, tous les établissements ont `secteur: null`.
- `population` : table non encore peuplée, `/api/statistiques/` et `/api/accessibilite/` renvoient des valeurs `null`/`false` en conséquence, pas des zéros trompeurs.
- `capacite` : non renseignée pour aucun établissement.
- Le SRID des shapefiles de limites administratives contenait une incohérence (métadonnées `.prj` erronées) — corrigée manuellement lors de l'import, documentée dans l'historique Git.
