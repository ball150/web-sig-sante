from django.urls import path

from . import views

urlpatterns = [
    path("etablissements/", views.etablissements_geojson, name="api-etablissements"),
    path("quartiers/", views.quartiers_geojson, name="api-quartiers"),
    path("communes/", views.communes_geojson, name="api-communes"),
    path("types-etablissements/", views.types_etablissements, name="api-types-etablissements"),
    path("secteurs/", views.secteurs, name="api-secteurs"),
    path("etablissement-proche/", views.etablissement_proche, name="api-etablissement-proche"),
    path("zone-desserte/", views.zone_desserte, name="api-zone-desserte"),
    path("statistiques/", views.statistiques, name="api-statistiques"),
    path("accessibilite/", views.accessibilite, name="api-accessibilite"),
    path("export/etablissements/", views.export_etablissements, name="api-export-etablissements"),
    path("itineraire/etablissements/", views.itineraire_etablissements, name="api-itineraire-etablissements"),
    path("itineraire/", views.itineraire_point, name="api-itineraire-point"),
    path("zone-desserte-reseau/", views.zone_desserte_reseau, name="api-zone-desserte-reseau"),
]
