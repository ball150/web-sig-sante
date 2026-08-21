from django.urls import path

from . import views

urlpatterns = [
    path("etablissements/", views.etablissements_geojson, name="api-etablissements"),
    path("quartiers/", views.quartiers_geojson, name="api-quartiers"),
    path("communes/", views.communes_geojson, name="api-communes"),
    path("etablissement-proche/", views.etablissement_proche, name="api-etablissement-proche"),
    path("zone-desserte/", views.zone_desserte, name="api-zone-desserte"),
    path("statistiques/", views.statistiques, name="api-statistiques"),
    path("accessibilite/", views.accessibilite, name="api-accessibilite"),
    path("types-etablissements/", views.types_etablissements_json, name="api-types"),
    path("secteurs/", views.secteurs_json, name="api-secteurs"),
    path("export/etablissements/", views.export_etablissements, name="api-export"),
    path("itineraire/etablissements/", views.itineraire_etablissements, name="api-itineraire-etablissements"),
    path("itineraire/", views.itineraire_depuis_position, name="api-itineraire-position"),
]