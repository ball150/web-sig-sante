document.addEventListener("DOMContentLoaded", function () {

    // ==========================================
    // MENU MOBILE (hamburger)
    // ==========================================

    const toggle = document.getElementById("nav-toggle");
    const nav = document.getElementById("main-nav");

    if (toggle && nav) {

        toggle.addEventListener("click", function () {

            const isOpen = nav.classList.toggle("open");

            toggle.classList.toggle("open", isOpen);
            toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
        });

        nav.querySelectorAll("a").forEach(function (link) {
            link.addEventListener("click", function () {
                nav.classList.remove("open");
                toggle.classList.remove("open");
                toggle.setAttribute("aria-expanded", "false");
            });
        });
    }


    // ==========================================
    // NAVBAR : ombre au scroll
    // ==========================================

    const navbar = document.getElementById("navbar");

    if (navbar) {

        function majOmbreNavbar() {
            if (window.scrollY > 8) {
                navbar.classList.add("scrolled");
            } else {
                navbar.classList.remove("scrolled");
            }
        }

        majOmbreNavbar();
        window.addEventListener("scroll", majOmbreNavbar, { passive: true });
    }


    // ==========================================
    // BOUTON RETOUR EN HAUT
    // ==========================================

    const backToTop = document.getElementById("back-to-top");

    if (backToTop) {

        function majVisibiliteBouton() {
            if (window.scrollY > 400) {
                backToTop.classList.add("visible");
            } else {
                backToTop.classList.remove("visible");
            }
        }

        majVisibiliteBouton();
        window.addEventListener("scroll", majVisibiliteBouton, { passive: true });

        backToTop.addEventListener("click", function () {
            window.scrollTo({ top: 0, behavior: "smooth" });
        });
    }


    // ==========================================
    // APPARITION AU SCROLL (éléments .reveal)
    // ==========================================

    const elementsReveal = document.querySelectorAll(".reveal");

    if (elementsReveal.length > 0 && "IntersectionObserver" in window) {

        const observer = new IntersectionObserver(function (entries) {

            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add("reveal-visible");
                    observer.unobserve(entry.target);
                }
            });

        }, { threshold: 0.15 });

        elementsReveal.forEach(function (el) {
            observer.observe(el);
        });

    } else {
        // Repli : navigateur sans IntersectionObserver, on affiche direct
        elementsReveal.forEach(function (el) {
            el.classList.add("reveal-visible");
        });
    }

});
