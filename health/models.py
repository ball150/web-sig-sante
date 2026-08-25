from django.db import models


class TypeEtablissement(models.Model):
    id_type = models.AutoField(primary_key=True)
    libelle_type = models.CharField(max_length=50)

    class Meta:
        db_table = "type_etablissement"

    def __str__(self):
        return self.libelle_type


class Secteur(models.Model):
    id_secteur = models.AutoField(primary_key=True)
    libelle = models.CharField(max_length=100)

    class Meta:
        db_table = "secteur"

    def __str__(self):
        return self.libelle

from django.contrib.gis.db import models as gis_models


class Commune(models.Model):
    id_commune = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=100)
    geom = gis_models.MultiPolygonField(srid=4326)

    class Meta:
        db_table = "commune"

    def __str__(self):
        return self.nom


class Quartier(models.Model):
    id_quartier = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=100)
    geom = gis_models.MultiPolygonField(srid=4326)
    id_commune = models.ForeignKey(
        Commune,
        on_delete=models.CASCADE,
        db_column="id_commune",
        related_name="quartiers",
    )

    class Meta:
        db_table = "quartier"

    def __str__(self):
        return self.nom
class EtablissementSante(models.Model):
    id_etablissement = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=150)
    adresse = models.CharField(max_length=150, blank=True, null=True)
    capacite = models.IntegerField(blank=True, null=True)
    geom = gis_models.PointField(srid=4326)

    id_type = models.ForeignKey(
        TypeEtablissement,
        on_delete=models.PROTECT,
        db_column="id_type",
        related_name="etablissements",
    )
    id_quartier = models.ForeignKey(
        Quartier,
        on_delete=models.PROTECT,
        db_column="id_quartier",
        related_name="etablissements",
    )
    id_secteur = models.ForeignKey(
        Secteur,
        on_delete=models.PROTECT,
        db_column="id_secteur",
        related_name="etablissements",
        blank=True,
        null=True,
    )

    class Meta:
        db_table = "etablissement_sante"

    def __str__(self):
        return self.nom
class Population(models.Model):
    id_population = models.AutoField(primary_key=True)
    effectif = models.IntegerField()
    pop_masculine = models.IntegerField()
    pop_feminine = models.IntegerField()
    id_quartier = models.ForeignKey(
        Quartier,
        on_delete=models.CASCADE,
        db_column="id_quartier",
        related_name="populations",
    )

    class Meta:
        db_table = "population"

    def __str__(self):
        return f"{self.id_quartier.nom} — {self.effectif} hab."
