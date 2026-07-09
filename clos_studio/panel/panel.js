/*
 * CLOS Studio — Panel Badacza (v0.8.5)
 *
 * Priorytet 1 (ten plik na tym etapie): wylacznie szkielet — przelaczanie
 * sekcji, dostepnosc klawiatury. ZERO danych, zero fetchowania.
 *
 * Loader danych (fetch z KONTRAKTU DANYCH, patrz SPRINT_v0.8.5.md) i render
 * sekcji z pobranego JSON zostana dodane w Priorytecie 2. Zadna metryka nie
 * moze trafic do tego pliku jako liczba na sztywno — to sprawdza
 * scripts/validate_panel.py (Priorytet 3).
 */

(function () {
  "use strict";

  var SECTIONS = [
    "overview", "lessons", "competency", "genomes",
    "provenance", "tests", "reports",
  ];

  var SECTION_LABELS = {
    overview: "Przegląd",
    lessons: "Lekcje i wyniki",
    competency: "Profil kompetencji",
    genomes: "Porównanie genomów",
    provenance: "Prowenancja",
    tests: "Testy i CI",
    reports: "Raporty",
  };

  function showSection(id) {
    if (SECTIONS.indexOf(id) === -1) return;

    SECTIONS.forEach(function (s) {
      var el = document.getElementById("section-" + s);
      if (el) el.classList.toggle("hidden", s !== id);
    });

    var navButtons = document.querySelectorAll(".nav[data-section]");
    navButtons.forEach(function (btn) {
      var on = btn.getAttribute("data-section") === id;
      btn.classList.toggle("on", on);
      btn.setAttribute("aria-current", on ? "true" : "false");
    });

    var heading = document.getElementById("main-heading");
    if (heading) heading.textContent = SECTION_LABELS[id] || id;

    if (history.replaceState) {
      history.replaceState(null, "", "#" + id);
    }
  }

  function initNav() {
    var navButtons = document.querySelectorAll(".nav[data-section]");
    navButtons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        showSection(btn.getAttribute("data-section"));
      });
    });

    var initial = (location.hash || "").replace("#", "");
    showSection(SECTIONS.indexOf(initial) !== -1 ? initial : "overview");
  }

  document.addEventListener("DOMContentLoaded", initNav);
})();
