(function () {

    const container = document.getElementById("home-stats-inner");

    if (!container) {
        return;
    }

    function animerCompteur(element, valeurFinale, duree = 1200) {

        const debut = performance.now();

        function etape(maintenant) {

            const progression = Math.min((maintenant - debut) / duree, 1);
            const valeurActuelle = Math.round(progression * valeurFinale);

            element.textContent = valeurActuelle;

            if (progression < 1) {
                requestAnimationFrame(etape);
            } else {
                element.textContent = valeurFinale;
            }
        }

        requestAnimationFrame(etape);
    }

    function lancerAnimations() {

        fetch("/api/statistiques/")
            .then(response => response.json())
            .then(data => {

                animerCompteur(document.getElementById("stat-etablissements"), data.total_etablissements || 0);
                animerCompteur(document.getElementById("stat-types"), data.par_type.length || 0);
                animerCompteur(document.getElementById("stat-quartiers"), data.par_quartier.length || 0);
            })
            .catch(error => {
                console.error("Erreur stats accueil :", error);
            });
    }

    // On ne lance l'animation que lorsque la section devient visible à l'écran
    if ("IntersectionObserver" in window) {

        const observer = new IntersectionObserver(function (entries) {

            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    lancerAnimations();
                    observer.disconnect();
                }
            });

        }, { threshold: 0.3 });

        observer.observe(container);

    } else {
        lancerAnimations();
    }

})();
