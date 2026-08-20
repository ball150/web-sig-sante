from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

from .models import (
    TypeEtablissement,
    Secteur,
    Commune,
    Quartier,
    EtablissementSante,
    Population,
)


@admin.register(TypeEtablissement)
class TypeEtablissementAdmin(admin.ModelAdmin):
    list_display = ("id_type", "libelle_type")
    search_fields = ("libelle_type",)


@admin.register(Secteur)
class SecteurAdmin(admin.ModelAdmin):
    list_display = ("id_secteur", "libelle")
    search_fields = ("libelle",)


@admin.register(Commune)
class CommuneAdmin(GISModelAdmin):
    list_display = ("id_commune", "nom")
    search_fields = ("nom",)


@admin.register(Quartier)
class QuartierAdmin(GISModelAdmin):
    list_display = ("id_quartier", "nom", "id_commune")
    list_filter = ("id_commune",)
    search_fields = ("nom",)


@admin.register(EtablissementSante)
class EtablissementSanteAdmin(GISModelAdmin):
    list_display = ("id_etablissement", "nom", "id_type", "id_quartier", "id_secteur", "capacite")
    list_filter = ("id_type", "id_secteur", "id_quartier")
    search_fields = ("nom", "adresse")


@admin.register(Population)
class PopulationAdmin(admin.ModelAdmin):
    list_display = ("id_population", "id_quartier", "effectif", "pop_masculine", "pop_feminine")
    list_filter = ("id_quartier",)