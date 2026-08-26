import csv
from pathlib import Path

from django.contrib.gis.geos import GEOSGeometry
from django.core.management.base import BaseCommand

from health.models import TypeEtablissement, EtablissementSante, Quartier

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
CSV_PATH = DATA_DIR / "donnees_exporter.csv"

# Mapping explicite : valeur du CSV -> nom exact du Quartier en base
QUARTIER_MAP = {
    "CAMBERENE": "Camberene",
    "GRAND YOFF": "Grand Yoff",
    "PARCELLES ASSAINIES": "Parcelles Assainies",
    "PATTE D OIE": "Patte D'Oie",
}


class Command(BaseCommand):
    help = "Importe TypeEtablissement et EtablissementSante depuis le CSV"

    def handle(self, *args, **options):
        with open(CSV_PATH, encoding="utf-8") as f:
            rows = list(csv.reader(f))

        # --- 1. TypeEtablissement : valeurs distinctes de la colonne type_etab ---
        types_distincts = sorted({row[2] for row in rows})
        for libelle in types_distincts:
            TypeEtablissement.objects.get_or_create(libelle_type=libelle)
        self.stdout.write(self.style.SUCCESS(
            f"{TypeEtablissement.objects.count()} type(s) d'établissement importé(s)."
        ))

        # --- 2. EtablissementSante ---
        erreurs = []
        for row in rows:
            geom_hex, type_etab, descriptif, nom = row[1], row[2], row[3], row[4]
            quartier_csv = row[8]

            quartier_nom = QUARTIER_MAP.get(quartier_csv)
            if quartier_nom is None:
                erreurs.append(f"Quartier inconnu dans le mapping : '{quartier_csv}' (établissement '{nom}')")
                continue

            try:
                quartier = Quartier.objects.get(nom=quartier_nom)
            except Quartier.DoesNotExist:
                erreurs.append(f"Quartier absent en base : '{quartier_nom}' (établissement '{nom}')")
                continue

            type_obj = TypeEtablissement.objects.get(libelle_type=type_etab)
            geom = GEOSGeometry(geom_hex)

            EtablissementSante.objects.create(
                nom=nom,
                adresse=descriptif,
                capacite=None,
                geom=geom,
                id_type=type_obj,
                id_quartier=quartier,
                id_secteur=None,
            )

        self.stdout.write(self.style.SUCCESS(
            f"{EtablissementSante.objects.count()} établissement(s) importé(s)."
        ))
        if erreurs:
            self.stdout.write(self.style.WARNING(f"{len(erreurs)} ligne(s) ignorée(s) :"))
            for e in erreurs:
                self.stdout.write(f"  - {e}")