from django.urls import path
from . import views

urlpatterns = [
    path("", views.accueil, name="accueil"),
    path("carte/", views.carte, name="carte"),
    path("etablissements/", views.etablissements_page, name="etablissements"),
    path("quartiers/", views.quartiers_page, name="quartiers"),
    path("statistiques/", views.statistiques_page, name="statistiques"),
]