from django.contrib.gis.geos import Point, MultiPolygon, Polygon
from django.test import TestCase
from django.urls import reverse

from .models import Commune, Quartier, TypeEtablissement, EtablissementSante


class ModelsTestCase(TestCase):
    """Vérifie que les modèles et leurs relations fonctionnent correctement."""

    def setUp(self):
        # Un petit carré comme géométrie de test, pas besoin des vraies formes complexes
        polygon = Polygon(((0, 0), (0, 1), (1, 1), (1, 0), (0, 0)), srid=4326)
        self.commune = Commune.objects.create(nom="Commune Test", geom=MultiPolygon(polygon))
        self.quartier = Quartier.objects.create(
            nom="Quartier Test", geom=MultiPolygon(polygon), id_commune=self.commune
        )
        self.type_poste = TypeEtablissement.objects.create(libelle_type="Poste de santé")

    def test_creation_etablissement(self):
        """Un établissement doit pouvoir être créé avec toutes ses relations."""
        etab = EtablissementSante.objects.create(
            nom="Poste Test",
            geom=Point(0.5, 0.5, srid=4326),
            id_type=self.type_poste,
            id_quartier=self.quartier,
        )
        self.assertEqual(etab.id_quartier.nom, "Quartier Test")
        self.assertEqual(etab.id_type.libelle_type, "Poste de santé")

    def test_related_name_quartier_vers_etablissements(self):
        """Le related_name 'etablissements' doit permettre de lister les établissements d'un quartier."""
        EtablissementSante.objects.create(
            nom="Poste A", geom=Point(0.5, 0.5, srid=4326),
            id_type=self.type_poste, id_quartier=self.quartier,
        )
        EtablissementSante.objects.create(
            nom="Poste B", geom=Point(0.2, 0.2, srid=4326),
            id_type=self.type_poste, id_quartier=self.quartier,
        )
        self.assertEqual(self.quartier.etablissements.count(), 2)

    def test_suppression_quartier_protegee(self):
        """id_quartier utilise PROTECT : supprimer un quartier avec des établissements doit échouer."""
        EtablissementSante.objects.create(
            nom="Poste A", geom=Point(0.5, 0.5, srid=4326),
            id_type=self.type_poste, id_quartier=self.quartier,
        )
        from django.db.models.deletion import ProtectedError
        with self.assertRaises(ProtectedError):
            self.quartier.delete()


class ApiEtablissementsTestCase(TestCase):
    """Vérifie l'endpoint /api/etablissements/ et ses filtres."""

    def setUp(self):
        polygon = Polygon(((0, 0), (0, 1), (1, 1), (1, 0), (0, 0)), srid=4326)
        commune = Commune.objects.create(nom="Commune Test", geom=MultiPolygon(polygon))
        self.quartier = Quartier.objects.create(
            nom="Camberene", geom=MultiPolygon(polygon), id_commune=commune
        )
        self.type_hopital = TypeEtablissement.objects.create(libelle_type="Hôpital")
        self.type_poste = TypeEtablissement.objects.create(libelle_type="Poste de santé")

        EtablissementSante.objects.create(
            nom="Hopital Central", geom=Point(0.5, 0.5, srid=4326),
            id_type=self.type_hopital, id_quartier=self.quartier,
        )
        EtablissementSante.objects.create(
            nom="Poste Nord", geom=Point(0.1, 0.1, srid=4326),
            id_type=self.type_poste, id_quartier=self.quartier,
        )

    def test_liste_sans_filtre(self):
        """Sans filtre, l'API doit retourner tous les établissements."""
        response = self.client.get("/api/etablissements/")
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data["features"]), 2)

    def test_filtre_par_type(self):
        """?type=Hôpital ne doit retourner que l'établissement de ce type."""
        response = self.client.get("/api/etablissements/?type=Hôpital")
        data = response.json()
        self.assertEqual(len(data["features"]), 1)
        self.assertEqual(data["features"][0]["properties"]["nom"], "Hopital Central")

    def test_filtre_sans_resultat_renvoie_liste_vide(self):
        """Un filtre qui ne matche rien doit renvoyer une liste vide, pas une erreur."""
        response = self.client.get("/api/etablissements/?type=Clinique")
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["features"], [])
    def test_sans_page_comportement_inchange(self):
        """Sans le paramètre 'page', la réponse doit rester identique à avant (rétrocompatibilité)."""
        response = self.client.get("/api/etablissements/")
        data = response.json()
        self.assertNotIn("pagination", data)
        self.assertEqual(len(data["features"]), 2)

    def test_avec_pagination(self):
        """Avec page_size=1, chaque page ne doit contenir qu'un seul établissement."""
        response = self.client.get("/api/etablissements/?page=1&page_size=1")
        data = response.json()
        self.assertEqual(len(data["features"]), 1)
        self.assertEqual(data["pagination"]["total_resultats"], 2)
        self.assertTrue(data["pagination"]["page_suivante"])


class ApiEtablissementProcheTestCase(TestCase):
    """Vérifie le calcul de distance de l'endpoint établissement le plus proche."""

    def setUp(self):
        polygon = Polygon(((0, 0), (0, 1), (1, 1), (1, 0), (0, 0)), srid=4326)
        commune = Commune.objects.create(nom="Commune Test", geom=MultiPolygon(polygon))
        quartier = Quartier.objects.create(nom="Camberene", geom=MultiPolygon(polygon), id_commune=commune)
        type_poste = TypeEtablissement.objects.create(libelle_type="Poste de santé")

        # Deux établissements réels de notre jeu de données, positions connues
        self.proche = EtablissementSante.objects.create(
            nom="PS CAMBERENE", geom=Point(-17.419660175, 14.769881555, srid=4326),
            id_type=type_poste, id_quartier=quartier,
        )
        self.loin = EtablissementSante.objects.create(
            nom="PS UNITE 9", geom=Point(-17.434863627, 14.763382473, srid=4326),
            id_type=type_poste, id_quartier=quartier,
        )

    def test_etablissement_le_plus_proche_est_bien_le_plus_proche(self):
        """Depuis un point très proche de PS CAMBERENE, c'est bien lui qui doit être retourné en premier."""
        response = self.client.get(
            "/api/etablissement-proche/?lat=14.7699&lon=-17.4197"
        )
        data = response.json()
        self.assertEqual(data["features"][0]["properties"]["nom"], "PS CAMBERENE")
        self.assertLess(data["features"][0]["properties"]["distance_m"], 500)

    def test_parametres_manquants_renvoie_erreur_400(self):
        """Sans lat/lon, l'API doit renvoyer une erreur claire, pas planter."""
        response = self.client.get("/api/etablissement-proche/")
        self.assertEqual(response.status_code, 400)

    def test_parametres_non_numeriques_renvoie_erreur_400(self):
        """lat='abc' doit être détecté et renvoyer 400, pas un crash serveur 500."""
        response = self.client.get("/api/etablissement-proche/?lat=abc&lon=-17.44")
        self.assertEqual(response.status_code, 400)
    def test_quartiers_nb_etablissements_correct(self):
        """Le comptage via annotate doit donner le même résultat qu'un comptage manuel."""
        response = self.client.get("/api/quartiers/")
        data = response.json()
        feature = data["features"][0]
        self.assertEqual(feature["properties"]["nom"], "Camberene")
        self.assertEqual(feature["properties"]["nb_etablissements"], 2)