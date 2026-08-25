import json

from django.http import JsonResponse

from .models import EtablissementSante, TypeEtablissement, Secteur


from django.db.models import Q


def types_etablissements(request):
    """Liste simple des types d'établissement (pour peupler un filtre).

    Documenté dans docs/API.md mais absent du code reçu : ajouté ici pour
    que le frontend n'ait pas à déduire les types uniquement depuis les
    résultats déjà chargés (ce qui masque les types sans résultat courant).
    """
    types = list(
        TypeEtablissement.objects.order_by("libelle_type")
        .values("id_type", "libelle_type")
    )
    return JsonResponse({"types": types})


def secteurs(request):
    """Liste simple des secteurs (cf. docs/API.md — table actuellement vide)."""
    data = list(Secteur.objects.order_by("libelle").values("id_secteur", "libelle"))
    return JsonResponse({"secteurs": data})


def _etablissements_queryset(request):
    etablissements = EtablissementSante.objects.select_related(
        "id_type", "id_quartier", "id_secteur"
    )

    type_param = request.GET.get("type")
    quartier_param = request.GET.get("quartier")
    secteur_param = request.GET.get("secteur")
    search_param = request.GET.get("search")

    if type_param:
        etablissements = etablissements.filter(id_type__libelle_type__icontains=type_param)

    if quartier_param:
        etablissements = etablissements.filter(id_quartier__nom__icontains=quartier_param)

    if secteur_param:
        etablissements = etablissements.filter(id_secteur__libelle__icontains=secteur_param)

    if search_param:
        etablissements = etablissements.filter(
            Q(nom__icontains=search_param) | Q(adresse__icontains=search_param)
        )

    return etablissements


def _etablissements_features(etablissements):
    features = []
    for e in etablissements:
        features.append({
            "type": "Feature",
            "geometry": json.loads(e.geom.geojson),
            "properties": {
                "id": e.id_etablissement,
                "nom": e.nom,
                "adresse": e.adresse,
                "capacite": e.capacite,
                "type": e.id_type.libelle_type,
                "quartier": e.id_quartier.nom,
                "secteur": e.id_secteur.libelle if e.id_secteur else None,
            },
        })
    return features


def etablissements_geojson(request):
    etablissements = _etablissements_queryset(request)
    features = _etablissements_features(etablissements)

    return JsonResponse({
        "type": "FeatureCollection",
        "features": features,
    })


def export_etablissements(request):
    """Identique à etablissements_geojson mais force le téléchargement."""
    etablissements = _etablissements_queryset(request)
    features = _etablissements_features(etablissements)

    response = JsonResponse({
        "type": "FeatureCollection",
        "features": features,
    })
    response["Content-Disposition"] = 'attachment; filename="etablissements.geojson"'
    return response

from .models import EtablissementSante, Quartier, Commune


def quartiers_geojson(request):
    quartiers = Quartier.objects.select_related("id_commune")

    features = []
    for q in quartiers:
        features.append({
            "type": "Feature",
            "geometry": json.loads(q.geom.geojson),
            "properties": {
                "id": q.id_quartier,
                "nom": q.nom,
                "commune": q.id_commune.nom,
                "nb_etablissements": q.etablissements.count(),
            },
        })

    return JsonResponse({"type": "FeatureCollection", "features": features})


def communes_geojson(request):
    communes = Commune.objects.all()

    features = []
    for c in communes:
        features.append({
            "type": "Feature",
            "geometry": json.loads(c.geom.geojson),
            "properties": {
                "id": c.id_commune,
                "nom": c.nom,
            },
        })

    return JsonResponse({"type": "FeatureCollection", "features": features})
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance


def etablissement_proche(request):
    lat = request.GET.get("lat")
    lon = request.GET.get("lon")

    if not lat or not lon:
        return JsonResponse({"error": "Paramètres 'lat' et 'lon' requis."}, status=400)

    try:
        lat = float(lat)
        lon = float(lon)
    except ValueError:
        return JsonResponse({"error": "'lat' et 'lon' doivent être des nombres."}, status=400)

    try:
        limit = int(request.GET.get("limit", 1))
    except ValueError:
        limit = 1

    position_utilisateur = Point(lon, lat, srid=4326)

    etablissements = (
        EtablissementSante.objects
        .select_related("id_type", "id_quartier")
        .annotate(distance=Distance("geom", position_utilisateur))
        .order_by("distance")[:limit]
    )

    features = []
    for e in etablissements:
        features.append({
            "type": "Feature",
            "geometry": json.loads(e.geom.geojson),
            "properties": {
                "id": e.id_etablissement,
                "nom": e.nom,
                "type": e.id_type.libelle_type,
                "quartier": e.id_quartier.nom,
                "distance_m": round(e.distance.m, 1),
            },
        })

    return JsonResponse({"type": "FeatureCollection", "features": features})
