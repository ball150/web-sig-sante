// ==========================================
// GARDE : ce script ne doit tourner que sur la page carte
// ==========================================

(function () {

    const mapContainer = document.getElementById("map");

    if (!mapContainer) {
        // On n'est pas sur la page carte, on ne fait rien.
        return;
    }

    // ==========================================
    // INITIALISATION DE LA CARTE
    // ==========================================

    const map = L.map("map").setView([14.75, -17.42], 13);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap contributors",
        maxZoom: 19
    }).addTo(map);


    // ==========================================
    // COUCHES
    // ==========================================

    let etablissementsLayer = L.layerGroup().addTo(map);
    let quartiersLayer = L.layerGroup().addTo(map);
    let communesLayer = L.layerGroup().addTo(map);
    let zoneDesserteLayer = L.layerGroup().addTo(map);


    // ==========================================
    // SYMBOLOGIE PAR TYPE D'ÉTABLISSEMENT
    // ==========================================

    // Palette fixe : couleur attribuée de façon stable à chaque type
    // (même type = même couleur d'une session à l'autre, ordre alphabétique).
    const PALETTE = [
        "#e63946", "#2a9d8f", "#e9c46a", "#264653",
        "#9d4edd", "#f4a261", "#118ab2", "#ef476f",
        "#06d6a0", "#8338ec"
    ];

    // Association type -> couleur, remplie au fur et à mesure
    const couleurParType = {};
    let prochaineCouleurIndex = 0;

    function couleurPourType(type) {
        const cle = type || "Non renseigné";

        if (!couleurParType[cle]) {
            couleurParType[cle] = PALETTE[prochaineCouleurIndex % PALETTE.length];
            prochaineCouleurIndex++;
        }

        return couleurParType[cle];
    }

    // Petit glyphe indicatif selon des mots-clés courants dans le libellé du type
    function iconePourType(type) {
        const t = (type || "").toLowerCase();

        if (t.includes("hôpital") || t.includes("hopital")) return "🏥";
        if (t.includes("clinique")) return "⚕️";
        if (t.includes("pharmacie")) return "💊";
        if (t.includes("poste")) return "➕";
        if (t.includes("centre médico") || t.includes("medico")) return "🩺";
        if (t.includes("centre")) return "🏨";

        return "📍";
    }

    function creerIcone(type) {
        const couleur = couleurPourType(type);
        const glyphe = iconePourType(type);

        return L.divIcon({
            className: "marker-sante",
            html: `<span class="marker-pin" style="background:${couleur}">${glyphe}</span>`,
            iconSize: [30, 30],
            iconAnchor: [15, 28],
            popupAnchor: [0, -26]
        });
    }


    // ==========================================
    // LÉGENDE DYNAMIQUE
    // ==========================================

    function majLegende() {
        const legendeEl = document.getElementById("legend");

        if (!legendeEl) {
            return;
        }

        const types = Object.keys(couleurParType).sort();

        if (types.length === 0) {
            legendeEl.innerHTML = "<p class=\"hint\">Aucune donnée à afficher.</p>";
            return;
        }

        legendeEl.innerHTML = types.map(type => `
            <div class="legend-item">
                <span class="legend-dot" style="background:${couleurParType[type]}"></span>
                <span>${type}</span>
            </div>
        `).join("");
    }


    // ==========================================
    // CHARGER LES ÉTABLISSEMENTS
    // ==========================================

    function chargerEtablissements(params = "") {

        fetch(`/api/etablissements/${params}`)
            .then(response => {

                if (!response.ok) {
                    throw new Error("Erreur API : " + response.status);
                }

                return response.json();
            })

            .then(data => {

                // Supprimer les anciens marqueurs
                etablissementsLayer.clearLayers();

                data.features.forEach(feature => {

                    const coords = feature.geometry.coordinates;

                    const lon = coords[0];
                    const lat = coords[1];
                    const props = feature.properties;

                    const marker = L.marker([lat, lon], {
                        icon: creerIcone(props.type)
                    });

                    marker.bindPopup(`
                        <div class="popup-sante">

                            <h3>${props.nom}</h3>

                            <p>
                                <strong>Type :</strong>
                                ${props.type}
                            </p>

                            <p>
                                <strong>Adresse :</strong>
                                ${props.adresse || "Non renseignée"}
                            </p>

                            <p>
                                <strong>Quartier :</strong>
                                ${props.quartier}
                            </p>

                            <p>
                                <strong>Secteur :</strong>
                                ${props.secteur || "Non renseigné"}
                            </p>

                            <p>
                                <strong>Capacité :</strong>
                                ${props.capacite !== null && props.capacite !== undefined ? props.capacite : "Non renseignée"}
                            </p>

                            <button class="popup-btn" data-select-id="${props.id}" data-select-nom="${props.nom}">
                                Zone de desserte
                            </button>

                            <button class="popup-btn popup-btn-secondary" data-itineraire-id="${props.id}" data-itineraire-nom="${props.nom}">
                                📍 Itinéraire depuis ma position
                            </button>
                        </div>
                    `);

                    marker.on("popupopen", function (e) {
                        const btn = e.popup.getElement().querySelector("[data-select-id]");

                        if (btn) {
                            btn.addEventListener("click", function () {
                                selectionnerEtablissement(props.id, props.nom);
                            });
                        }

                        const btnItineraire = e.popup.getElement().querySelector("[data-itineraire-id]");

                        if (btnItineraire) {
                            btnItineraire.addEventListener("click", function () {
                                calculerItineraireDepuisMaPosition(props.id, props.nom);
                            });
                        }
                    });

                    marker.addTo(etablissementsLayer);
                });

                majLegende();
            })

            .catch(error => {
                console.error("Erreur :", error);
            });
    }


    // ==========================================
    // REMPLIR LE FILTRE TYPE
    // ==========================================

    function chargerTypes() {

        fetch("/api/types-etablissements/")
            .then(response => {
                if (!response.ok) throw new Error("endpoint indisponible");
                return response.json();
            })
            .then(data => {
                const selectType = document.getElementById("type");

                data.types.forEach(t => {
                    const option = document.createElement("option");
                    option.value = t.libelle_type;
                    option.textContent = t.libelle_type;
                    selectType.appendChild(option);
                });
            })
            .catch(() => {
                // Repli : si l'endpoint dédié n'existe pas encore côté backend,
                // on déduit les types depuis les établissements déjà chargés.
                fetch("/api/etablissements/")
                    .then(response => response.json())
                    .then(data => {
                        const selectType = document.getElementById("type");
                        const types = new Set();

                        data.features.forEach(f => {
                            if (f.properties.type) types.add(f.properties.type);
                        });

                        Array.from(types).sort().forEach(type => {
                            const option = document.createElement("option");
                            option.value = type;
                            option.textContent = type;
                            selectType.appendChild(option);
                        });
                    })
                    .catch(err => console.error("Erreur lors du chargement des types :", err));
            });
    }


    // ==========================================
    // REMPLIR LE FILTRE SECTEUR
    // ==========================================

    function chargerSecteurs() {

        fetch("/api/secteurs/")
            .then(response => response.json())
            .then(data => {

                const selectSecteur = document.getElementById("secteur");
                const hint = document.getElementById("secteur-hint");

                if (!data.secteurs || data.secteurs.length === 0) {
                    // Donnée non disponible pour l'instant (cf docs/API.md)
                    selectSecteur.disabled = true;

                    if (hint) hint.style.display = "block";

                    return;
                }

                if (hint) hint.style.display = "none";

                data.secteurs.forEach(s => {
                    const option = document.createElement("option");
                    option.value = s.libelle;
                    option.textContent = s.libelle;
                    selectSecteur.appendChild(option);
                });
            })
            .catch(error => console.error("Erreur secteurs :", error));
    }


    // ==========================================
    // RECHERCHE + FILTRES
    // ==========================================

    function lancerRecherche() {

        const search = document.getElementById("search").value.trim();
        const type = document.getElementById("type").value;
        const secteurSelect = document.getElementById("secteur");
        const secteur = secteurSelect && !secteurSelect.disabled ? secteurSelect.value : "";

        const params = new URLSearchParams();

        if (search) params.append("search", search);
        if (type) params.append("type", type);
        if (secteur) params.append("secteur", secteur);

        const query = params.toString();

        chargerEtablissements(query ? `?${query}` : "");
    }

    document.getElementById("btn-search").addEventListener("click", lancerRecherche);

    document.getElementById("btn-reset").addEventListener("click", function () {
        document.getElementById("search").value = "";
        document.getElementById("type").value = "";

        const secteurSelect = document.getElementById("secteur");
        if (secteurSelect) secteurSelect.value = "";

        chargerEtablissements();
    });

    document.getElementById("search").addEventListener("keydown", function (event) {
        if (event.key === "Enter") {
            lancerRecherche();
        }
    });


    // ==========================================
    // COUCHES : CASES À COCHER
    // ==========================================

    document.getElementById("layer-etablissements").addEventListener("change", function () {
        if (this.checked) map.addLayer(etablissementsLayer);
        else map.removeLayer(etablissementsLayer);
    });

    document.getElementById("layer-quartiers").addEventListener("change", function () {
        if (this.checked) map.addLayer(quartiersLayer);
        else map.removeLayer(quartiersLayer);
    });

    document.getElementById("layer-communes").addEventListener("change", function () {
        if (this.checked) map.addLayer(communesLayer);
        else map.removeLayer(communesLayer);
    });


    // ==========================================
    // CHARGER LES QUARTIERS (choroplèthe simple selon nb d'établissements)
    // ==========================================

    function couleurChoroplethe(nb) {
        if (nb >= 10) return "#08306b";
        if (nb >= 6) return "#2171b5";
        if (nb >= 3) return "#6baed6";
        if (nb >= 1) return "#c6dbef";
        return "#f7fbff";
    }

    function chargerQuartiers() {

        fetch("/api/quartiers/")
            .then(response => response.json())
            .then(data => {

                data.features.forEach(feature => {

                    const layer = L.geoJSON(feature, {

                        style: {
                            color: "#3388ff",
                            weight: 1,
                            fillColor: couleurChoroplethe(feature.properties.nb_etablissements),
                            fillOpacity: 0.35
                        },

                        onEachFeature: function (feature, layer) {

                            layer.bindPopup(`
                                <strong>Quartier :</strong>
                                ${feature.properties.nom}
                                <br>
                                <strong>Établissements :</strong>
                                ${feature.properties.nb_etablissements}
                            `);

                        }

                    });

                    layer.addTo(quartiersLayer);

                });

            })

            .catch(error => {
                console.error("Erreur quartiers :", error);
            });
    }


    // ==========================================
    // CHARGER LES COMMUNES
    // ==========================================

    // Palette dédiée aux limites de communes (distincte de celle des types
    // d'établissement, pour ne pas créer de confusion visuelle)
    const PALETTE_COMMUNES = ["#e67e22", "#8338ec", "#118ab2", "#e63946", "#06d6a0", "#f4a261"];

    function chargerCommunes() {

        fetch("/api/communes/")
            .then(response => response.json())
            .then(data => {

                data.features.forEach((feature, index) => {

                    const couleur = PALETTE_COMMUNES[index % PALETTE_COMMUNES.length];

                    const layer = L.geoJSON(feature, {

                        style: {
                            color: couleur,
                            weight: 3,
                            fillColor: couleur,
                            fillOpacity: 0.04,
                            dashArray: "8 4"
                        },

                        onEachFeature: function (feature, layer) {

                            layer.bindPopup(`
                                <strong>Commune :</strong>
                                ${feature.properties.nom}
                            `);

                        }

                    });

                    layer.addTo(communesLayer);

                });

                // On centre/zoome automatiquement la carte pour que toutes les
                // communes soient visibles dès le chargement (sinon la vue
                // par défaut, centrée sur un seul quartier, peut en cacher
                // certaines complètement).
                if (data.features.length > 0) {
                    const bounds = communesLayer.getBounds();
                    if (bounds.isValid()) {
                        map.fitBounds(bounds, { padding: [20, 20] });
                    }
                }

            })

            .catch(error => {
                console.error("Erreur communes :", error);
            });
    }


    // ==========================================
    // ZONE DE DESSERTE (bonus) — par mode de déplacement + durée
    // ==========================================

    let etablissementSelectionne = null; // { id, nom }
    let modeActuel = "pied";
    let vitesseActuelle = 83.3; // mètres / minute (≈ 5 km/h)

    function selectionnerEtablissement(id, nom) {
        etablissementSelectionne = { id, nom };

        const panel = document.getElementById("zone-desserte-panel");
        const label = document.getElementById("zone-desserte-label");

        panel.classList.remove("disabled");
        label.textContent = `Établissement sélectionné : ${nom}`;
    }

    document.querySelectorAll(".mode-btn").forEach(function (btn) {
        btn.addEventListener("click", function () {

            document.querySelectorAll(".mode-btn").forEach(b => b.classList.remove("active"));
            this.classList.add("active");

            modeActuel = this.dataset.mode;
            vitesseActuelle = parseFloat(this.dataset.vitesse);
        });
    });

    document.querySelectorAll(".radius-btn").forEach(function (btn) {
        btn.addEventListener("click", function () {

            if (!etablissementSelectionne) {
                return;
            }

            const minutes = parseFloat(this.dataset.minutes);
            const icone = modeActuel === "pied" ? "🚶" : "🚗";

            document.getElementById("zone-desserte-label").textContent =
                `${icone} ${etablissementSelectionne.nom} — calcul en cours...`;

            // On tente d'abord le VRAI réseau routier (pgRouting).
            // S'il n'est pas configuré côté base de données (503) ou si le
            // calcul échoue pour cet établissement (404 : pas assez de rues
            // atteignables), on se replie sur le cercle à vol d'oiseau.
            fetch(`/api/zone-desserte-reseau/?id=${etablissementSelectionne.id}&minutes=${minutes}&mode=${modeActuel}`)
                .then(response => {
                    if (!response.ok) {
                        throw { repli: true, status: response.status };
                    }
                    return response.json();
                })
                .then(data => {
                    afficherZoneDesserte(data, true, icone, minutes);
                })
                .catch(() => {

                    // Repli : cercle géométrique approximatif
                    const rayon = Math.round(vitesseActuelle * minutes);

                    fetch(`/api/zone-desserte/?id=${etablissementSelectionne.id}&rayon=${rayon}`)
                        .then(response => {
                            if (!response.ok) throw new Error("Erreur zone de desserte");
                            return response.json();
                        })
                        .then(data => {
                            afficherZoneDesserte(data, false, icone, minutes, rayon);
                        })
                        .catch(error => console.error("Erreur zone de desserte :", error));
                });
        });
    });

    function afficherZoneDesserte(data, reseauReel, icone, minutes, rayon) {

        zoneDesserteLayer.clearLayers();

        L.geoJSON(data, {
            style: reseauReel ? {
                color: "#087f5b",
                weight: 2,
                fillColor: "#087f5b",
                fillOpacity: 0.18
            } : {
                color: "#087f5b",
                weight: 2,
                fillColor: "#087f5b",
                fillOpacity: 0.15,
                dashArray: "6 4"
            }
        }).addTo(zoneDesserteLayer);

        const suffixe = reseauReel
            ? " (réseau routier réel)"
            : ` ≈ ${(rayon / 1000).toFixed(1)} km à vol d'oiseau`;

        document.getElementById("zone-desserte-label").textContent =
            `${icone} ${etablissementSelectionne.nom} — ${minutes} min${suffixe}`;
    }

    document.getElementById("btn-clear-zone").addEventListener("click", function () {
        zoneDesserteLayer.clearLayers();
        etablissementSelectionne = null;

        document.getElementById("zone-desserte-panel").classList.add("disabled");
        document.getElementById("zone-desserte-label").textContent = "Aucun établissement sélectionné";
    });


    // ==========================================
    // ITINÉRAIRE RÉEL depuis ma position
    // ==========================================

    let itineraireLayer = L.layerGroup().addTo(map);

    function calculerItineraireDepuisMaPosition(etablissementId, etablissementNom) {

        if (!navigator.geolocation) {
            alert("La géolocalisation n'est pas disponible sur ce navigateur.");
            return;
        }

        navigator.geolocation.getCurrentPosition(
            function (position) {

                const lat = position.coords.latitude;
                const lon = position.coords.longitude;

                fetch(`/api/itineraire/?lat=${lat}&lon=${lon}&id=${etablissementId}`)
                    .then(response => {
                        if (!response.ok) {
                            return response.json().then(err => { throw new Error(err.error || "Erreur itinéraire"); });
                        }
                        return response.json();
                    })
                    .then(data => {

                        itineraireLayer.clearLayers();

                        L.geoJSON(data, {
                            style: { color: "#e63946", weight: 4, opacity: 0.85 }
                        }).addTo(itineraireLayer);

                        map.fitBounds(L.geoJSON(data).getBounds(), { padding: [40, 40] });

                        const distanceKm = (data.properties.distance_m / 1000).toFixed(2);
                        alert(`Itinéraire vers ${etablissementNom} : ${distanceKm} km (réseau routier réel).`);
                    })
                    .catch(error => {
                        alert("Itinéraire indisponible : " + error.message);
                    });
            },
            function () {
                alert("Impossible d'obtenir votre position. Autorisez la géolocalisation et réessayez.");
            }
        );
    }


    // ==========================================
    // LANCEMENT
    // ==========================================

    chargerEtablissements();
    chargerTypes();
    chargerSecteurs();
    chargerQuartiers();
    chargerCommunes();

})();
