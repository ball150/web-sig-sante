(function () {

    const cardsContainer = document.getElementById("stats-cards");

    if (!cardsContainer) {
        return;
    }

    const PALETTE = [
        "#087f5b", "#e63946", "#e9c46a", "#264653",
        "#9d4edd", "#f4a261", "#118ab2", "#ef476f",
        "#06d6a0", "#8338ec"
    ];

    // Options communes : on force la taille définie par le conteneur CSS
    // plutôt que de laisser Chart.js grandir librement.
    const BASE_OPTIONS = {
        responsive: true,
        maintainAspectRatio: false
    };

    fetch("/api/statistiques/")
        .then(response => response.json())
        .then(data => {

            const population = data.population;

            const cartes = [
                { label: "Établissements", valeur: data.total_etablissements },
                { label: "Types d'établissement", valeur: data.par_type.length },
                { label: "Quartiers couverts", valeur: data.par_quartier.length },
                {
                    label: "Population totale",
                    valeur: population.disponible ? population.totale.toLocaleString("fr-FR") : "Non disponible"
                }
            ];

            cardsContainer.innerHTML = cartes.map(c => `
                <div class="stat-card">
                    <div class="stat-value">${c.valeur}</div>
                    <div class="stat-label">${c.label}</div>
                </div>
            `).join("");

            // ---- Graphique par type (barres) ----
            new Chart(document.getElementById("chart-type"), {
                type: "bar",
                data: {
                    labels: data.par_type.map(r => r.type),
                    datasets: [{
                        label: "Nombre d'établissements",
                        data: data.par_type.map(r => r.total),
                        backgroundColor: data.par_type.map((_, i) => PALETTE[i % PALETTE.length])
                    }]
                },
                options: {
                    ...BASE_OPTIONS,
                    plugins: { legend: { display: false } },
                    scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
                }
            });

            // ---- Graphique par secteur (camembert) ----
            new Chart(document.getElementById("chart-secteur"), {
                type: "pie",
                data: {
                    labels: data.par_secteur.map(r => r.secteur),
                    datasets: [{
                        data: data.par_secteur.map(r => r.total),
                        backgroundColor: data.par_secteur.map((_, i) => PALETTE[i % PALETTE.length])
                    }]
                },
                options: {
                    ...BASE_OPTIONS,
                    plugins: { legend: { position: "bottom" } }
                }
            });

            // ---- Graphique population Hommes / Femmes (doughnut) ----
            const wrapPopulation = document.getElementById("wrap-population");
            const hintPopulation = document.getElementById("population-hint");

            if (population.disponible && population.masculine !== null && population.feminine !== null) {

                hintPopulation.style.display = "none";

                new Chart(document.getElementById("chart-population"), {
                    type: "doughnut",
                    data: {
                        labels: ["Hommes", "Femmes"],
                        datasets: [{
                            data: [population.masculine, population.feminine],
                            backgroundColor: ["#118ab2", "#ef476f"]
                        }]
                    },
                    options: {
                        ...BASE_OPTIONS,
                        plugins: { legend: { position: "bottom" } }
                    }
                });

            } else {
                wrapPopulation.style.display = "none";
                hintPopulation.style.display = "block";
            }

            // ---- Graphique par quartier (barres horizontales) ----
            new Chart(document.getElementById("chart-quartier"), {
                type: "bar",
                data: {
                    labels: data.par_quartier.map(r => r.quartier),
                    datasets: [{
                        label: "Nombre d'établissements",
                        data: data.par_quartier.map(r => r.total),
                        backgroundColor: "#087f5b"
                    }]
                },
                options: {
                    ...BASE_OPTIONS,
                    indexAxis: "y",
                    plugins: { legend: { display: false } },
                    scales: { x: { beginAtZero: true, ticks: { precision: 0 } } }
                }
            });

        })
        .catch(error => {
            console.error("Erreur statistiques :", error);
            cardsContainer.innerHTML = `<p class="loading-row">Erreur lors du chargement des statistiques.</p>`;
        });


    // ---- Graphique accessibilité (habitants par établissement, par quartier) ----

    fetch("/api/accessibilite/")
        .then(response => response.json())
        .then(data => {

            const hint = document.getElementById("accessibilite-hint");

            if (data.avertissement && hint) {
                hint.textContent = "⚠️ " + data.avertissement;
            }

            const quartiersAvecPopulation = (data.quartiers || []).filter(
                q => q.habitants_par_etablissement !== null && q.habitants_par_etablissement !== undefined
            );

            if (quartiersAvecPopulation.length === 0) {
                document.getElementById("chart-accessibilite").parentElement.style.display = "none";
                if (hint) hint.textContent = "Donnée population non disponible pour calculer cet indicateur.";
                return;
            }

            // Tri décroissant : quartiers les moins bien desservis en premier
            quartiersAvecPopulation.sort((a, b) => b.habitants_par_etablissement - a.habitants_par_etablissement);

            new Chart(document.getElementById("chart-accessibilite"), {
                type: "bar",
                data: {
                    labels: quartiersAvecPopulation.map(q => q.quartier),
                    datasets: [{
                        label: "Habitants par établissement",
                        data: quartiersAvecPopulation.map(q => q.habitants_par_etablissement),
                        backgroundColor: "#e63946"
                    }]
                },
                options: {
                    ...BASE_OPTIONS,
                    indexAxis: "y",
                    plugins: { legend: { display: false } },
                    scales: { x: { beginAtZero: true, ticks: { precision: 0 } } }
                }
            });
        })
        .catch(error => {
            console.error("Erreur accessibilité :", error);
        });

})();