UTM_SRID = 32628  # UTM zone 28N, système métrique adapté à Dakar

RAYON_MIN = 50
RAYON_MAX = 8000


def zone_desserte(request):
    etablissement_id = request.GET.get("id")
    rayon = request.GET.get("rayon")

    if not etablissement_id:
        return JsonResponse({"error": "Paramètre 'id' requis."}, status=400)

    try:
        rayon = int(rayon)
    except (TypeError, ValueError):
        return JsonResponse({"error": "Paramètre 'rayon' requis (entier, en mètres)."}, status=400)

    if not (RAYON_MIN <= rayon <= RAYON_MAX):
        return JsonResponse(
            {"error": f"Rayon hors limites autorisées ({RAYON_MIN} à {RAYON_MAX} mètres)."},
            status=400,
        )

    try:
        etablissement = EtablissementSante.objects.select_related("id_type").get(
            id_etablissement=etablissement_id
        )
    except EtablissementSante.DoesNotExist:
        return JsonResponse({"error": "Établissement introuvable."}, status=404)

    point_utm = etablissement.geom.transform(UTM_SRID, clone=True)
    buffer_utm = point_utm.buffer(rayon)
    buffer_4326 = buffer_utm.transform(4326, clone=True)

    feature = {
        "type": "Feature",
        "geometry": json.loads(buffer_4326.geojson),
        "properties": {
            "etablissement_id": etablissement.id_etablissement,
            "nom": etablissement.nom,
            "type": etablissement.id_type.libelle_type,
            "rayon_m": rayon,
        },
    }

    return JsonResponse({"type": "FeatureCollection", "features": [feature]})
from django.db.models import Count, Sum

from .models import Population


def statistiques(request):
    total_etablissements = EtablissementSante.objects.count()

    par_type = list(
        EtablissementSante.objects
        .values("id_type__libelle_type")
        .annotate(total=Count("id_etablissement"))
        .order_by("-total")
    )
    par_type = [{"type": r["id_type__libelle_type"], "total": r["total"]} for r in par_type]

    par_secteur = list(
        EtablissementSante.objects
        .values("id_secteur__libelle")
        .annotate(total=Count("id_etablissement"))
        .order_by("-total")
    )
    par_secteur = [
        {"secteur": r["id_secteur__libelle"] or "Non renseigné", "total": r["total"]}
        for r in par_secteur
    ]

    par_quartier = list(
        EtablissementSante.objects
        .values("id_quartier__nom")
        .annotate(total=Count("id_etablissement"))
        .order_by("-total")
    )
    par_quartier = [{"quartier": r["id_quartier__nom"], "total": r["total"]} for r in par_quartier]

    population_data = Population.objects.aggregate(
        effectif=Sum("effectif"),
        masculine=Sum("pop_masculine"),
        feminine=Sum("pop_feminine"),
    )
    population_disponible = population_data["effectif"] is not None

    return JsonResponse({
        "total_etablissements": total_etablissements,
        "par_type": par_type,
        "par_secteur": par_secteur,
        "par_quartier": par_quartier,
        "population": {
            "disponible": population_disponible,
            "totale": population_data["effectif"] or 0,
            "masculine": population_data["masculine"] or 0,
            "feminine": population_data["feminine"] or 0,
        },
    })
def accessibilite(request):
    quartiers = Quartier.objects.select_related("id_commune")

    resultats = []
    for q in quartiers:
        nb_etablissements = q.etablissements.count()

        population_obj = Population.objects.filter(id_quartier=q).first()
        population = population_obj.effectif if population_obj else None

        if population is not None and nb_etablissements > 0:
            indicateur = round(population / nb_etablissements, 1)
        else:
            indicateur = None

        resultats.append({
            "quartier": q.nom,
            "population": population,
            "nb_etablissements": nb_etablissements,
            "habitants_par_etablissement": indicateur,
        })

    return JsonResponse({
        "avertissement": (
            "Indicateur spatial simplifié (population / nombre d'établissements). "
            "Ne tient pas compte de la distance réelle, de la capacité des "
            "établissements, des spécialités offertes, du temps de trajet ni de "
            "la qualité des infrastructures. Ce n'est pas un indicateur médical officiel."
        ),
        "quartiers": resultats,
    })


from django.shortcuts import render

from django.db import connection, DatabaseError


# ==========================================================
# ROUTAGE RÉEL (pgRouting) — voir setup_routing.sql
# ==========================================================
# Ces vues consomment les tables troncon_route_clean /
# troncon_route_vertices construites manuellement via
# setup_routing.sql (hors migrations Django, cf. commentaire
# en tête de ce script). Si ce script n'a pas encore été exécuté
# sur la base de données utilisée, ces vues renvoient une erreur
# 503 explicite plutôt qu'un 500 imprévisible.

