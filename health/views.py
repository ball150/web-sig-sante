import json

from django.http import JsonResponse

from .models import EtablissementSante


from django.db.models import Q


from django.core.paginator import Paginator


def etablissements_geojson(request):
    etablissements = EtablissementSante.objects.select_related(
        "id_type", "id_quartier", "id_secteur"
    )

    type_param = request.GET.get("type")
    quartier_param = request.GET.get("quartier")
    secteur_param = request.GET.get("secteur")
    search_param = request.GET.get("search")
    page_param = request.GET.get("page")
    page_size_param = request.GET.get("page_size", 20)

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

    pagination_info = None
    if page_param:
        try:
            page_size = int(page_size_param)
        except ValueError:
            page_size = 20

        paginator = Paginator(etablissements, page_size)
        try:
            page_number = int(page_param)
        except ValueError:
            page_number = 1

        page_obj = paginator.get_page(page_number)
        etablissements = page_obj.object_list

        pagination_info = {
            "page": page_obj.number,
            "page_size": page_size,
            "total_pages": paginator.num_pages,
            "total_resultats": paginator.count,
            "page_suivante": page_obj.has_next(),
            "page_precedente": page_obj.has_previous(),
        }

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

    response_data = {"type": "FeatureCollection", "features": features}
    if pagination_info:
        response_data["pagination"] = pagination_info

    return JsonResponse(response_data)

from .models import EtablissementSante, Quartier, Commune


from django.db.models import Count


def quartiers_geojson(request):
    quartiers = (
        Quartier.objects
        .select_related("id_commune")
        .annotate(nb_etablissements=Count("etablissements"))
    )

    features = []
    for q in quartiers:
        features.append({
            "type": "Feature",
            "geometry": json.loads(q.geom.geojson),
            "properties": {
                "id": q.id_quartier,
                "nom": q.nom,
                "commune": q.id_commune.nom,
                "nb_etablissements": q.nb_etablissements,
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

RAYONS_AUTORISES = [500, 1000, 2000]


def zone_desserte(request):
    etablissement_id = request.GET.get("id")
    rayon = request.GET.get("rayon")

    if not etablissement_id:
        return JsonResponse({"error": "Paramètre 'id' requis."}, status=400)

    try:
        rayon = int(rayon)
    except (TypeError, ValueError):
        return JsonResponse({"error": "Paramètre 'rayon' requis (entier, en mètres)."}, status=400)

    if rayon not in RAYONS_AUTORISES:
        return JsonResponse(
            {"error": f"Rayon non autorisé. Valeurs possibles : {RAYONS_AUTORISES}."},
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
from .models import TypeEtablissement, Secteur


def types_etablissements_json(request):
    data = list(TypeEtablissement.objects.values("id_type", "libelle_type"))
    return JsonResponse({"types": data})


def secteurs_json(request):
    data = list(Secteur.objects.values("id_secteur", "libelle"))
    return JsonResponse({"secteurs": data})


def export_etablissements(request):
    response = etablissements_geojson(request)
    response["Content-Disposition"] = 'attachment; filename="etablissements_export.geojson"'
    return response