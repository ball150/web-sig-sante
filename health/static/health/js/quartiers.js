(function () {

    const tbody = document.getElementById("quartiers-table-body");

    if (!tbody) {
        return;
    }

    fetch("/api/accessibilite/")
        .then(response => response.json())
        .then(data => {

            const banner = document.getElementById("avertissement-banner");
            if (banner && data.avertissement) {
                banner.textContent = "⚠️ " + data.avertissement;
            }

            if (!data.quartiers || data.quartiers.length === 0) {
                tbody.innerHTML = `<tr><td colspan="4" class="loading-row">Aucune donnée de quartier disponible.</td></tr>`;
                return;
            }

            tbody.innerHTML = data.quartiers.map(q => `
                <tr>
                    <td>${q.quartier}</td>
                    <td>${q.nb_etablissements}</td>
                    <td>${q.population !== null && q.population !== undefined ? q.population.toLocaleString("fr-FR") : "Donnée population manquante"}</td>
                    <td>${q.habitants_par_etablissement !== null && q.habitants_par_etablissement !== undefined ? q.habitants_par_etablissement.toLocaleString("fr-FR") : "Donnée population manquante"}</td>
                </tr>
            `).join("");
        })
        .catch(error => {
            console.error("Erreur accessibilité :", error);
            tbody.innerHTML = `<tr><td colspan="4" class="loading-row">Erreur lors du chargement des données.</td></tr>`;
        });

})();