def _table_routage_existe():
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT to_regclass('public.troncon_route_clean'), "
            "to_regclass('public.troncon_route_vertices')"
        )
        clean, vertices = cursor.fetchone()
        return clean is not None and vertices is not None


def _plus_proche_noeud(cursor, lon, lat):
    """Retourne l'id du nœud du réseau routier le plus proche d'un point."""
    cursor.execute(
        """
        SELECT id
        FROM troncon_route_vertices
        ORDER BY geom <-> ST_SetSRID(ST_MakePoint(%s, %s), 4326)
        LIMIT 1
        """,
        [lon, lat],
    )
    row = cursor.fetchone()
    return row[0] if row else None


def _calculer_itineraire(cursor, noeud_depart, noeud_arrivee):
    """Exécute pgr_dijkstra et reconstruit la géométrie du trajet.

    Retourne (geojson_line, distance_m) ou (None, None) si aucun chemin
    n'existe entre les deux nœuds (îlots non connectés — cf. setup_routing.sql).
    """
    cursor.execute(
        """
        SELECT dij.edge, dij.agg_cost, e.geom
        FROM pgr_dijkstra(
            'SELECT id, source, target, cost FROM troncon_route_clean',
            %s, %s,
            directed => false
        ) AS dij
        JOIN troncon_route_clean AS e ON e.id = dij.edge
        ORDER BY dij.path_seq
        """,
        [noeud_depart, noeud_arrivee],
    )
    rows = cursor.fetchall()

    if not rows:
        return None, None

    distance_totale = rows[-1][1]

    segment_ids = [str(r[0]) for r in rows]
    cursor.execute(
        f"""
        SELECT ST_AsGeoJSON(ST_LineMerge(ST_Union(geom)))
        FROM troncon_route_clean
        WHERE id IN ({','.join(segment_ids)})
        """
    )
    geojson_str = cursor.fetchone()[0]

    return json.loads(geojson_str), distance_totale


def itineraire_etablissements(request):
    """GET /api/itineraire/etablissements/?id1=&id2=

    Calcule le plus court chemin réel (réseau routier) entre deux
    établissements de santé, via pgRouting.
    """
    if not _table_routage_existe():
        return JsonResponse(
            {"error": "Le réseau de routage n'est pas encore configuré (voir setup_routing.sql)."},
            status=503,
        )

    id1 = request.GET.get("id1")
    id2 = request.GET.get("id2")

    if not id1 or not id2:
        return JsonResponse({"error": "Paramètres 'id1' et 'id2' requis."}, status=400)

    try:
        e1 = EtablissementSante.objects.get(id_etablissement=id1)
        e2 = EtablissementSante.objects.get(id_etablissement=id2)
    except EtablissementSante.DoesNotExist:
        return JsonResponse({"error": "Établissement introuvable."}, status=404)

    with connection.cursor() as cursor:
        noeud1 = _plus_proche_noeud(cursor, e1.geom.x, e1.geom.y)
        noeud2 = _plus_proche_noeud(cursor, e2.geom.x, e2.geom.y)

        if noeud1 is None or noeud2 is None:
            return JsonResponse({"error": "Réseau routier vide."}, status=503)

        geometry, distance_m = _calculer_itineraire(cursor, noeud1, noeud2)

    if geometry is None:
        return JsonResponse(
            {"error": "Aucun itinéraire trouvé (les deux établissements sont probablement "
                      "dans des îlots du réseau non connectés entre eux)."},
            status=404,
        )

    return JsonResponse({
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "depart": e1.nom,
            "arrivee": e2.nom,
            "distance_m": round(distance_m, 1),
        },
    })


def itineraire_point(request):
    """GET /api/itineraire/?lat=&lon=&id=

    Calcule le plus court chemin réel entre un point quelconque
    (ex : position de l'utilisateur) et un établissement de santé.
    """
    if not _table_routage_existe():
        return JsonResponse(
            {"error": "Le réseau de routage n'est pas encore configuré (voir setup_routing.sql)."},
            status=503,
        )

    lat = request.GET.get("lat")
    lon = request.GET.get("lon")
    etablissement_id = request.GET.get("id")

    if not lat or not lon or not etablissement_id:
        return JsonResponse({"error": "Paramètres 'lat', 'lon' et 'id' requis."}, status=400)

    try:
        lat = float(lat)
        lon = float(lon)
    except ValueError:
        return JsonResponse({"error": "'lat' et 'lon' doivent être des nombres."}, status=400)

    try:
        etablissement = EtablissementSante.objects.get(id_etablissement=etablissement_id)
    except EtablissementSante.DoesNotExist:
        return JsonResponse({"error": "Établissement introuvable."}, status=404)

    with connection.cursor() as cursor:
        noeud_depart = _plus_proche_noeud(cursor, lon, lat)
        noeud_arrivee = _plus_proche_noeud(cursor, etablissement.geom.x, etablissement.geom.y)

        if noeud_depart is None or noeud_arrivee is None:
            return JsonResponse({"error": "Réseau routier vide."}, status=503)

        geometry, distance_m = _calculer_itineraire(cursor, noeud_depart, noeud_arrivee)

    if geometry is None:
        return JsonResponse(
            {"error": "Aucun itinéraire trouvé (point probablement hors du réseau connecté)."},
            status=404,
        )

    return JsonResponse({
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "arrivee": etablissement.nom,
            "distance_m": round(distance_m, 1),
        },
    })


