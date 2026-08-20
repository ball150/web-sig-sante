from pathlib import Path

from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import GEOSGeometry
from django.core.management.base import BaseCommand

from health.models import Commune, Quartier

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

COMMUNE_SHP = DATA_DIR / "limite_parcelle_commune.shp"
QUARTIER_SHP = DATA_DIR / "limite_parcelle_assainies.shp"

SOURCE_SRID = 32628  # vrai SRID des coordonnées, le .prj de ces fichiers étant erroné


def read_features_as_4326(shp_path):
    """Lit un shapefile et renvoie une liste de (feature, geom) avec geom forcée
    depuis SOURCE_SRID puis reprojetée en 4326, en ignorant le .prj du fichier."""
    ds = DataSource(str(shp_path))
    layer = ds[0]
    results = []
    for feature in layer:
        geom = GEOSGeometry(feature.geom.wkt, srid=SOURCE_SRID)
        geom.transform(4326)
        results.append((feature, geom))
    return results


class Command(BaseCommand):
    help = "Importe Commune et Quartier en forçant le vrai SRID source (32628)"

    def handle(self, *args, **options):
        from django.contrib.gis.geos import MultiPolygon, Polygon

        self.stdout.write("Import de la commune...")
        for feature, geom in read_features_as_4326(COMMUNE_SHP):
            if isinstance(geom, Polygon):
                geom = MultiPolygon(geom)
            Commune.objects.create(nom=feature.get("NAME_3"), geom=geom)
        self.stdout.write(self.style.SUCCESS(f"{Commune.objects.count()} commune(s) importée(s)."))

        commune = Commune.objects.get(nom="Parcelles Assainies")

        self.stdout.write("Import des quartiers...")
        for feature, geom in read_features_as_4326(QUARTIER_SHP):
            if isinstance(geom, Polygon):
                geom = MultiPolygon(geom)
            Quartier.objects.create(nom=feature.get("NAME_4"), geom=geom, id_commune=commune)
        self.stdout.write(self.style.SUCCESS(f"{Quartier.objects.count()} quartier(s) importé(s)."))