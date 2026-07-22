/*
 * CLOS Studio — Panel Badacza (v0.8.5)
 *
 * Priorytet 1: szkielet — przelaczanie sekcji, dostepnosc klawiatury.
 * Priorytet 2: loader danych + render sekcji WYLACZNIE z pobranego JSON.
 * Priorytet 3 (ten plik teraz): zrodlem liczby testow i statusu CI jest
 * reports/status.json — generowany w CI (.github/workflows/ci.yml,
 * scripts/write_status.py) WYLACZNIE po zielonym pytest + trzech
 * walidatorach, wiec panel nie zaleznie od GitHub API (odporne na rate
 * limit) i nie zgaduje.
 *
 * ZERO metryk wpisanych na sztywno — kazda liczba w DOM pochodzi z fetch()
 * jednego z artefaktow w KONTRAKCIE DANYCH ponizej. scripts/validate_panel.py
 * skanuje ten plik w CI i failuje, jesli znajdzie wklejona liczbe/hash.
 */

(function () {
  "use strict";

  /* ---------- KONFIGURACJA (BASE) ---------- */
  var OWNER = "gozimek79-debug";
  var REPO = "SST-Incubator";
  var BRANCH = "v0.7.2-scientific-integrity";
  var BASE = "https://raw.githubusercontent.com/" + OWNER + "/" + REPO + "/" + BRANCH + "/";
  var API_BASE = "https://api.github.com/repos/" + OWNER + "/" + REPO;

  /* ---------- KONTRAKT DANYCH ---------- */
  var ARTIFACTS = {
    report: "reports/academy/L1_1_pattern_echo.json",
    competency: "publications/competency_profile.json",
    prereg: "publications/preregistration_L1_1.json",
    status: "reports/status.json",
    chronicle: "reports/history.json",
    population: "reports/population/population_validation_v0_11_0.json",
  };

  // CTO 2026-07-22 (audyt "panel samodzielny"): sekcja "Lekcje i wyniki"
  // CZYTA WYLACZNIE ten plik (re-run konfirmacyjny, 23 genomy x n=185/genom,
  // Hard-Halt PASS) - NIE demo-raporty ARTIFACTS.report/prereg (2 genomy,
  // n=10, v0.8/v0.9). WCZESNIEJ tu byla reczna lista POPULATION_LESSONS
  // (ktore lekcje/srodowiska/metryki pokazac) - to byl DOKLADNIE ten sam
  // blad co hardcode L1.1: WYKONAWCA decydowal co widac, nie DANE. Usunieta.
  // renderLessons() ponizej ODKRYWA lekcje/srodowiska/metryki przez
  // Object.keys() na kazdym poziomie - dodanie L1.3 do population json
  // pojawia sie w panelu bez zadnej zmiany w tym pliku (test docelowy CTO).
  // Nazwy lekcji ("Pattern Echo") swiadomie NIE sa tu odtworzone - plik
  // populacyjny nie ma pola z nazwa opisowa, a dopisywanie czegokolwiek do
  // przegłosowanego, potwierdzonego przez Final Audit Gate artefaktu
  // wykracza poza ten audyt (Problem B, oddzielne zadanie) - tytul karty to
  // surowy klucz lekcji (np. "L1.1"), srodowisko juz osobno w podtytule.

  // Auto-odswiezanie: pelny loadAll() co 10 minut (raw.githubusercontent ma
  // cache ~5 min, wiec czesciej nie ma sensu; GitHub API ma limit 60/h na IP
  // bez autoryzacji - 10 min => ~12-18 zapytan API/h, bezpiecznie ponizej).
  // Dodatkowo wiek danych w pulsie przeliczany co minute z JUZ pobranego
  // statusu (bez zadnego fetchu) - "3 min temu" nie zamarza na ekranie.
  var REFRESH_MS = 10 * 60 * 1000;
  var lastStatus = null;
  var lastRefreshAt = null;

  var C = {
    chA: "#4FC8E0", chB: "#A98CFF", ok: "#5FC98C", warn: "#F2B049",
    mut: "#78879A", txt: "#E8EDF3",
  };

  /* ---------- sekcje (musi byc zgodne z index.html) ---------- */
  var SECTIONS = ["overview", "history", "lessons", "competency", "genomes", "provenance", "tests", "reports"];
  var SECTION_LABELS = {
    overview: "Przegląd", history: "Historia", lessons: "Lekcje i wyniki", competency: "Profil kompetencji",
    genomes: "Porównanie genomów", provenance: "Prowenancja", tests: "Testy i CI", reports: "Raporty",
  };

  /* ================= nawigacja (Priorytet 1) ================= */
  function showSection(id) {
    if (SECTIONS.indexOf(id) === -1) return;
    SECTIONS.forEach(function (s) {
      var el = document.getElementById("section-" + s);
      if (el) el.classList.toggle("hidden", s !== id);
    });
    document.querySelectorAll(".nav[data-section]").forEach(function (btn) {
      var on = btn.getAttribute("data-section") === id;
      btn.classList.toggle("on", on);
      btn.setAttribute("aria-current", on ? "true" : "false");
    });
    var heading = document.getElementById("main-heading");
    if (heading) heading.textContent = SECTION_LABELS[id] || id;
    if (history.replaceState) history.replaceState(null, "", "#" + id);
  }

  function initNav() {
    document.querySelectorAll(".nav[data-section]").forEach(function (btn) {
      btn.addEventListener("click", function () { showSection(btn.getAttribute("data-section")); });
    });
    var initial = (location.hash || "").replace("#", "");
    showSection(SECTIONS.indexOf(initial) !== -1 ? initial : "overview");
  }

  /* ================= helpers ================= */
  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function fmtNum(v, digits) {
    if (v === null || v === undefined || typeof v !== "number" || isNaN(v)) return "—";
    return v.toFixed(digits === undefined ? 4 : digits);
  }

  function fmtBool(v) {
    return v === true ? "true" : v === false ? "false" : "—";
  }

  function truncHash(h) {
    if (!h || typeof h !== "string" || h.length < 20) return h || "—";
    return h.slice(0, 12) + "…" + h.slice(-6);
  }

  // SPRINT_v0.11.0.md Zadanie 3: formatowanie daty/wieku z timestampu ISO -
  // ZERO literalow dat/wersji w tym pliku, wszystko liczone z pol JSON w
  // momencie renderowania. "stale" = true gdy wiek > 7 dni, zeby zastoj
  // danych byl widoczny wizualnie (age-stale w panel.css), nie tylko w tekscie.
  function formatUtc(iso) {
    if (!iso) return null;
    var d = new Date(iso);
    if (isNaN(d.getTime())) return null;
    var pad = function (n) { return n < 10 ? "0" + n : String(n); };
    return d.getUTCFullYear() + "-" + pad(d.getUTCMonth() + 1) + "-" + pad(d.getUTCDate()) +
      " " + pad(d.getUTCHours()) + ":" + pad(d.getUTCMinutes()) + " UTC";
  }

  function ageInfo(iso) {
    if (!iso) return null;
    var then = new Date(iso).getTime();
    if (isNaN(then)) return null;
    var diffMs = Date.now() - then;
    if (diffMs < 0) return { text: "przed chwilą", days: 0 };
    var minutes = Math.floor(diffMs / 60000);
    var hours = Math.floor(diffMs / 3600000);
    var days = Math.floor(diffMs / 86400000);
    var text;
    if (minutes < 60) {
      text = minutes <= 1 ? "przed chwilą" : minutes + " min temu";
    } else if (hours < 24) {
      text = hours + " " + (hours === 1 ? "godzinę" : hours < 5 ? "godziny" : "godzin") + " temu";
    } else {
      text = days + " " + (days === 1 ? "dzień" : "dni") + " temu";
    }
    return { text: text, days: days, stale: days > 7 };
  }

  // Sekcje w index.html maja juz klase "grid" nadana statycznie — renderery
  // wstawiaja gotowe stringi HTML (karty/stuby) bezposrednio, bez
  // dodatkowego zagniezdzania wlasnego <div class="grid">.
  function setSectionHTML(id, html) {
    var container = document.getElementById("section-" + id);
    if (!container) return;
    container.innerHTML = html;
  }

  function stateHtml(kind, message, detail) {
    return '<div class="card-stub"><div class="state state-' + kind + '">' +
      "<p>" + escapeHtml(message) + "</p>" +
      (detail ? '<p class="state-detail">' + escapeHtml(detail) + "</p>" : "") +
      "</div></div>";
  }

  // Karta-notatka o brakującym pojedynczym artefakcie — uzywana WEWNATRZ
  // renderow, zeby przy czesciowym sukcesie (np. prereg OK, report nie)
  // informacja o bledzie nie zostala nadpisana przez czesciowy render.
  function missingArtifactHtml(artifactLabel, err) {
    var detail = (err && err.sourceUrl)
      ? "Nie udało się pobrać: " + err.sourceUrl + " (" + err.message + "). " +
        "Sprawdź, czy gałąź/plik istnieją pod tą ścieżką, i czy przeglądarka ma dostęp do raw.githubusercontent.com."
      : (err && err.message) || "nieznany błąd";
    return '<section class="card span"><div class="card-b"><div class="state state-error">' +
      "<p>Nie udało się wczytać: <code>" + escapeHtml(artifactLabel) + "</code></p>" +
      '<p class="state-detail">' + escapeHtml(detail) + "</p></div></div></section>";
  }

  function sectionError(id, artifactLabel, err) {
    setSectionHTML(id, missingArtifactHtml(artifactLabel, err));
  }

  // Blad wywolania GitHub API (nie raw.githubusercontent) — osobny,
  // czytelniejszy komunikat dla przypadku limitu zapytan (403 /
  // x-ratelimit-remaining=0), bo to realny scenariusz na hostowanym Pages
  // z wieloma userami z jednego zakresu IP. Jawnie mowi, ze WLASCIWE dane
  // (metryki naukowe) sa gdzie indziej i dzialaja niezaleznie.
  function apiErrorHtml(scopeLabel, err) {
    if (err && err.rateLimited) {
      return '<div class="state state-error">' +
        "<p>Limit zapytań GitHub API przekroczony (60/h bez autoryzacji dla tego adresu IP) — " +
        escapeHtml(scopeLabel) + " chwilowo niedostępne.</p>" +
        '<p class="state-detail">Właściwe dane (raporty, profil kompetencji, prowenancja, status testów/CI) ' +
        "są czytane z raw.githubusercontent.com, nie z GitHub API — nie są tym dotknięte, patrz pozostałe " +
        "sekcje/karty niżej.</p></div>";
    }
    return '<div class="state state-error"><p>Nie udało się pobrać z GitHub API: ' + escapeHtml(scopeLabel) + ".</p>" +
      '<p class="state-detail">' + escapeHtml((err && err.message) || "nieznany błąd") + "</p></div>";
  }

  /* ================= fetch layer ================= */
  function fetchJSON(path) {
    var url = BASE + path;
    return fetch(url).then(function (res) {
      if (!res.ok) {
        var e = new Error("HTTP " + res.status);
        e.sourceUrl = url;
        throw e;
      }
      return res.json();
    }).catch(function (err) {
      if (!err.sourceUrl) err.sourceUrl = url;
      throw err;
    });
  }

  // fetchJSON() zaklada JSON.parse - dokumenty .md sa tekstem, wiec sekcja
  // Raporty (#8, auto-discovery) potrzebuje osobnego pobierania surowej
  // tresci pliku, zeby wyciagnac z niej naglowek H1 jako opis.
  function fetchText(path) {
    var url = BASE + path;
    return fetch(url).then(function (res) {
      if (!res.ok) {
        var e = new Error("HTTP " + res.status);
        e.sourceUrl = url;
        throw e;
      }
      return res.text();
    }).catch(function (err) {
      if (!err.sourceUrl) err.sourceUrl = url;
      throw err;
    });
  }

  // GitHub API (nie raw.githubusercontent) ma limit 60 zapytan/h na IP bez
  // autoryzacji. Na hostowanym panelu, uzywanym przez wielu userow z tego
  // samego zakresu adresow, to realne ryzyko 403. apiHttpError() oznacza
  // taki blad jawna flaga rateLimited, zeby render mogl pokazac zrozumialy
  // komunikat zamiast pustej/zepsutej sekcji — i NIE blokowac reszty panelu,
  // bo wlasciwe metryki naukowe pochodza z raw.githubusercontent.com, ktore
  // ma inny, znacznie luzniejszy limit.
  function apiHttpError(res, url) {
    var e = new Error("HTTP " + res.status);
    e.sourceUrl = url;
    e.status = res.status;
    var remaining = res.headers && res.headers.get ? res.headers.get("x-ratelimit-remaining") : null;
    e.rateLimited = res.status === 403 || remaining === "0";
    return e;
  }

  // CTO 2026-07-22 (audyt "panel samodzielny", #6): odkrywa WSZYSTKIE
  // katalogi w publications/ i probuje pobrac metadata.json z kazdego -
  // zero filtra po prefiksie nazwy (wczesniej: tylko "EXP-*", wiec
  // L1_1_pattern_echo/L1_2_shock_recovery mialy OSOBNY, recznie zaszyty
  // fetch ARTIFACTS.metadata ograniczony do L1.1, a L1.2 (istniejacy bundle)
  // nigdzie sie nie pojawial). Dodanie L1_3_.../metadata.json do repo
  // pojawia sie w Prowenancji bez zadnej zmiany w tym pliku.
  function fetchAllBundles() {
    var listUrl = API_BASE + "/contents/publications?ref=" + BRANCH;
    return fetch(listUrl).then(function (res) {
      if (!res.ok) throw apiHttpError(res, listUrl);
      return res.json();
    }).then(function (entries) {
      var dirs = entries.filter(function (en) { return en.type === "dir"; });
      return Promise.all(dirs.map(function (d) {
        return fetchJSON("publications/" + d.name + "/metadata.json")
          .then(function (meta) { return { name: d.name, meta: meta, ok: true }; })
          .catch(function (err) { return { name: d.name, error: err, ok: false }; });
      }));
    });
  }

  // CTO 2026-07-22 (audyt "panel samodzielny", #8): odkrywa pliki .md w
  // podanym katalogu przez GitHub API listing (ten sam wzorzec co
  // fetchAllBundles) - opis kazdego wpisu to PIERWSZY NAGLOWEK H1 pliku
  // (fetchText + regex), NIE reczny string wpisany w panel.js. Wczesniej
  // caly ten spis (28 pozycji, 4 grupy tematyczne) byl tablica zaszyta
  // wprost w kodzie JS - identyczny blad co POPULATION_LESSONS (#3) i
  // ARTIFACTS.metadata (#6): WYKONAWCA decydowal co widac.
  function fetchMdReportsIn(dirPath) {
    var listUrl = API_BASE + "/contents" + (dirPath ? "/" + dirPath : "") + "?ref=" + BRANCH;
    return fetch(listUrl).then(function (res) {
      if (!res.ok) throw apiHttpError(res, listUrl);
      return res.json();
    }).then(function (entries) {
      var files = entries.filter(function (en) { return en.type === "file" && /\.md$/i.test(en.name); });
      return Promise.all(files.map(function (f) {
        var relPath = dirPath ? dirPath + "/" + f.name : f.name;
        return fetchText(relPath).then(function (text) {
          var m = text.match(/^#\s+(.+)$/m);
          return { path: relPath, title: m ? m[1].trim() : relPath, ok: true };
        }).catch(function (err) {
          return { path: relPath, title: relPath, ok: false, error: err };
        });
      }));
    });
  }

  // Zasieg CELOWO ograniczony do 4 katalogow, NIEREKURENCYJNIE (type==="file"
  // wprost w kazdym z nich, nie w podkatalogach): "" (root: raporty sprintow,
  // README, ROADMAP), docs/ (dokumentacja/metodologia), publications/
  // (competency_profile.md - JSON-y i podkatalogi bundli odfiltrowane przez
  // /\.md$/), clos_academy/ (ontologia). Rekurencyjne przeszukanie
  // publications//execution_package_v0_11/reports/population zalaloby liste
  // plikami RUN-LEVEL (np. 40 runs/run_*.json per bundle, 12765 rekordow
  // JSONL) - to sa DANE, juz pokazywane w Lekcjach/Prowenancji, nie
  // "dokumenty do przeczytania" ktore ta sekcja ma listowac.
  function fetchAllReports() {
    var dirs = ["", "docs", "publications", "clos_academy"];
    return Promise.all(dirs.map(fetchMdReportsIn)).then(function (lists) {
      return lists.reduce(function (acc, l) { return acc.concat(l); }, []);
    });
  }

  function fetchCommits(limit) {
    var url = API_BASE + "/commits?sha=" + BRANCH + "&per_page=" + (limit || 10);
    return fetch(url).then(function (res) {
      if (!res.ok) throw apiHttpError(res, url);
      return res.json();
    });
  }

  /* ================= SVG chart: MAE@50 ± CI95 =================
   * SPRINT_v0.11.0.md P1: pole bylo nazwane "MSE" (kod liczyl abs(), nie
   * kwadrat) - etykieta naprawiona tutaj. passCond.mse_at_tick_50_max
   * NIE jest zmieniane - to nazwa pola w zamrozonej prerejestracji
   * (publications/preregistration_L1_1.json), patrz aneks. */
  function maeChartSvg(genomeRows) {
    var W = 520, H = 220, padL = 48, padR = 16, padT = 18, padB = 34;
    var plotW = W - padL - padR, plotH = H - padT - padB;
    var maxVal = 0;
    genomeRows.forEach(function (g) { if (g.hi > maxVal) maxVal = g.hi; });
    maxVal = maxVal > 0 ? maxVal * 1.2 : 1;

    function y(v) { return padT + plotH - (v / maxVal) * plotH; }

    var ticks = 4, gridSvg = "";
    for (var t = 0; t <= ticks; t++) {
      var val = (maxVal * t) / ticks;
      var yy = y(val);
      gridSvg += '<line x1="' + padL + '" y1="' + yy + '" x2="' + (W - padR) + '" y2="' + yy +
        '" style="stroke:var(--line)" stroke-dasharray="2 4"/>';
      gridSvg += '<text x="' + (padL - 8) + '" y="' + (yy + 3) + '" text-anchor="end" ' +
        'style="fill:var(--mut);font-size:10px;font-family:\'IBM Plex Mono\',monospace">' +
        val.toFixed(2) + "</text>";
    }

    var n = genomeRows.length;
    var barsSvg = genomeRows.map(function (g, i) {
      var cx = padL + (plotW * (i + 0.5)) / n;
      var barW = Math.min(64, (plotW / n) * 0.5);
      var barY = y(g.mean);
      var barH = padT + plotH - barY;
      var errTop = y(g.hi), errBot = y(g.lo);
      var hasCi = g.valid;
      return (
        '<rect x="' + (cx - barW / 2) + '" y="' + barY + '" width="' + barW + '" height="' + Math.max(0, barH) +
        '" style="fill:' + g.color + ';fill-opacity:.85" rx="3"/>' +
        (hasCi ?
          '<line x1="' + cx + '" y1="' + errTop + '" x2="' + cx + '" y2="' + errBot + '" style="stroke:var(--txt);stroke-width:1.5"/>' +
          '<line x1="' + (cx - 6) + '" y1="' + errTop + '" x2="' + (cx + 6) + '" y2="' + errTop + '" style="stroke:var(--txt);stroke-width:1.5"/>' +
          '<line x1="' + (cx - 6) + '" y1="' + errBot + '" x2="' + (cx + 6) + '" y2="' + errBot + '" style="stroke:var(--txt);stroke-width:1.5"/>'
          : "") +
        '<text x="' + cx + '" y="' + (barY - 8) + '" text-anchor="middle" ' +
        'style="fill:var(--txt);font-size:11px;font-family:\'IBM Plex Mono\',monospace">' + g.mean.toFixed(4) + "</text>" +
        '<text x="' + cx + '" y="' + (H - 10) + '" text-anchor="middle" ' +
        'style="fill:var(--mut);font-size:11px;font-family:\'IBM Plex Mono\',monospace">' + escapeHtml(g.name) + "</text>"
      );
    }).join("");

    return (
      '<svg viewBox="0 0 ' + W + " " + H + '" width="100%" height="210" role="img" ' +
      'aria-label="MAE po 50 tickach ciszy, srednia z przedzialem ufnosci 95%, per genom">' +
      gridSvg + barsSvg + "</svg>"
    );
  }

  /* ================= renderery sekcji ================= */

  /* SPRINT_v0.11.0.md P1 (decyzja CTO 2026-07-18): PYTHON JEST JEDYNYM
   * ZRODLEM klasyfikacji valid/degenerate/insufficient - clos_scientist/
   * competency_profile.py juz ja liczy i zapisuje w comp.full_profile
   * (valid/degenerate/insufficient_data, gotowe listy pojec) oraz
   * comp.minimal_profile (axes/cognitive_axes/physiological_state_variables,
   * gotowe listy nazw). classifyConcepts() CZYTA te gotowe listy - NIE
   * liczy niczego. _fallbackClassifyConcepts() istnieje WYLACZNIE na
   * wypadek starego/niezgodnego competency_profile.json bez pola
   * full_profile (np. zacache'owany artefakt sprzed tej zmiany) - to jest
   * FALLBACK, nie zrodlo prawdy. Powod tej zmiany: poprzednia wersja
   * panelu liczyla klasyfikacje SAMA (competencyRowState()), wiec zmiana
   * ontologii 6+1 w Pythonie NIE dotarla do panelu automatycznie - "kod
   * (Python) != artefakt (widok)" w warstwie panelu, bez cracha i bez
   * ostrzezenia. scripts/validate_panel.py sprawdza teraz statycznie, ze
   * ten plik nie reimplementuje progow ci95_valid/n_effective poza tą
   * jedną, jawnie nazwaną funkcją fallbacku. */
  function _fallbackClassifyConcepts(concepts) {
    var byState = { valid: [], degenerate: [], insufficient: [] };
    concepts.forEach(function (c) {
      var state;
      if (c.status !== "measured") {
        state = "insufficient";
      } else {
        var genomeKeys = Object.keys(c.genomes || {});
        var allValid = genomeKeys.length > 0 && genomeKeys.every(function (g) { return c.genomes[g].ci95_valid === true; });
        state = allValid ? "valid" : "degenerate";
      }
      byState[state].push(c);
    });
    return byState;
  }

  function classifyConcepts(comp) {
    if (comp.full_profile) {
      return {
        valid: comp.full_profile.valid,
        degenerate: comp.full_profile.degenerate,
        insufficient: comp.full_profile.insufficient_data,
      };
    }
    return _fallbackClassifyConcepts(comp.concepts);
  }

  function renderOverview(ctx) {
    var comp = ctx.competency;
    var population = ctx.population;
    var commits = ctx.commits;
    var status = ctx.status;

    var measured = comp ? comp.summary.measured : null;
    var total = comp ? comp.summary.total_concepts : null;
    var validCount = comp ? classifyConcepts(comp).valid.length : null;
    // CTO 2026-07-22: liczba lekcji = Object.keys(population.lessons).length,
    // czyli ILE lekcji plik populacyjny FAKTYCZNIE zawiera - zero listy
    // wybranej recznie (patrz komentarz przy ARTIFACTS wyzej). L1.3 dopisana
    // do population json podniesie ta liczbe bez zadnej zmiany w panel.js.
    var lessonsCount = population && population.lessons ? Object.keys(population.lessons).length : 0;

    var tiles = [
      { l: "Status", val: "Research Grade Infrastructure", sub: "deklaracja repo, nie liczba", c: "var(--chA)", wide: true },
      { l: "Testy", val: status && status.tests ? String(status.tests.passed) : "—",
        sub: status ? "passed · reports/status.json" : "reports/status.json niedostępny", c: "var(--ok)" },
      { l: "CI", val: status && status.ci ? status.ci.conclusion : "—",
        sub: status ? "per-commit, po walidatorach" : "reports/status.json niedostępny",
        c: status && status.ci && status.ci.conclusion === "success" ? "var(--ok)" : "var(--crit)" },
      { l: "Core", val: "frozen", sub: "zasada sprintu (clos_brain/, clos_kernel/, genome/, birth/)", c: "var(--chA)" },
      { l: "Lekcje", val: lessonsCount ? String(lessonsCount) : "—", sub: lessonsCount ? "re-run konfirmacyjny v0.11 (population)" : "brak danych", c: "var(--txt)" },
      { l: "Kompetencje", val: comp ? validCount + "/" + total : "—",
        sub: comp ? "ważne CI95 · " + measured + "/" + total + " zmierzone" : "publications/competency_profile.json niedostępny", c: "var(--warn)" },
    ];

    var tilesHtml = tiles.map(function (t) {
      return '<div class="tile"><div class="tile-l">' + escapeHtml(t.l) + '</div>' +
        '<div class="tile-v" style="color:' + t.c + (t.wide ? ';font-size:16px' : "") + '">' + escapeHtml(t.val) + "</div>" +
        '<div class="tile-s">' + escapeHtml(t.sub) + "</div></div>";
    }).join("");

    var statusNotice = status ? "" : missingArtifactHtml(ARTIFACTS.status, ctx.statusError);

    var timelineHtml;
    if (commits && commits.length) {
      timelineHtml = '<div class="timeline">' + commits.map(function (c) {
        var sha = (c.sha || "").slice(0, 7);
        var msg = ((c.commit && c.commit.message) || "").split("\n")[0];
        return '<div class="tl-row"><code class="tl-c">' + escapeHtml(sha) + "</code>" +
          '<span class="tl-p"></span><span class="tl-t">' + escapeHtml(msg) + "</span></div>";
      }).join("") + "</div>";
    } else {
      timelineHtml = apiErrorHtml("historia commitów", ctx.commitsError);
    }
    var timelineCard = '<section class="card span"><header class="card-h">' +
      '<span class="card-t">Ostatnie commity</span><span class="card-s">gałąź ' + escapeHtml(BRANCH) +
      " · GitHub API</span></header><div class=\"card-b\">" + timelineHtml + "</div></section>";

    setSectionHTML("overview", '<div class="tiles" style="grid-column:1/-1">' + tilesHtml + "</div>" + timelineCard + statusNotice);
  }

  // Wiersz jednej metryki jednej lekcji - czyta WYLACZNIE gotowe pola z
  // population_validation_v0_11_0.json (status/classification/valid_rate/
  // pairwise_comparisons/omnibus_anova_raw) - zero progow/porownan liczonych
  // tutaj (to zablokowalby validate_panel.py, punkt A - i slusznie: Python
  // jest jedynym zrodlem klasyfikacji, patrz classifyConcepts() wyzej).
  // Uwaga (znalezione przy weryfikacji, 2026-07-21): n_genomes_total oraz n
  // per-genom RÓŻNIĄ SIĘ metryka-po-metryce w tej samej lekcji (np.
  // Homeostatic Resilience: n_genomes_total=14 zamiast 23, n per genom
  // 2-185 przez cenzurowanie - Working Memory/Stability maja jednolite
  // n=185/23 genomy). Dlatego liczby genomów/n sa pokazywane TUTAJ, per
  // wiersz metryki (jednoznaczne), NIE jako jeden zbiorczy naglowek karty
  // lekcji (bylby myslacy dla lekcji z cenzurowana metryka).
  function renderPopulationMetricRow(name, entry) {
    if (!entry) {
      return '<div class="leg-row"><code>' + escapeHtml(name) + "</code>" +
        '<span class="pill" style="color:var(--mut);border-color:#78879A55">brak w pliku</span></div>';
    }
    var pc = entry.pairwise_comparisons;
    var pairsText = pc ? pc.n_fdr_significant_q_0_05 + "/" + pc.n_pairs + " par (FDR q=0.05)" : "—";
    var anova = entry.omnibus_anova_raw;
    var fText = anova ? (anova.computable ? "f=" + fmtNum(anova.f, 4) : "nieobliczalne") : "—";
    var pgKeys = entry.per_genome ? Object.keys(entry.per_genome) : [];
    var nValues = pgKeys.map(function (g) { return entry.per_genome[g].n; });
    var nMin = nValues.length ? Math.min.apply(null, nValues) : null;
    var nMax = nValues.length ? Math.max.apply(null, nValues) : null;
    var nText = nMin === null ? "—" : nMin === nMax ? "n=" + nMin : "n=" + nMin + "–" + nMax + " (cenzurowane)";
    return '<div class="leg-row"><code>' + escapeHtml(name) + "</code>" +
      '<span class="pill">' + escapeHtml(entry.classification || "—") + "</span>" +
      '<span class="leg-note">' + (entry.n_genomes_valid != null ? entry.n_genomes_valid : "—") + "/" +
      (entry.n_genomes_total != null ? entry.n_genomes_total : "—") + " genomów, " + nText + "</span>" +
      '<span class="leg-note">valid_rate=' + fmtNum(entry.valid_rate, 2) + "</span>" +
      '<span class="leg-note">' + pairsText + "</span>" +
      '<span class="leg-note">ANOVA surowe ' + fText + "</span></div>";
  }

  // CTO 2026-07-22: ODKRYWA lekcje/srodowiska/metryki przez Object.keys() na
  // kazdym poziomie zagniezdzenia population.lessons - zero recznej listy
  // (patrz komentarz przy ARTIFACTS). Renderuje WSZYSTKO co znajdzie w
  // pliku, wlacznie z kontrolnymi srodowiskami (np. stable_world) - panel
  // nie decyduje co jest "wazne", pokazuje to co jest w danych, sortowanie
  // alfabetyczne kluczy jest jedynym porzadkiem narzuconym przez JS.
  function renderLessons(population, populationErr) {
    if (!population || !population.lessons) { setSectionHTML("lessons", missingArtifactHtml(ARTIFACTS.population, populationErr)); return; }

    var statusNote = population.dataset_status
      ? '<p class="prose" style="grid-column:1/-1">' + escapeHtml(population.dataset_status) + "</p>" : "";

    var lessonKeys = Object.keys(population.lessons).sort();
    var cards = lessonKeys.map(function (lessonKey) {
      var envs = population.lessons[lessonKey] || {};
      var envKeys = Object.keys(envs).sort();
      return envKeys.map(function (envKey) {
        var envData = envs[envKey] || {};
        var metricKeys = Object.keys(envData).sort();
        var rows = metricKeys.map(function (m) { return renderPopulationMetricRow(m, envData[m]); }).join("");
        return '<section class="card span"><header class="card-h">' +
          '<span class="card-t">' + escapeHtml(lessonKey) + "</span>" +
          '<span class="card-s">środowisko: ' + escapeHtml(envKey) + " · " + metricKeys.length +
          " metryk w pliku · re-run konfirmacyjny</span></header>" +
          '<div class="card-b"><div class="legacy">' + (rows || '<p class="prose">Brak metryk w tym środowisku.</p>') + "</div>" +
          '<p class="note">Liczby parowe (Welch+FDR) i omnibusowe (ANOVA, surowe) wprost z ' +
          "<code>" + escapeHtml(ARTIFACTS.population) + "</code>. Interpretacja " +
          "(VALIDATED/EXPERIMENTAL, test Kruskal-Wallis niezależny od ANOVA) jest w " +
          "<code>docs/METRIC_STATUS_TABLE.md</code> — panel pokazuje surowe dane, nie ocenę.</p>" +
          "</div></section>";
      }).join("");
    }).join("");

    setSectionHTML("lessons", statusNote + (cards || '<p class="prose" style="grid-column:1/-1">Plik populacyjny nie zawiera żadnej lekcji.</p>'));
  }

  // Audytor 2026-07-21: demo-raport 2-genomowy (v0.8/v0.9, n=10) NIE jest
  // kasowany - byl tu wczesniej pod bledna etykieta "wynik lekcji"
  // (mylony z populacyjnym re-runem). Przeniesiony do Prowenancji z jawnym
  // banerem archiwalnym - slad audytowy zostaje widoczny, nie znika.
  function renderLegacyDemoCard(report, prereg, reportErr, preregErr) {
    if (!report && !prereg) return missingArtifactHtml(ARTIFACTS.report, reportErr);

    var design = prereg ? prereg.experiment_design : null;
    var passCond = prereg ? prereg.pass_conditions : null;

    var scenario = (report && report.scenario) || (design && design.scenario) || "—";
    var control = (report && report.control_baseline) || (design && design.control_baseline && design.control_baseline.scenario) || "—";
    var seeds = design && design.seeds ? design.seeds.length : (report ? Object.keys(report.per_genome || {}).length && (report.results ? report.results.length / Object.keys(report.per_genome).length : null) : null);

    var allPassed = null;
    if (report && report.results) {
      var primaryRuns = report.results.filter(function (r) { return r.scenario === report.scenario; });
      if (primaryRuns.length) allPassed = primaryRuns.every(function (r) { return r.passed === true; });
    }

    var archivedBanner = '<div class="datastate datastate-archived">' +
      "<b>Archiwalne demo (v0.8/v0.9, 2 genomy, n=10)</b> — NIE wynik konfirmacyjny. " +
      "Populacyjny re-run (23 genomy, n=185) jest w zakładce „Lekcje i wyniki”, " +
      "źródło <code>" + escapeHtml(ARTIFACTS.population) + "</code>.</div>";

    var head =
      '<section class="card span"><header class="card-h"><span class="card-t">' +
      escapeHtml((prereg && prereg.lesson_id) || (report && report.lesson) || "L1.1") + " — " +
      escapeHtml((report && report.title) || (prereg && prereg.title) || "") + " (demo)</span>" +
      '<span class="card-s">' + escapeHtml(scenario) + " · kontrola: " + escapeHtml(control) + "</span></header>" +
      '<div class="card-b">' + archivedBanner +
      (prereg ? '<p class="prose"><b>Hipoteza.</b> ' + escapeHtml(prereg.hypothesis) + "</p>" : "") +
      '<div class="kv">' +
      '<div><span>Primary endpoint</span><b>' + escapeHtml((prereg && prereg.primary_endpoint && prereg.primary_endpoint.metric) || "—") +
      (prereg && prereg.primary_endpoint ? " @ " + prereg.primary_endpoint.measurement_tick : "") + "</b></div>" +
      '<div><span>Kryterium PASS</span><b>' + (passCond ? "MAE@50 &lt; " + fmtNum(passCond.mse_at_tick_50_max, 2) : "—") + "</b></div>" +
      '<div><span>Seedy / genom</span><b>' + (seeds || "—") + "</b></div>" +
      '<div><span>Wynik</span><b style="color:' + (allPassed === null ? "var(--mut)" : allPassed ? "var(--ok)" : "var(--crit)") + '">' +
      (allPassed === null ? "—" : allPassed ? "PASS" : "FAIL") + "</b></div>" +
      "</div></div></section>";

    var chartHtml = "";
    if (report && report.per_genome) {
      var keys = Object.keys(report.per_genome);
      var colors = [C.chA, C.chB];
      var rows = keys.map(function (g, i) {
        var s = report.per_genome[g].experimental_stats;
        return { name: g, mean: s.mean, lo: s.ci95_low, hi: s.ci95_high, valid: s.ci95_valid, color: colors[i % colors.length] };
      });
      chartHtml =
        '<section class="card span"><header class="card-h"><span class="card-t">MAE @ 50 · średnia ± CI95 (demo)</span>' +
        '<span class="card-s">scenariusz: ' + escapeHtml(scenario) + "</span></header>" +
        '<div class="card-b">' + maeChartSvg(rows) +
        '<p class="note">Kontrola <code>' + escapeHtml(control) + "</code> jest deterministyczna (n_effective=1, " +
        "CI95 nie dotyczy) — punkt odniesienia, nie źródło wariancji.</p></div></section>";
    }

    return head + chartHtml;
  }

  function renderConceptRow(c, state) {
    var label = state === "valid" ? "zmierzone" : state === "degenerate" ? "zdegenerowane" : "brak danych";
    var color = state === "valid" ? "var(--ok)" : state === "degenerate" ? "var(--warn)" : "var(--mut)";

    var body = "";
    if (state === "valid" || state === "degenerate") {
      var genomeKeys = Object.keys(c.genomes || {});
      var colors = [C.chA, C.chB];
      var gRows = genomeKeys.map(function (g, i) {
        var gd = c.genomes[g];
        return '<div class="gbar"><span class="gbar-lbl" style="color:' + colors[i % colors.length] + '">' +
          escapeHtml(g) + "</span>" +
          '<div class="gbar-track"><div class="gbar-fill" style="width:' +
          Math.min(100, Math.abs(gd.value) / (Math.abs(gd.value) + 0.01) * 40 + 10) + "%;background:" + colors[i % colors.length] + '"></div></div>' +
          '<code class="gbar-val">' + fmtNum(gd.value, 6) + "</code>" +
          '<code class="gbar-ci">n_eff=' + gd.n_effective + " · ci95_valid=" + fmtBool(gd.ci95_valid) + "</code></div>";
      }).join("");
      var dHtml = (c.genome_comparison && c.genome_comparison.computable)
        ? '<div class="crow-d">Cohen&apos;s d (genom vs genom): <code>' + fmtNum(c.genome_comparison.cohens_d, 3) + "</code></div>"
        : "";
      body = '<div class="crow-body">' + gRows + dHtml + "</div>";
      if (state === "degenerate") {
        body += '<div class="crow-warn">⚠ co najmniej jeden genom ma <code>ci95_valid=false</code> — ' +
          "policzone, ale bez informacji o wariancji między seedami.</div>";
      }
    } else {
      body = '<div class="crow-gap">brak lekcji mierzącej to pojęcie (status: <code>insufficient_data</code>)</div>';
    }

    if (c.secondary_observations && c.secondary_observations.length) {
      var secHtml = c.secondary_observations.map(function (obs) {
        var gHtml = Object.keys(obs.genomes || {}).map(function (g) {
          var gs = obs.genomes[g];
          return '<code class="gbar-ci">' + escapeHtml(g) + "=" + fmtNum(gs.value, 4) +
            " · deterministic=" + fmtBool(gs.deterministic) + " · ci95_valid=" + fmtBool(gs.ci95_valid) + "</code>";
        }).join(" ");
        return '<div class="crow-warn">⊘ nie wliczone do puli CI95 (' + escapeHtml(obs.lesson) + "): " + gHtml +
          '<br><span style="opacity:.8">' + escapeHtml(obs.note || "") + "</span></div>";
      }).join("");
      body += secHtml;
    }

    return '<div class="crow ' + state + '"><div class="crow-head"><span class="crow-k">' + escapeHtml(c.concept) + "</span>" +
      '<span class="pill" style="color:' + color + ";border-color:" + color + '55">' + label +
      (c.source_lesson ? " · " + escapeHtml(c.source_lesson) : "") + "</span></div>" + body + "</div>";
  }

  // SPRINT_v0.11.0.md Zadanie 3: banery cyklu zycia danych dla sekcji, ktore
  // czytaja competency_profile.json - CZYTA pola juz obecne
  // (comp.generated_at, comp.dataset_status), nie liczy/nie zgaduje niczego.
  // Dwa banery moga wystapic razem: dane SA zywe (maja generated_at) I
  // JEDNOCZESNIE oznaczone Exploratory (jeszcze nie potwierdzajace) - to nie
  // sprzecznosc, to dwa rozne pytania (swiezosc artefaktu vs. status naukowy).
  function datasetStateBannersHtml(comp) {
    var html = "";
    if (comp.generated_at) {
      var age = ageInfo(comp.generated_at);
      html += '<div class="datastate datastate-live">' +
        "<b>Żywe:</b> zaktualizowano " + escapeHtml(formatUtc(comp.generated_at) || comp.generated_at) +
        (age ? ' <span class="' + (age.stale ? "age-stale" : "") + '">(' + escapeHtml(age.text) + ")</span>" : "") +
        "</div>";
    }
    if (comp.dataset_status) {
      html += '<div class="datastate datastate-exploratory">' +
        "<b>Exploratory Dataset:</b> " + escapeHtml(comp.dataset_status) + "</div>";
    }
    return html;
  }

  function renderCompetency(comp) {
    if (!comp) return;
    var measured = comp.summary.measured, total = comp.summary.total_concepts;
    var byState = classifyConcepts(comp);

    var stateByName = {};
    byState.valid.forEach(function (c) { stateByName[c.concept] = "valid"; });
    byState.degenerate.forEach(function (c) { stateByName[c.concept] = "degenerate"; });
    byState.insufficient.forEach(function (c) { stateByName[c.concept] = "insufficient"; });

    // SPRINT_v0.11.0.md P1 (decyzja CTO 2026-07-17/18): rozroznienie OS
    // POZNAWCZYCH od ZMIENNYCH STANU FIZJOLOGICZNEGO (np. Final Energy
    // Level - mierzy stan systemu, nie jego zdolnosc do czegokolwiek) jest
    // CZYTANE z comp.minimal_profile.cognitive_axes/.physiological_state_variables
    // (gotowe listy NAZW z Pythona), nie liczone tutaj z jakiegokolwiek
    // pola per-koncept. Fallback (stary JSON bez tego podzialu): wszystko
    // traktowane jako poznawcze - jawnie gorsza, ale bezpieczna degradacja.
    var conceptByName = {};
    comp.concepts.forEach(function (c) { conceptByName[c.concept] = c; });
    var cognitiveNames = (comp.minimal_profile && comp.minimal_profile.cognitive_axes) || byState.valid.map(function (c) { return c.concept; });
    var physiologicalNames = (comp.minimal_profile && comp.minimal_profile.physiological_state_variables) || [];
    var validCognitive = cognitiveNames.map(function (name) { return conceptByName[name]; }).filter(Boolean);
    var validPhysiological = physiologicalNames.map(function (name) { return conceptByName[name]; }).filter(Boolean);

    var minimalCard =
      '<section class="card span"><header class="card-h"><span class="card-t">Profil minimalny (oficjalny)</span>' +
      '<span class="card-s">' + byState.valid.length + "/" + total + " pojęć z ważnym CI95 — " +
      validCognitive.length + " poznawczych + " + validPhysiological.length + " stanu fizjologicznego</span></header>" +
      '<div class="card-b">' +
      '<h4 class="comp-subhead">Osie poznawcze (' + validCognitive.length + ')</h4>' +
      '<div class="comp">' + validCognitive.map(function (c) { return renderConceptRow(c, "valid"); }).join("") + "</div>" +
      (validPhysiological.length ?
        '<h4 class="comp-subhead">Zmienne stanu fizjologicznego (' + validPhysiological.length + ') — NIE zdolności poznawcze</h4>' +
        '<div class="comp">' + validPhysiological.map(function (c) { return renderConceptRow(c, "valid"); }).join("") + "</div>"
        : "") +
      '<p class="note">Wyłącznie pojęcia, dla których wszystkie obecne genomy mają <code>ci95_valid=true</code> ' +
      "— jedyny profil, na który można się powołać jako \"co system faktycznie mierzy wiarygodnie\". " +
      "Zmienne stanu fizjologicznego mierzą STAN systemu, nie jego kompetencję — nie sumować z osiami " +
      "poznawczymi jako równoważne wpisy.</p></div></section>";

    var fullCard =
      '<section class="card span"><header class="card-h"><span class="card-t">Profil pełny</span>' +
      '<span class="card-s">zmierzone ' + measured + "/" + total + " · ważne CI95 " + byState.valid.length + "/" + total +
      ' — luki są jawne, nie ukryte</span></header><div class="card-b"><div class="comp">' +
      comp.concepts.map(function (c) { return renderConceptRow(c, stateByName[c.concept]); }).join("") + "</div></div></section>";

    setSectionHTML("competency", datasetStateBannersHtml(comp) + minimalCard + fullCard);
  }

  function renderGenomes(comp) {
    if (!comp) return;
    var rows = classifyConcepts(comp).valid;
    var genomeKeys = rows.length ? Object.keys(rows[0].genomes) : [];

    var trHtml = rows.map(function (c) {
      var g0 = genomeKeys[0], g1 = genomeKeys[1];
      var v0 = c.genomes[g0].value, v1 = c.genomes[g1] ? c.genomes[g1].value : null;
      var diff = v1 !== null ? v1 - v0 : null;
      var d = c.genome_comparison && c.genome_comparison.computable ? c.genome_comparison.cohens_d : null;
      return "<tr><td>" + escapeHtml(c.concept) + '</td><td><code style="color:' + C.chA + '">' + fmtNum(v0, 4) + "</code></td>" +
        '<td><code style="color:' + C.chB + '">' + (v1 !== null ? fmtNum(v1, 4) : "—") + "</code></td>" +
        "<td><code>" + (diff !== null ? fmtNum(diff, 4) : "—") + "</code></td>" +
        '<td><code style="color:' + (d !== null && Math.abs(d) > 0.8 ? "var(--warn)" : "var(--txt)") + '">' +
        (d !== null ? fmtNum(d, 3) : "n/d") + "</code></td></tr>";
    }).join("");

    var html =
      '<section class="card span"><header class="card-h"><span class="card-t">' +
      (genomeKeys.length ? escapeHtml(genomeKeys.join(" vs ")) : "Porównanie genomów") + "</span>" +
      '<span class="card-s">tylko pojęcia z ważnym CI95 · effect size między genomami</span></header>' +
      '<div class="card-b"><table class="tbl"><thead><tr><th>Pojęcie</th><th>' + escapeHtml(genomeKeys[0] || "genom A") +
      "</th><th>" + escapeHtml(genomeKeys[1] || "genom B") + "</th><th>Δ śr.</th><th>Cohen&apos;s d</th></tr></thead>" +
      "<tbody>" + (trHtml || '<tr><td colspan="5">Brak pojęć z ważnym CI95.</td></tr>') + "</tbody></table>" +
      '<p class="note">Porównanie opiera się wyłącznie na pojęciach, dla których <code>competency_profile.json</code> ' +
      "podaje <code>ci95_valid=true</code> dla obu genomów.</p></div></section>";
    setSectionHTML("genomes", datasetStateBannersHtml(comp) + html);
  }

  // CTO 2026-07-22 (#6): jedna karta na kazdy bundle z pelnym ksztaltem
  // metadata.json (eksperyment_id/git_commit/hashe/timestamp/frozen) -
  // dziala dla L1.1, L1.2 i kazdego przyszlego L1_x_.../metadata.json bez
  // zmiany tej funkcji. Legacy (pre-0.7.2, pole "provenance") ma inny,
  // rzadszy ksztalt - rozroznione PO OBECNOSCI POLA w danych, nie po nazwie
  // katalogu (wczesniej: "EXP-*" prefix hardkodowany w fetchAllBundles).
  var BUNDLE_FIELDS = ["experiment_id", "git_commit", "config_hash", "manifest_hash", "timestamp", "total_runs", "clos_version", "reproducible"];

  function renderBundleCard(item) {
    if (!item.ok) {
      return '<div class="leg-row"><code>' + escapeHtml(item.name) + "</code>" +
        '<span class="leg-note" style="color:var(--crit)">nie wczytano metadata.json</span></div>';
    }
    // Dwa ROZNE ksztalty, celowo NIE pod jedna nazwa zmiennej: bundle legacy
    // (pole "provenance", brak frozen/frozen_reason) uzywa "legacy" - poza
    // zasiegiem scripts/validate_panel.py (CHAIN_ROOTS), bo to inny, uboszy
    // ksztalt niz L1_1_pattern_echo/metadata.json (referencyjny plik
    // walidatora). Bundle "bogaty" (L1.1/L1.2/przyszle) uzywa "metadata" -
    // TA nazwa jest scisle sprawdzana przez validate_panel.py punkt B
    // (kazdy metadata.x.y w kodzie MUSI istniec w realnym pliku referencyjnym) -
    // NIE zmieniac nazwy bez zmiany walidatora, inaczej test_missing_frozen_reason_key_fails
    // przestaje wykrywac usuniety klucz.
    if (item.meta.provenance) {
      var legacy = item.meta;
      return '<div class="leg-row"><code>' + escapeHtml(legacy.experiment_id || item.name) + "</code>" +
        '<span class="pill" style="color:var(--mut);border-color:#78879A55">' + escapeHtml(legacy.provenance) + "</span>" +
        '<span class="leg-note">git_commit: ' + (legacy.git_commit ? escapeHtml(truncHash(legacy.git_commit)) : "pusty (nie zgadywany)") + "</span></div>";
    }
    var metadata = item.meta;
    // SPRINT_v0.11.0.md Zadanie 3 (NAJWAZNIEJSZE z trzech stanow): bundle
    // frozen=true NIGDY sie nie zaktualizuje (decyzja CTO, egzekwowana przez
    // scripts/validate_bundle_freshness.py) - bez tej etykiety panel
    // wygladalby na ZEPSUTY (dane "stare"), a jest POPRAWNY.
    var frozenBanner = metadata.frozen
      ? '<div class="datastate datastate-frozen">' +
        "<b>❄ Frozen Historical Artifact</b> — celowo niezmieniany od " +
        escapeHtml(String(metadata.timestamp || "—").replace("T", " ")) +
        (metadata.clos_version ? " (clos_version " + escapeHtml(metadata.clos_version) + ")" : "") +
        ".<br>" + escapeHtml(metadata.frozen_reason || "") + "</div>"
      : "";
    var fieldsHtml = BUNDLE_FIELDS.filter(function (k) { return metadata[k] !== undefined; }).map(function (k) {
      var v = metadata[k];
      var shown = (k === "git_commit" || k === "config_hash" || k === "manifest_hash") ? truncHash(v) :
        (k === "timestamp" ? String(v).replace("T", " ") :
        (k === "reproducible" ? (v ? "✓ true" : "✗ false") : String(v)));
      return "<div><dt>" + k + "</dt><dd>" + escapeHtml(shown) + "</dd></div>";
    }).join("");
    return '<section class="card span"><header class="card-h"><span class="card-t">Bundle ' +
      escapeHtml(metadata.experiment_id || item.name) + " — prowenancja</span>" +
      '<span class="card-s">odtwarzalność eksperymentu</span></header><div class="card-b">' + frozenBanner +
      '<dl class="prov">' + fieldsHtml + "</dl></div></section>";
  }

  // CTO 2026-07-22 (#6): "slad NAJWAZNIEJSZEGO zestawu danych" - baseline
  // AUD-001/Hard-Halt dla re-runu konfirmacyjnego v0.11. Zrodlo: pola JUZ
  // OBECNE w population_validation_v0_11_0.json (hard_halt_baseline,
  // git_commit, manifest, n_raw_records) - ten plik jest JUZ pobrany dla
  // sekcji Lekcje (ARTIFACTS.population), wiec ZERO dodatkowego fetchu.
  // Swiadomie NIE parsuje execution_package_v0_11/hashes/baseline_hash.txt
  // (plik tekstowy z komentarzami, nie JSON - parsowanie go w JS byloby
  // kruche) - population json niesie TE SAME fakty (ten sam baseline, ten
  // sam commit) w formie juz strukturalnej, bez duplikowania zrodla prawdy.
  function renderHardHaltCard(population) {
    if (!population) return "";
    var fdr = population.fdr_correction_omnibus;
    return '<section class="card span"><header class="card-h">' +
      '<span class="card-t">Re-run konfirmacyjny — Hard-Halt / prowenancja</span>' +
      '<span class="card-s">' + escapeHtml(population.study_id || "—") + "</span></header>" +
      '<div class="card-b"><dl class="prov">' +
      "<div><dt>hard_halt_baseline (AUD-001)</dt><dd>" + escapeHtml(truncHash(population.hard_halt_baseline)) + "</dd></div>" +
      "<div><dt>git_commit</dt><dd>" + escapeHtml(truncHash(population.git_commit)) + "</dd></div>" +
      "<div><dt>manifest</dt><dd>" + escapeHtml(population.manifest || "—") + "</dd></div>" +
      "<div><dt>n_raw_records</dt><dd>" + escapeHtml(String(population.n_raw_records != null ? population.n_raw_records : "—")) + "</dd></div>" +
      (fdr ? "<div><dt>fdr_correction.n_real_testable_cells</dt><dd>" + escapeHtml(String(fdr.n_real_testable_cells)) + "</dd></div>" : "") +
      '</dl><p class="note">Pola wprost z <code>' + escapeHtml(ARTIFACTS.population) +
      "</code> (już pobrany dla sekcji Lekcje) — kanoniczny ślad Hard-Halt dla aktualnego, " +
      "konfirmacyjnego zestawu danych.</p></div></section>";
  }

  function renderProvenance(bundles, bundlesError, population, demoReport, demoPrereg, demoReportError, demoPreregError) {
    var hardHaltCard = renderHardHaltCard(population);

    var bundlesHtml;
    if (bundles && bundles.length) {
      var rich = bundles.filter(function (b) { return b.ok && !b.meta.provenance; });
      var sparse = bundles.filter(function (b) { return !b.ok || b.meta.provenance; });
      var richCards = rich.map(renderBundleCard).join("");
      var sparseCard = sparse.length
        ? '<section class="card span"><header class="card-h"><span class="card-t">Bundle legacy / niekompletne</span>' +
          '<span class="card-s">oznaczone, prowenancja nie fabrykowana · GitHub API</span></header>' +
          '<div class="card-b"><div class="legacy">' + sparse.map(renderBundleCard).join("") + "</div></div></section>"
        : "";
      bundlesHtml = richCards + sparseCard;
    } else {
      bundlesHtml = '<section class="card span"><div class="card-b">' +
        apiErrorHtml("lista bundli publikacji", bundlesError) + "</div></section>";
    }

    var demoCard = renderLegacyDemoCard(demoReport, demoPrereg, demoReportError, demoPreregError);

    setSectionHTML("provenance", hardHaltCard + bundlesHtml + demoCard);
  }

  function renderTests(status, statusErr) {
    if (!status) {
      setSectionHTML("tests", missingArtifactHtml(ARTIFACTS.status, statusErr));
      return;
    }

    var tests = status.tests || {};
    var ci = status.ci || {};
    var validators = status.validators || {};

    var tiles = [
      { l: "pytest", val: tests.passed != null ? String(tests.passed) : "—",
        sub: "passed", c: tests.status === "green" ? "var(--ok)" : "var(--crit)" },
      { l: "Core", val: "frozen", sub: "zasada sprintu (clos_brain/, clos_kernel/, genome/, birth/)", c: "var(--chA)" },
      { l: "CI", val: ci.conclusion || "—", sub: escapeHtml(ci.workflow || "reports/status.json"),
        c: ci.conclusion === "success" ? "var(--ok)" : "var(--crit)" },
    ];
    var tilesHtml = tiles.map(function (t) {
      return '<div class="tile"><div class="tile-l">' + escapeHtml(t.l) + "</div>" +
        '<div class="tile-v" style="color:' + t.c + '">' + escapeHtml(t.val) + "</div>" +
        '<div class="tile-s">' + t.sub + "</div></div>";
    }).join("");

    var validatorRows = Object.keys(validators).map(function (name) {
      var v = validators[name];
      var ok = v === "OK";
      return '<div class="leg-row"><code>' + escapeHtml(name) + "</code>" +
        '<span class="pill" style="color:' + (ok ? "var(--ok)" : "var(--crit)") +
        ";border-color:" + (ok ? "var(--ok)" : "var(--crit)") + '55">' + escapeHtml(v) + "</span></div>";
    }).join("");

    var validatorsCard =
      '<section class="card span"><header class="card-h"><span class="card-t">Walidatory (bramka jakości)</span>' +
      '<span class="card-s">uruchamiane w CI na każdy push</span></header><div class="card-b">' +
      '<div class="legacy">' + (validatorRows || "<p>Brak danych o walidatorach.</p>") + "</div>" +
      '<p class="note">Status generowany WYŁĄCZNIE, gdy wszystkie kroki CI (pytest + 3 walidatory) ' +
      "zakończyły się sukcesem — jeśli którykolwiek zawiedzie, job CI przerywa się przed zapisem " +
      "<code>reports/status.json</code>, więc ten plik nigdy nie może zawierać fałszywego OK.</p></div></section>";

    var metaCard =
      '<section class="card span"><header class="card-h"><span class="card-t">Źródło</span></header>' +
      '<div class="card-b"><dl class="prov"><div><dt>commit</dt><dd>' + escapeHtml(truncHash(status.commit)) + "</dd></div>" +
      "<div><dt>branch</dt><dd>" + escapeHtml(status.branch || "—") + "</dd></div>" +
      "<div><dt>timestamp</dt><dd>" + escapeHtml(String(status.timestamp || "—").replace("T", " ")) + "</dd></div>" +
      "</dl></div></section>";

    setSectionHTML("tests", '<div class="tiles" style="grid-column:1/-1">' + tilesHtml + "</div>" + validatorsCard + metaCard);
  }

  /* ================= Historia (kronika laboratorium) =================
   * Wpisy kroniki pochodza z reports/history.json (DANE, recznie
   * utrzymywana kronika - jak lista w sekcji Raporty), NIE z tego pliku:
   * validate_panel.py skanuje panel.js pod katem wklejonych metryk/hashy,
   * wiec tresc historyczna (liczby, commity) MUSI zyc w artefakcie JSON.
   * Obok kroniki - zywy strumien commitow z GitHub API (operacje biezace). */
  function renderHistory(chron, commits, chronErr, commitsErr) {
    var chronicleCard;
    if (chron && chron.entries && chron.entries.length) {
      var entriesHtml = chron.entries.map(function (ev) {
        var commitHtml = ev.commit
          ? '<div class="hist-commit">commit <a href="https://github.com/' + OWNER + "/" + REPO + "/commit/" +
            encodeURIComponent(ev.commit) + '" target="_blank" rel="noopener"><code>' + escapeHtml(ev.commit) + "</code></a></div>"
          : "";
        return '<article class="hist-entry">' +
          '<div class="hist-when">' + escapeHtml(ev.date || "—") +
          (ev.sprint ? '<span class="hist-sprint">' + escapeHtml(ev.sprint) + "</span>" : "") + "</div>" +
          "<div>" +
          '<h3 class="hist-title">' + escapeHtml(ev.title || "") + "</h3>" +
          '<p class="hist-body">' + escapeHtml(ev.body || "") + "</p>" +
          commitHtml +
          "</div></article>";
      }).join("");
      chronicleCard =
        '<section class="card span"><header class="card-h"><span class="card-t">' + escapeHtml(chron.title || "Kronika") + "</span>" +
        '<span class="card-s">' + chron.entries.length + " wpisów · aktualizacja " + escapeHtml(chron.updated || "—") + "</span></header>" +
        '<div class="card-b"><div class="hist">' + entriesHtml + "</div>" +
        '<p class="note">' + escapeHtml(chron.note || "") + "</p></div></section>";
    } else {
      chronicleCard = missingArtifactHtml(ARTIFACTS.chronicle, chronErr);
    }

    var liveCard;
    if (commits && commits.length) {
      var liveRows = commits.map(function (gc) {
        var when = gc.commit && gc.commit.author && gc.commit.author.date
          ? formatUtc(gc.commit.author.date) : "—";
        var msg = gc.commit && gc.commit.message ? gc.commit.message.split("\n")[0] : "—";
        var sha = gc.sha ? gc.sha.slice(0, 7) : "—";
        return '<div class="tl-row"><span class="tl-c">' + escapeHtml(when) + "</span>" +
          '<span class="tl-p">' + escapeHtml(sha) + "</span>" +
          '<span class="tl-t">' + escapeHtml(msg) + "</span></div>";
      }).join("");
      liveCard =
        '<section class="card span"><header class="card-h"><span class="card-t">Operacje bieżące (git, na żywo)</span>' +
        '<span class="card-s">ostatnie ' + commits.length + " commitów · GitHub API</span></header>" +
        '<div class="card-b"><div class="timeline">' + liveRows + "</div>" +
        '<p class="note">Strumień pobierany na żywo z GitHub API przy każdym odświeżeniu — uzupełnia kronikę ' +
        "wyżej o operacje, które nie mają jeszcze swojego wpisu.</p></div></section>";
    } else {
      liveCard = '<section class="card span"><div class="card-b">' +
        apiErrorHtml("lista commitów", commitsErr) + "</div></section>";
    }

    setSectionHTML("history", chronicleCard + liveCard);
  }

  // CTO 2026-07-22 (#8): grupowanie WYLACZNIE po katalogu zrodlowym (fakt
  // strukturalny, wyprowadzalny z r.path) - NIE po temacie/sprincie
  // (wczesniej: "Sprint v0.11.0", "Walidacja v0.10.1" - to byla EDYTORSKA
  // kategoryzacja, ktorej nie da sie wyprowadzic automatycznie z pliku).
  // Etykieta grupy i opis kazdego wpisu (pierwszy H1) pochodza z danych.
  var REPORT_GROUP_LABELS = {
    "": "Katalog główny — raporty sprintów, README, ROADMAP",
    docs: "docs/ — dokumentacja i metodologia",
    publications: "publications/ — profil kompetencji",
    clos_academy: "clos_academy/ — ontologia",
  };

  function renderReports(reports, reportsErr) {
    if (!reports || !reports.length) {
      setSectionHTML("reports", '<section class="card span"><div class="card-b">' +
        apiErrorHtml("lista dokumentów (GitHub API)", reportsErr) + "</div></section>");
      return;
    }
    var byDir = {};
    reports.forEach(function (r) {
      var dir = r.path.indexOf("/") === -1 ? "" : r.path.slice(0, r.path.indexOf("/"));
      if (!byDir[dir]) byDir[dir] = [];
      byDir[dir].push(r);
    });
    var dirOrder = ["", "docs", "publications", "clos_academy"];
    Object.keys(byDir).forEach(function (d) { if (dirOrder.indexOf(d) === -1) dirOrder.push(d); });

    var html = dirOrder.filter(function (d) { return byDir[d] && byDir[d].length; }).map(function (dir) {
      var items = byDir[dir].sort(function (a, b) { return a.path < b.path ? -1 : 1; });
      var rowsHtml = items.map(function (r) {
        var url = "https://github.com/" + OWNER + "/" + REPO + "/blob/" + BRANCH + "/" + r.path;
        var descr = r.ok ? r.title : "błąd wczytania nagłówka";
        return '<div class="rep-row"><a class="rep-f" href="' + url + '" target="_blank" rel="noopener">' +
          escapeHtml(r.path) + "</a><span class=\"rep-d\">" + escapeHtml(descr) + "</span></div>";
      }).join("");
      var label = REPORT_GROUP_LABELS[dir] || (dir + "/");
      return '<section class="card span"><header class="card-h"><span class="card-t">' + escapeHtml(label) + "</span>" +
        '<span class="card-s">' + items.length + " plików · gałąź " + escapeHtml(BRANCH) + "</span></header>" +
        '<div class="card-b"><div class="reports">' + rowsHtml + "</div></div></section>";
    }).join("") +
      '<section class="card span"><div class="card-b">' +
      '<p class="note">Lista odkrywana automatycznie (GitHub API listing katalogu głównego, docs/, ' +
      "publications/, clos_academy/) — opis każdego wpisu to pierwszy nagłówek H1 pliku, nie tekst " +
      "wpisany w panel.js. Nowy plik .md w jednym z tych katalogów pojawia się tu bez zmiany kodu " +
      "panelu. Świadomie NIE rekurencyjne — pomija podkatalogi z danymi run-level " +
      "(publications/*/runs/, execution_package_v0_11/), już pokazane w Lekcjach/Prowenancji.</p></div></section>";
    setSectionHTML("reports", html);
  }

  function updateTopPills(commits, status) {
    var container = document.getElementById("top-pills");
    if (!container) return;
    var head = commits && commits.length ? commits[0].sha.slice(0, 7) : null;
    var ciOk = status && status.ci && status.ci.conclusion === "success";
    var ciColor = status ? (ciOk ? "var(--ok)" : "var(--crit)") : "var(--mut)";
    var ciLabel = status && status.ci ? status.ci.conclusion : "brak danych";
    container.innerHTML =
      '<span class="pill" style="color:var(--chA);border-color:#4FC8E055">Research Grade Infrastructure</span>' +
      '<span class="pill" style="color:var(--mut)">' + escapeHtml(BRANCH) + (head ? "@" + escapeHtml(head) : "") + "</span>" +
      '<span class="pill" style="color:' + ciColor + '" ' + (status ? 'data-dot="1"' : "") + ">" +
      (status ? '<i class="pdot" style="background:' + ciColor + '"></i>' : "") +
      "CI · " + escapeHtml(ciLabel) + "</span>";
  }

  function updateFooter(metadata) {
    var foot = document.getElementById("foot");
    if (!foot) return;
    var ts = metadata && metadata.timestamp ? String(metadata.timestamp).replace("T", " ") : null;
    var refreshed = lastRefreshAt ? formatUtc(lastRefreshAt.toISOString()) : null;
    foot.innerHTML = "Dane: gałąź <code>" + escapeHtml(BRANCH) + "</code>" +
      (ts ? " · bundle L1.1 wygenerowany " + escapeHtml(ts) : "") +
      (refreshed ? " · ostatnie odświeżenie " + escapeHtml(refreshed) : "") +
      " · panel czyta na żywo z <code>raw.githubusercontent.com</code> i odświeża dane automatycznie " +
      "co 10 minut (cache GitHub ~5 min) — żadna liczba nie jest wpisana na sztywno.";
  }

  // SPRINT_v0.11.0.md Zadanie 3: globalny puls, widoczny niezaleznie od
  // aktywnej sekcji - sprint (VERSION -> write_status.py -> status.json),
  // data generacji CI, jej wiek liczony w JS, i commit. ZERO literalow -
  // wszystko z parametru status (reports/status.json); brak -> jawny komunikat, nie cisza.
  function updatePulse(status) {
    var el = document.getElementById("pulse-banner");
    if (!el) return;
    if (!status) {
      el.textContent = "Brak danych CI (reports/status.json niedostępny) — nie da się ustalić wieku danych.";
      return;
    }
    var sprint = status.sprint ? escapeHtml(status.sprint) : "—";
    var dateStr = formatUtc(status.timestamp) || "—";
    var age = ageInfo(status.timestamp);
    var commit = status.commit ? escapeHtml(status.commit.slice(0, 7)) : "—";
    el.innerHTML =
      "<b>Sprint " + sprint + "</b> · dane z CI: " + escapeHtml(dateStr) +
      (age ? ' <span class="' + (age.stale ? "age-stale" : "") + '">(' + escapeHtml(age.text) + ")</span>" : "") +
      " · commit <code>" + commit + "</code>";
  }

  /* ================= orkiestracja ================= */
  function loadAll() {
    lastRefreshAt = new Date();
    var loads = {
      report: fetchJSON(ARTIFACTS.report),
      competency: fetchJSON(ARTIFACTS.competency),
      prereg: fetchJSON(ARTIFACTS.prereg),
      status: fetchJSON(ARTIFACTS.status),
      chronicle: fetchJSON(ARTIFACTS.chronicle),
      population: fetchJSON(ARTIFACTS.population),
      bundles: fetchAllBundles(),
      reports: fetchAllReports(),
      commits: fetchCommits(10),
    };

    var results = {};

    loads.report.then(function (v) { results.report = v; }).catch(function (e) { results.reportError = e; });
    loads.prereg.then(function (v) { results.prereg = v; }).catch(function (e) { results.preregError = e; });
    loads.status.then(function (v) { results.status = v; }).catch(function (e) { results.statusError = e; });
    loads.population.then(function (v) { results.population = v; }).catch(function (e) { results.populationError = e; });
    loads.competency.then(function (v) { results.competency = v; }).catch(function (e) {
      sectionError("competency", ARTIFACTS.competency, e);
      sectionError("genomes", ARTIFACTS.competency, e);
    });
    loads.bundles.then(function (v) { results.bundles = v; }).catch(function (e) { results.bundlesError = e; });
    loads.reports.then(function (v) { results.reports = v; }).catch(function (e) { results.reportsError = e; });
    loads.commits.then(function (v) { results.commits = v; }).catch(function (e) { results.commitsError = e; });

    // Lekcje i wyniki: WYLACZNIE population (re-run konfirmacyjny) - demo
    // report/prereg NIE trafiaja tu juz w ogole, patrz renderProvenance.
    loads.population.catch(function () { return null; }).then(function (population) {
      renderLessons(population, results.populationError);
    });

    loads.competency.then(function (comp) {
      renderCompetency(comp);
      renderGenomes(comp);
    }).catch(function () {});

    Promise.all([
      loads.bundles.catch(function () { return null; }),
      loads.population.catch(function () { return null; }),
      loads.report.catch(function () { return null; }),
      loads.prereg.catch(function () { return null; }),
    ]).then(function (vals) {
      renderProvenance(vals[0], results.bundlesError, vals[1],
        vals[2], vals[3], results.reportError, results.preregError);
    });

    loads.status.then(function (s) { lastStatus = s; renderTests(s, null); updatePulse(s); })
      .catch(function (e) { renderTests(null, e); updatePulse(null); });

    // Historia: kronika (raw) + zywe commity (API) - bledy per zrodlo,
    // czesciowy sukces renderuje to, co sie udalo pobrac.
    var chronState = {};
    Promise.all([
      loads.chronicle.catch(function (e) { chronState.chronErr = e; return null; }),
      loads.commits.catch(function (e) { chronState.commitsErr = e; return null; }),
    ]).then(function (vals) {
      renderHistory(vals[0], vals[1], chronState.chronErr, chronState.commitsErr);
    });

    loads.reports.catch(function () { return null; }).then(function (reports) {
      renderReports(reports, results.reportsError);
    });

    Promise.all([
      loads.competency.catch(function () { return null; }),
      loads.population.catch(function () { return null; }),
      loads.commits.catch(function () { return null; }),
      loads.status.catch(function () { return null; }),
    ]).then(function (vals) {
      renderOverview({
        competency: vals[0], population: vals[1], commits: vals[2], status: vals[3],
        commitsError: results.commitsError, statusError: results.statusError,
      });
      updateTopPills(vals[2], vals[3]);
    });

    // Stopka pokazuje date wygenerowania bundla L1.1 - wczesniej osobny
    // fetch ARTIFACTS.metadata, teraz L1.1 jest jednym z odkrytych bundli
    // (loads.bundles), wiec zero dodatkowego zapytania.
    loads.bundles.then(function (list) {
      var l11 = (list || []).filter(function (b) { return b.ok && b.name === "L1_1_pattern_echo"; })[0];
      updateFooter(l11 ? l11.meta : null);
    }).catch(function () { updateFooter(null); });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initNav();
    loadAll();
    // Pelne odswiezenie wszystkich danych co 10 minut...
    setInterval(loadAll, REFRESH_MS);
    // ...a sam WIEK danych w pulsie przeliczany co minute z juz pobranego
    // statusu (zero fetchu; guard - nie nadpisuj komunikatu bledu, gdy
    // status jeszcze/w ogole nie zostal pobrany).
    setInterval(function () { if (lastStatus) updatePulse(lastStatus); }, 60 * 1000);
  });
})();