VITESSES_M_PAR_MIN = {
    "pied": 83.3,      # ≈ 5 km/h
    "vehicule": 500.0,  # ≈ 30 km/h en ville
}


def zone_desserte_reseau(request):
    """GET /api/zone-desserte-reseau/?id=&minutes=&mode=pied|vehicule

    Vraie isochrone basée sur le réseau routier réel (pgr_drivingDistance),
    par opposition à /api/zone-desserte/ qui trace un simple cercle à vol
    d'oiseau. Retourne l'enveloppe convexe des nœuds atteignables dans le
    temps imparti — une approximation nettement plus réaliste qu'un cercle,
    mais qui reste une enveloppe (pas le détail de chaque rue accessible).
    """
    if not _table_routage_existe():
        return JsonResponse(
            {"error": "Le réseau de routage n'est pas encore configuré (voir setup_routing.sql)."},
            status=503,
        )

    etablissement_id = request.GET.get("id")
    minutes = request.GET.get("minutes")
    mode = request.GET.get("mode", "pied")

    if not etablissement_id or not minutes:
        return JsonResponse({"error": "Paramètres 'id' et 'minutes' requis."}, status=400)

    if mode not in VITESSES_M_PAR_MIN:
        return JsonResponse({"error": "Paramètre 'mode' doit être 'pied' ou 'vehicule'."}, status=400)

    try:
        minutes = float(minutes)
    except ValueError:
        return JsonResponse({"error": "'minutes' doit être un nombre."}, status=400)

    try:
        etablissement = EtablissementSante.objects.get(id_etablissement=etablissement_id)
    except EtablissementSante.DoesNotExist:
        return JsonResponse({"error": "Établissement introuvable."}, status=404)

    cout_limite = minutes * 60 * (VITESSES_M_PAR_MIN[mode] / 60)  # = minutes * vitesse_m/min

    with connection.cursor() as cursor:
        noeud_depart = _plus_proche_noeud(cursor, etablissement.geom.x, etablissement.geom.y)

        if noeud_depart is None:
            return JsonResponse({"error": "Réseau routier vide."}, status=503)

        cursor.execute(
            """
            SELECT v.geom
            FROM pgr_drivingDistance(
                'SELECT id, source, target, cost FROM troncon_route_clean',
                %s, %s,
                directed => false
            ) AS dd
            JOIN troncon_route_vertices AS v ON v.id = dd.node
            """,
            [noeud_depart, cout_limite],
        )
        points = cursor.fetchall()

        if len(points) < 3:
            return JsonResponse(
                {"error": "Réseau routier insuffisant autour de cet établissement pour "
                          "calculer une zone (moins de 3 nœuds atteignables)."},
                status=404,
            )

        ids_str = ",".join(str(i) for i in range(len(points)))
        cursor.execute(
            """
            SELECT ST_AsGeoJSON(ST_ConvexHull(ST_Collect(v.geom)))
            FROM pgr_drivingDistance(
                'SELECT id, source, target, cost FROM troncon_route_clean',
                %s, %s,
                directed => false
            ) AS dd
            JOIN troncon_route_vertices AS v ON v.id = dd.node
            """,
            [noeud_depart, cout_limite],
        )
        geojson_str = cursor.fetchone()[0]

    return JsonResponse({
        "type": "Feature",
        "geometry": json.loads(geojson_str),
        "properties": {
            "etablissement_id": etablissement.id_etablissement,
            "nom": etablissement.nom,
            "mode": mode,
            "minutes": minutes,
            "reseau_reel": True,
        },
    })


def accueil(request):
    return render(request, "health/accueil.html")

def carte(request):
    return render(request, "health/carte.html")

def etablissements_page(request):
    return render(request, "health/etablissements.html")

def quartiers_page(request):
    return render(request, "health/quartiers.html")

def statistiques_page(request):
    return render(request, "health/statistiques.html")