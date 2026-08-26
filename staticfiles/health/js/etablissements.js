(function () {

    const tbody = document.getElementById("etab-table-body");

    if (!tbody) {
        // Pas sur la page établissements.
        return;
    }

    function charger(params = "") {

        tbody.innerHTML = `<tr><td colspan="6" class="loading-row">Chargement des données...</td></tr>`;

        fetch(`/api/etablissements/${params}`)
            .then(response => response.json())
            .then(data => {

                if (data.features.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="6" class="loading-row">Aucun établissement ne correspond à ces critères.</td></tr>`;
                    document.getElementById("etab-count").textContent = "";
                    return;
                }

                tbody.innerHTML = data.features.map(f => {
                    const p = f.properties;
                    return `
                        <tr>
                            <td>${p.nom}</td>
                            <td><span class="badge">${p.type}</span></td>
                            <td>${p.quartier}</td>
                            <td>${p.adresse || "Non renseignée"}</td>
                            <td>${p.secteur || "Non renseigné"}</td>
                            <td>${p.capacite !== null && p.capacite !== undefined ? p.capacite : "—"}</td>
                        </tr>
                    `;
                }).join("");

                document.getElementById("etab-count").textContent =
                    `${data.features.length} établissement(s) affiché(s)`;
            })
            .catch(error => {
                console.error("Erreur :", error);
                tbody.innerHTML = `<tr><td colspan="6" class="loading-row">Erreur lors du chargement des données.</td></tr>`;
            });
    }

    function chargerTypes() {

        fetch("/api/types-etablissements/")
            .then(response => {
                if (!response.ok) throw new Error("indisponible");
                return response.json();
            })
            .then(data => {
                const select = document.getElementById("filter-type");
                data.types.forEach(t => {
                    const option = document.createElement("option");
                    option.value = t.libelle_type;
                    option.textContent = t.libelle_type;
                    select.appendChild(option);
                });
            })
            .catch(() => {
                fetch("/api/etablissements/")
                    .then(r => r.json())
                    .then(data => {
                        const select = document.getElementById("filter-type");
                        const types = new Set();
                        data.features.forEach(f => { if (f.properties.type) types.add(f.properties.type); });
                        Array.from(types).sort().forEach(type => {
                            const option = document.createElement("option");
                            option.value = type;
                            option.textContent = type;
                            select.appendChild(option);
                        });
                    });
            });
    }

    function appliquerFiltres() {
        const search = document.getElementById("search-etab").value.trim();
        const type = document.getElementById("filter-type").value;

        const params = new URLSearchParams();
        if (search) params.append("search", search);
        if (type) params.append("type", type);

        const query = params.toString();

        charger(query ? `?${query}` : "");

        // Garder l'export cohérent avec le filtre actif
        document.getElementById("btn-export").href =
            `/api/export/etablissements/${query ? `?${query}` : ""}`;
    }

    document.getElementById("btn-filtrer-etab").addEventListener("click", appliquerFiltres);

    document.getElementById("search-etab").addEventListener("keydown", function (e) {
        if (e.key === "Enter") appliquerFiltres();
    });

    chargerTypes();
    charger();

})();
