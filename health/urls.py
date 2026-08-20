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
]