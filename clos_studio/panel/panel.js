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
    // SPRINT v0.11.0 KROK 1 P2 (CTO 2026-07-26): gotowy raport .md
    // wygenerowany przez scripts/report_composer.py z danych re-runu.
    // Przycisk "Generuj raport do analizy" tylko go FETCHUJE i pobiera -
    // ZERO skladania raportu w JS (jedno zrodlo prawdy = generator Python).
    report_md: "reports/rerun_full_report_v0_11_0.md",
    // Odmrozenie sekcji PC-001 (zadanie uzytkownika): panel.js mial ZERO
    // odwolan do calego programu PC-001 (zweryfikowane grepem przed ta
    // zmiana) - spec i baseline sa jedynym zrodlem prawdy o stanie
    // protokolu/bramek, wiec czytane bezposrednio, tak jak reszta ARTIFACTS.
    spec: "SPECYFIKACJA_KANONICZNA_PC_001.json",
    baseline_hash: "execution_package_v0_11/hashes/pc_001_baseline_hash.txt",
    power_analysis: "publications/power_analysis_PC_001.json",
    // NAPRAWA LIMITU API (zadanie uzytkownika): dokumenty/piloci/bundle byly
    // odkrywane listowaniem katalogow GitHub API z kazdej przegladarki przy
    // kazdym ladowaniu (~8 zapytan x auto-refresh = limit 60/h wyczerpywany).
    // Ten plik jest generowany RAZ w CI (scripts/generate_artifacts_index.py,
    // ten sam wzorzec co status: powyzej / write_status.py) - panel czyta go
    // przez raw fetch (fetchJSON, bez limitu API) zamiast listowac katalogi
    // sam. Auto-discovery ZACHOWANE, przeniesione o warstwe nizej (do CI).
    artifacts_index: "reports/artifacts_index.json",
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
  var SECTIONS = ["overview", "history", "lessons", "competency", "genomes", "provenance", "pc001", "tests", "reports"];
  var SECTION_LABELS = {
    overview: "Przegląd", history: "Historia", lessons: "Lekcje i wyniki", competency: "Profil kompetencji",
    genomes: "Porównanie genomów", provenance: "Prowenancja", pc001: "PC-001", tests: "Testy i CI", reports: "Raporty",
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

  /* ================= daty tresci (odmrozenie: daty wszedzie) =================
   * Rozroznienie DWOCH dat, celowo nie mieszanych (decyzja uzytkownika):
   *   DATA TRESCI  - kiedy artefakt POWSTAL, czytana Z WNETRZA pliku. Glowna.
   *   DATA COMMITA - kiedy plik OSTATNIO ZMIENIONO w repo (GitHub API,
   *     patrz fetchLastCommitDate) - uzywana WYLACZNIE tam, gdzie rozjazd
   *     miedzy "tresc powstala X" a "plik dotkniety pozniej" ma znaczenie
   *     (Bramki - patrz renderPc001Gates) - NIE przy kazdym dokumencie, bo
   *     kosztowaloby to jedno zapytanie API na plik (~60+ plikow w Raportach/
   *     PC-001 razem) i przebilo limit 60/h bez autoryzacji z marginesem
   *     rownym zero. Poza Bramkami pokazujemy WYLACZNIE date tresci.
   */

  // Kolejnosc = priorytet, gdy artefakt ma wiecej niz jedno pole - "timestamp"
  // przed "bundled_at" u bogatych bundli (patrz renderBundleCard: timestamp
  // to moment ZAMROZENIA bundla, bundled_at to moment spakowania - starszy
  // fakt bije mlodszy, gdy oba istnieja). Lista zamknieta i jawna - ZERO
  // zgadywania nazwy pola spoza niej (task: "jesli pole daty nie istnieje -
  // 'data nieznana', nie zgadywanie").
  var CONTENT_DATE_FIELDS = ["generated_at", "timestamp", "date", "bundled_at", "preregistration_date"];

  function extractJsonContentDate(obj) {
    if (!obj) return null;
    for (var i = 0; i < CONTENT_DATE_FIELDS.length; i++) {
      var v = obj[CONTENT_DATE_FIELDS[i]];
      if (v) return v;
    }
    return null;
  }

  // Naglowek dokumentow protokolu ma linie "**Data:** 2026-07-28 · ..." -
  // pierwszy token po dwukropku, przed spacja/interpunktem. Fallback: data
  // zaszyta w nazwie pliku (np. "..._ANEKS_1_2026-07-28.md") - dokladnie
  // tak, jak nazwano to w zadaniu. Kolejnosc: naglowek MA PIERWSZENSTWO -
  // to jest tresc dokumentu, nazwa pliku to tylko etykieta.
  var MD_DATE_HEADER_RE = /\*\*Data:\*\*\s*(\S+)/;
  var FILENAME_DATE_RE = /(\d{4}-\d{2}-\d{2})/;

  function extractMdContentDate(text, filename) {
    var m = MD_DATE_HEADER_RE.exec(text || "");
    if (m) return m[1];
    var fm = FILENAME_DATE_RE.exec(filename || "");
    if (fm) return fm[1];
    return null;
  }

  // Czysta data "2026-07-28" (bez czasu) pokazana WPROST - formatUtc()
  // doklejalaby "00:00 UTC", ktorego w zrodle nie ma (fabrykowalby precyzje).
  function formatContentDate(raw) {
    if (!raw) return null;
    if (/^\d{4}-\d{2}-\d{2}$/.test(raw)) return raw;
    return formatUtc(raw) || raw;
  }

  // Znacznik "data nieznana" jest CELOWO widoczny (nie pusty string) - luka
  // w artefakcie ma byc widoczna na ekranie, nie cicho pominieta (ten sam
  // duch co "cisza jest gorsza niz blad", SPRINT_v0.11.0.md).
  function dateBadgeHtml(raw) {
    var formatted = formatContentDate(raw);
    if (!formatted) return '<span class="leg-note" style="color:var(--mut)">data nieznana</span>';
    var age = ageInfo(raw);
    return '<span class="leg-note">' + escapeHtml(formatted) +
      (age ? ' <span class="' + (age.stale ? "age-stale" : "") + '">(' + escapeHtml(age.text) + ")</span>" : "") +
      "</span>";
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

  // NAPRAWA LIMITU API (zgloszenie uzytkownika): auto-discovery dokumentow/
  // pilotow/bundli dzialalo dotad przez listowanie katalogow GitHub API Z
  // PRZEGLADARKI kazdego uzytkownika (~8 zapytan/ladowanie x auto-refresh co
  // 10 min = limit 60/h bez autoryzacji wyczerpywany, listy znikaly).
  // Rozwiazanie: ten sam wzorzec co reports/status.json - odkrywanie
  // PRZENIESIONE do CI (scripts/generate_artifacts_index.py, listing z
  // systemu plikow, uruchamiany raz na commit), panel czyta JEDEN
  // wygenerowany plik przez raw.githubusercontent (bez limitu API), zamiast
  // wielu zapytan API na kazde ladowanie. Auto-discovery jest ZACHOWANE -
  // przeniesione o warstwe nizej, nie zlikwidowane: nowy dokument/pilot w
  // repo pojawia sie w indeksie przy najblizszym commicie CI, bez zadnej
  // zmiany w panel.js. Ksztalt kazdej pozycji w indeksie jest CELOWO
  // identyczny z tym, co dawniej zwracaly fetchMdReportsIn()/
  // fetchAllPilotResults()/fetchAllBundles() (API) - wiec renderReports/
  // renderPc001Documents/renderPc001PilotResults/renderProvenance ponizej
  // NIE WYMAGAJA zadnej zmiany, tylko zrodlo danych sie zmienilo.
  //
  // Historia (fetchCommits) ZOSTAJE na GitHub API - to jedyna rzecz, ktorej
  // statyczny indeks nie moze zastapic (strumien biezacych commitow), i to
  // JEDNO zapytanie/ladowanie, nie osiem.
  function fetchArtifactsIndex() {
    return fetchJSON(ARTIFACTS.artifacts_index);
  }

  function fetchCommits(limit) {
    var url = API_BASE + "/commits?sha=" + BRANCH + "&per_page=" + (limit || 10);
    return fetch(url).then(function (res) {
      if (!res.ok) throw apiHttpError(res, url);
      return res.json();
    });
  }

  // DATA COMMITA dla jednego pliku (patrz blok komentarza przy dateBadgeHtml)
  // - jedno zapytanie API. Uzywane CELOWO oszczednie: tylko tam, gdzie
  // rozjazd tresc/commit ma znaczenie interpretacyjne (Bramki), NIE dla
  // kazdego z ~60 dokumentow w Raportach/PC-001 (przebilo by limit 60/h).
  function fetchLastCommitDate(path) {
    var url = API_BASE + "/commits?path=" + encodeURIComponent(path) + "&sha=" + BRANCH + "&per_page=1";
    return fetch(url).then(function (res) {
      if (!res.ok) throw apiHttpError(res, url);
      return res.json();
    }).then(function (commits) {
      if (!commits || !commits.length) return null;
      var latest = commits[0];
      return (latest.commit && latest.commit.author && latest.commit.author.date) || null;
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

    // Odmrozenie: data wygenerowania pliku populacyjnego. Zgloszenie, nie
    // naprawa: population_validation_v0_11_0.json NIE MA zadnego pola daty
    // (generated_at/timestamp/date) - "data nieznana" ponizej jest wiec
    // realnym stanem pliku, nie usterka tej funkcji. Luka do wypelnienia w
    // generatorze (clos_scientist/...), nie w panelu.
    var dateNote = '<p class="prose" style="grid-column:1/-1">Data wygenerowania: ' +
      dateBadgeHtml(extractJsonContentDate(population)) + "</p>";

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

    setSectionHTML("lessons", dateNote + statusNote + (cards || '<p class="prose" style="grid-column:1/-1">Plik populacyjny nie zawiera żadnej lekcji.</p>'));
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
      // Odmrozenie: data prerejestracji (prereg.preregistration_date) - jedyne
      // pole daty w tej parze artefaktow. `report` (reports/academy/
      // L1_1_pattern_echo.json) NIE MA zadnego pola daty - zgloszenie, nie luka
      // tej funkcji.
      '<div><span>Data (prereg)</span><b>' + dateBadgeHtml(extractJsonContentDate(prereg)) + "</b></div>" +
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
      // CTO 2026-07-22 (P0 + panel): genome_comparison od re-runu
      // konfirmacyjnego (23 genomy) niesie pary FDR (Welch+BH q=0.05) +
      // ANOVA surowe - NIE pojedynczy Cohen's d miedzy dwoma genomami
      // (ten koncept nie ma sensu przy 23 genomach: KTORA para?). Ten sam
      // wzorzec co sekcja Lekcje (#3) - pary FDR, nie fabrykowany efekt
      // dla dowolnie wybranej pary. Pola czytane BEZPOSREDNIO jako
      // c.genome_comparison.X (bez aliasu do lokalnej zmiennej) - inaczej
      // scripts/validate_panel.py (CHAIN_RE) nie widzi ich i przestaje
      // pilnowac, ze te pola istnieja w competency_profile.json.
      var dHtml = (c.genome_comparison && c.genome_comparison.n_pairs)
        ? '<div class="crow-d">Pary FDR (Welch+BH, q=0.05): <code>' + c.genome_comparison.n_fdr_significant_q_0_05 +
          "/" + c.genome_comparison.n_pairs + "</code>" +
          (c.genome_comparison.anova_computable ? " · ANOVA surowe f=" + fmtNum(c.genome_comparison.anova_f, 4) : "") + "</div>"
        : "";
      body = '<div class="crow-body">' + gRows + dHtml + "</div>";
      if (state === "degenerate") {
        body += '<div class="crow-warn">⚠ co najmniej jeden genom ma <code>ci95_valid=false</code> — ' +
          "policzone, ale bez informacji o wariancji między seedami.</div>";
      }
    } else {
      body = '<div class="crow-gap">brak lekcji mierzącej to pojęcie (status: <code>insufficient_data</code>)</div>';
    }

    return '<div class="crow ' + state + '"><div class="crow-head"><span class="crow-k">' + escapeHtml(c.concept) + "</span>" +
      '<span class="pill" style="color:' + color + ";border-color:" + color + '55">' + label +
      (c.source_lesson ? " · " + escapeHtml(c.source_lesson) : "") + "</span></div>" + body + "</div>";
  }

  // SPRINT_v0.11.0.md Zadanie 3: banery cyklu zycia danych dla sekcji, ktore
  // czytaja competency_profile.json - CZYTA pola juz obecne
  // (comp.generated_at, comp.dataset_status), nie liczy/nie zgaduje niczego.
  // Dwa banery moga wystapic razem: dane SA zywe (maja generated_at) I
  // JEDNOCZESNIE oznaczone Exploratory/Confirmatory - to nie sprzecznosc,
  // to dwa rozne pytania (swiezosc artefaktu vs. status naukowy).
  // CTO 2026-07-22 (P0): etykieta drugiego banera WARUNKOWA - profil
  // przeszedl z Exploratory (n=10) na CONFIRMATORY (re-run 23 genomy), wiec
  // baner musi za nim, inaczej pokazywalby sprzeczne "Exploratory Dataset:
  // CONFIRMATORY (NIE Exploratory)". Prefiks czytany z tresci dataset_status
  // (pierwsze slowo), nie zgadywany.
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
      // CONFIRMATORY uzywa bazowej klasy .datastate (neutralny akcent) - NIE
      // "-exploratory" (pomaranczowy = ostrzezenie "jeszcze nie potwierdzone",
      // falszywe dla danych konfirmacyjnych) i NIE "-live" (zielony,
      // zarezerwowany dla banera swiezosci wyzej). Zero nowej klasy CSS.
      var isConfirmatory = /^\s*CONFIRMATORY/i.test(comp.dataset_status);
      var label = isConfirmatory ? "Confirmatory Dataset:" : "Exploratory Dataset:";
      var cls = isConfirmatory ? "" : " datastate-exploratory";
      html += '<div class="datastate' + cls + '">' +
        "<b>" + label + "</b> " + escapeHtml(comp.dataset_status) + "</div>";
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

  // CTO 2026-07-22 (P0 + panel, ten sam wzorzec co Lekcje #3): sekcja
  // Genomow POKAZYWALA pojedyncza pare (default vs highly_plastic) +
  // Cohen's d - nie ma to sensu przy 23 genomach (ktora para z 253?).
  // Teraz: jedna linia na koncept, z JUZ POLICZONYCH pol competency_profile.json
  // (classification/valid_rate/n_genomes_valid/n_genomes_total/genome_comparison
  // z pairs FDR + ANOVA surowe) - zero fabrykowanego effect size dla
  // dowolnie wybranej pary genomow.
  // Pola genome_comparison czytane BEZPOSREDNIO jako c.genome_comparison.X
  // (bez aliasu) - patrz komentarz w renderConceptRow: alias ukrylby je
  // przed validate_panel.py (CHAIN_RE sledzi tylko dosl. lancuchy z rootow).
  function renderGenomeComparisonRow(c) {
    var pairsText = (c.genome_comparison && c.genome_comparison.n_pairs)
      ? c.genome_comparison.n_fdr_significant_q_0_05 + "/" + c.genome_comparison.n_pairs + " par (FDR q=0.05)"
      : "—";
    var anovaText = (c.genome_comparison && c.genome_comparison.anova_computable) ? "f=" + fmtNum(c.genome_comparison.anova_f, 4) : "—";
    var nTotal = c.n_genomes_total != null ? c.n_genomes_total : Object.keys(c.genomes || {}).length;
    return "<tr><td>" + escapeHtml(c.concept) + "</td>" +
      "<td>" + escapeHtml(c.classification || "—") + "</td>" +
      "<td>" + fmtNum(c.valid_rate, 2) + "</td>" +
      "<td>" + (c.n_genomes_valid != null ? c.n_genomes_valid : "—") + "/" + nTotal + "</td>" +
      "<td>" + escapeHtml(pairsText) + "</td>" +
      "<td>" + escapeHtml(anovaText) + "</td></tr>";
  }

  function renderGenomes(comp) {
    if (!comp) return;
    var rows = classifyConcepts(comp).valid;
    var genomeCount = rows.length ? Object.keys(rows[0].genomes).length : 0;

    var trHtml = rows.map(renderGenomeComparisonRow).join("");

    var html =
      '<section class="card span"><header class="card-h"><span class="card-t">Porównanie genomów</span>' +
      '<span class="card-s">' + genomeCount + " genomów · pary FDR (Welch+BH, q=0.05) i ANOVA surowe · re-run konfirmacyjny</span></header>" +
      '<div class="card-b"><table class="tbl"><thead><tr><th>Pojęcie</th><th>Classification</th>' +
      "<th>valid_rate</th><th>n_valid/n_total</th><th>Pary FDR</th><th>ANOVA f (surowe)</th></tr></thead>" +
      "<tbody>" + (trHtml || '<tr><td colspan="6">Brak pojęć z ważnym CI95.</td></tr>') + "</tbody></table>" +
      '<p class="note">Liczby wprost z <code>publications/competency_profile.json</code> (' + genomeCount +
      " genomów, re-run konfirmacyjny) — zero fabrykowanego Cohen's d dla dowolnie wybranej pary. " +
      "Interpretacja (VALIDATED/EXPERIMENTAL) jest w <code>docs/METRIC_STATUS_TABLE.md</code>.</p></div></section>";
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
      // Odmrozenie (#1e "sprawdz czy wszystkie karty maja daty"): bundle
      // legacy MA pole "bundled_at" (zweryfikowane w plikach EXP-*), po
      // prostu nie bylo dotad pokazywane - to jest dokladnie ta luka.
      return '<div class="leg-row"><code>' + escapeHtml(legacy.experiment_id || item.name) + "</code>" +
        '<span class="pill" style="color:var(--mut);border-color:#78879A55">' + escapeHtml(legacy.provenance) + "</span>" +
        '<span class="leg-note">git_commit: ' + (legacy.git_commit ? escapeHtml(truncHash(legacy.git_commit)) : "pusty (nie zgadywany)") + "</span>" +
        dateBadgeHtml(extractJsonContentDate(legacy)) + "</div>";
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
      // Odmrozenie: brak pola daty w population_validation_v0_11_0.json
      // (zweryfikowane) - "data nieznana" tutaj jest zgloszeniem stanu pliku,
      // nie usterka tej karty (patrz ta sama uwaga w renderLessons).
      "<div><dt>data treści</dt><dd>" + dateBadgeHtml(extractJsonContentDate(population)) + "</dd></div>" +
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
          '<span class="card-s">oznaczone, prowenancja nie fabrykowana</span></header>' +
          '<div class="card-b"><div class="legacy">' + sparse.map(renderBundleCard).join("") + "</div></div></section>"
        : "";
      bundlesHtml = richCards + sparseCard;
    } else {
      // Zrodlem jest teraz raw fetch indeksu CI (nie GitHub API), wiec blad
      // to brak/uszkodzony artefakt, nie limit zapytan - missingArtifactHtml.
      bundlesHtml = missingArtifactHtml(ARTIFACTS.artifacts_index, bundlesError);
    }

    var demoCard = renderLegacyDemoCard(demoReport, demoPrereg, demoReportError, demoPreregError);

    setSectionHTML("provenance", hardHaltCard + bundlesHtml + demoCard);
  }

  /* ================= sekcja PC-001 (odmrożenie) =================
   * Zasada jak wszędzie indziej w tym pliku: panel POKAZUJE dane, NIE
   * interpretuje (interpretacja żyje w SPECYFIKACJA_KANONICZNA_PC_001.md).
   * Zero list warunków/dokumentów wpisanych na sztywno - wszystko z
   * Object.keys()/GitHub API listing, jak sekcje Lekcje (#3) i Raporty (#8).
   */

  function stripMd(s) {
    return String(s == null ? "" : s).replace(/\*\*/g, "").replace(/`/g, "").replace(/^\s+|\s+$/g, "");
  }

  // Reguła decyzyjna żyje w §2.6 Specyfikacji (adres strukturalny dokumentu,
  // ta sama kategoria co ARTIFACTS.report/competency itd. - "wolno" pod C-001,
  // patrz SPECYFIKACJA_KANONICZNA_PC_001.md §0.2). Tabela odnaleziona PO
  // KSZTAŁCIE (kolumny "Warunek" + "Status"), nie po pozycji w liście bloków -
  // §2.6 ma DWIE tabele (reguła + zastrzeżenia wiążące), z różnymi kolumnami.
  function findDecisionRuleTable(spec) {
    var sections = (spec && spec.sections) || [];
    var section = null;
    for (var i = 0; i < sections.length; i++) {
      if (sections[i].id === "2.6") { section = sections[i]; break; }
    }
    if (!section) return null;
    var blocks = section.blocks || [];
    for (var j = 0; j < blocks.length; j++) {
      var b = blocks[j];
      if (b.type === "table" && b.columns && b.columns.indexOf("Warunek") !== -1 && b.columns.indexOf("Status") !== -1) {
        return b;
      }
    }
    return null;
  }

  function renderPc001DecisionRule(spec, specErr) {
    if (!spec) return missingArtifactHtml(ARTIFACTS.spec, specErr);
    var table = findDecisionRuleTable(spec);
    if (!table) {
      return missingArtifactHtml(ARTIFACTS.spec + " §2.6 (tabela reguły decyzyjnej)", null);
    }
    var rows = table.rows || [];
    var suspended = rows.filter(function (r) { return stripMd(r["Status"]) !== "aktywny"; });
    var suspendedHtml = suspended.map(function (r) {
      return '<div class="leg-row"><code>' + escapeHtml(stripMd(r["Warunek"])) + "</code>" +
        '<span class="pill" style="color:var(--warn);border-color:#F2B04955">' +
        escapeHtml(stripMd(r["Status"])) + "</span></div>";
    }).join("");

    return '<section class="card span"><header class="card-h"><span class="card-t">' +
      escapeHtml(spec.title || "Specyfikacja Kanoniczna PC-001") + "</span>" +
      '<span class="card-s">reguła decyzyjna: ' + (rows.length - suspended.length) + "/" + rows.length +
      " warunków aktywnych · " + (spec.sections ? spec.sections.length : "—") + " sekcji w dokumencie</span></header>" +
      '<div class="card-b"><div class="legacy">' +
      (suspendedHtml || '<p class="prose">Wszystkie warunki reguły decyzyjnej mają status „aktywny".</p>') +
      "</div>" +
      '<p class="note">Pełna lista ' + rows.length + " warunków (w tym aktywnych) w <code>" +
      escapeHtml(ARTIFACTS.spec) + "</code> §2.6 — panel pokazuje tylko warunki o statusie innym niż " +
      '„aktywny"; nazwa i status wprost z tabeli, interpretacja (dlaczego) żyje w Specyfikacji, ' +
      "nie tutaj.</p></div></section>";
  }

  // Blok komentarza "# STATUS: ..." w pc_001_baseline_hash.txt może się
  // rozciągać na kilka linii (jedna linia obcięłaby zdanie w połowie) -
  // ten sam algorytm co baseline_status_at() w
  // scripts/generate_canonical_parameters_report.py, tylko po stronie JS,
  // bo panel nie ma zaplecza Pythona - czyta surowy tekst przez fetchText().
  function parseBaselineStatus(text) {
    if (!text) return null;
    var lines = text.split("\n");
    var collected = [];
    var collecting = false;
    for (var i = 0; i < lines.length; i++) {
      var stripped = lines[i].replace(/^\s+|\s+$/g, "");
      if (!collecting) {
        if (stripped.indexOf("# STATUS:") === 0) {
          collecting = true;
          collected.push(stripped.slice("# STATUS:".length).replace(/^\s+/, ""));
        }
        continue;
      }
      if (stripped === "#" || stripped === "") break;
      if (stripped.indexOf("#") === 0) {
        collected.push(stripped.replace(/^#+\s*/, ""));
      } else {
        break;
      }
    }
    return collected.length ? collected.join(" ") : null;
  }

  // "Pilot Final" nie ma dziś jeszcze artefaktu (D-031, znalezisko §6.4
  // Specyfikacji: parametry Pilota Final nieudokumentowane w repo) i nie ma
  // ustalonej konwencji nazewnictwa pliku (istniejące piloty B4a/B4a-2/W-01
  // nazywają się wg mierzonej wielkości: "pilot_W_early_red_...",
  // "w01_recovery_1_..." - żaden nie zawiera słowa "final"). Zero-hardkodowany
  // sposób odróżnienia "jest" od "brak": szukamy pliku, którego NAZWA albo
  // pole "purpose" zawiera "final" (bez rozróżniania wielkości liter) - gdy
  // Pilot Final faktycznie powstanie, ujawni się przez tę samą, ogólną regułę,
  // bez zmiany w tym pliku. Do tego czasu poprawnie pokazuje "brak".
  function findPilotFinalArtifact(pilotResults) {
    var items = pilotResults || [];
    for (var i = 0; i < items.length; i++) {
      var item = items[i];
      var name = item.path.slice(item.path.lastIndexOf("/") + 1);
      var purpose = (item.ok && item.data && item.data.purpose) || "";
      if (/final/i.test(name) || /final/i.test(purpose)) return item;
    }
    return null;
  }

  // Bramki to JEDYNE miejsce w tym pliku, gdzie dokladamy DATE COMMITA
  // (fetchLastCommitDate) obok daty tresci - patrz blok komentarza przy
  // dateBadgeHtml co do tego, dlaczego nie robimy tego wszedzie. baseline_hash.txt
  // to plik tekstowy z prozą (nie JSON/naglowek MD), wiec nie ma "daty tresci"
  // w rozumieniu §2 zadania - jedyny dostepny fakt to KIEDY PLIK OSTATNIO
  // ZMIENIONO, jawnie podpisany jako taki (nie udajemy, ze to data tresci).
  function renderPc001Gates(baselineText, baselineErr, baselineCommitDate, powerAnalysisExists, pilotResults) {
    var baselineStatus = parseBaselineStatus(baselineText);
    var baselineComputed = !!baselineStatus && !/^TBD\b/i.test(baselineStatus);
    var baselineVal = baselineStatus ? escapeHtml(baselineStatus) : (baselineErr ? "błąd odczytu" : "—");
    var baselineCommitHtml = baselineCommitDate
      ? " <span class=\"leg-note\">(ostatnia zmiana pliku: " + escapeHtml(formatContentDate(baselineCommitDate)) + ")</span>"
      : "";
    var pilotFinal = findPilotFinalArtifact(pilotResults);
    var pilotFinalDateHtml = pilotFinal ? " " + dateBadgeHtml(extractJsonContentDate(pilotFinal.data)) : "";
    return '<section class="card span"><header class="card-h"><span class="card-t">Bramki przed startem</span>' +
      '<span class="card-s">Pilot Final → B4b Monte Carlo → B5 baseline → B6 → START</span></header>' +
      '<div class="card-b"><div class="kv">' +
      '<div><span>Pilot Final</span><b style="color:' + (pilotFinal ? "var(--ok)" : "var(--mut)") + '">' +
      (pilotFinal ? "istnieje (" + escapeHtml(pilotFinal.path) + ")" : "brak") + pilotFinalDateHtml + "</b></div>" +
      '<div><span>PC_001_BASELINE</span><b style="color:' + (baselineComputed ? "var(--ok)" : "var(--warn)") +
      '">' + baselineVal + baselineCommitHtml + "</b></div>" +
      '<div><span>Artefakt analizy mocy</span><b style="color:' +
      (powerAnalysisExists ? "var(--ok)" : "var(--mut)") + '">' +
      (powerAnalysisExists ? "istnieje" : "nie istnieje") + "</b></div></div>" +
      '<p class="note">Status <code>PC_001_BASELINE</code> czytany wprost z <code>' +
      escapeHtml(ARTIFACTS.baseline_hash) + "</code> (blok komentarza <code># STATUS:</code>) plus data " +
      "ostatniego commita dotykającego ten plik (GitHub API), " +
      "istnienie artefaktu mocy sprawdzone przez pobranie <code>" + escapeHtml(ARTIFACTS.power_analysis) +
      "</code>, Pilot Final wykryty przez dopasowanie „final” w nazwie pliku/polu <code>purpose</code> " +
      "wśród <code>reports/pilot/*.json</code> (data tam, gdzie istnieje: pole treści pliku) — panel nic " +
      "tu nie liczy ani nie zgaduje.</p></div></section>";
  }

  // Dokumenty PC-001 to PODZBIÓR listy już pobranej dla sekcji Raporty
  // (loads.reports) - zero dodatkowego zapytania do API. Filtr po nazwie
  // pliku (nie po katalogu), bo prerejestracje/aneksy leżą w publications/,
  // a Specyfikacja Kanoniczna w katalogu głównym.
  var PC001_DOC_NAME_RE = /^(SPECYFIKACJA_KANONICZNA_PC_001|preregistration_PC_001|specyfikacja_W2)/;

  function renderPc001Documents(reports, reportsErr) {
    if (!reports) {
      // Zrodlem jest teraz raw fetch indeksu CI (nie GitHub API) - brak
      // artefaktu, nie limit zapytan.
      return missingArtifactHtml(ARTIFACTS.artifacts_index, reportsErr);
    }
    var docs = reports.filter(function (r) {
      var base = r.path.slice(r.path.lastIndexOf("/") + 1);
      return PC001_DOC_NAME_RE.test(base);
    }).sort(function (a, b) { return a.path < b.path ? -1 : 1; });

    var noDate = docs.filter(function (r) { return !r.date; }).length;
    var rowsHtml = docs.map(function (r) {
      var url = "https://github.com/" + OWNER + "/" + REPO + "/blob/" + BRANCH + "/" + r.path;
      var descr = r.ok ? r.title : "błąd wczytania nagłówka";
      return '<div class="rep-row"><a class="rep-f" href="' + url + '" target="_blank" rel="noopener">' +
        escapeHtml(r.path) + "</a><span class=\"rep-d\">" + escapeHtml(descr) + "</span>" +
        dateBadgeHtml(r.date) + "</div>";
    }).join("");

    return '<section class="card span"><header class="card-h"><span class="card-t">Dokumenty PC-001</span>' +
      '<span class="card-s">' + docs.length + " plików (.md/.json) · prerejestracja, aneksy, Specyfikacja Kanoniczna, W2" +
      (noDate ? " · " + noDate + " bez daty" : "") + "</span></header>" +
      '<div class="card-b"><div class="reports">' +
      (rowsHtml || '<p class="prose">Brak dopasowanych dokumentów.</p>') + "</div></div></section>";
  }

  function renderPc001PilotResults(items, itemsErr) {
    if (!items) {
      // Zrodlem jest teraz raw fetch indeksu CI (nie GitHub API) - brak
      // artefaktu, nie limit zapytan.
      return missingArtifactHtml(ARTIFACTS.artifacts_index, itemsErr);
    }
    var rows = items.map(function (item) {
      if (!item.ok) {
        return '<div class="leg-row"><code>' + escapeHtml(item.path) + "</code>" +
          '<span class="leg-note" style="color:var(--crit)">nie wczytano</span></div>';
      }
      var d = item.data || {};
      var neverPill = d.NEVER_FOR_INFERENCE
        ? '<span class="pill" style="color:var(--crit);border-color:#F0655A55">NEVER_FOR_INFERENCE</span>' : "";
      return '<div class="leg-row"><code>' + escapeHtml(item.path) + "</code>" + neverPill +
        (d.purpose ? '<span class="leg-note">' + escapeHtml(d.purpose) + "</span>" : "") +
        (d.recorded_quantity ? '<span class="leg-note">recorded_quantity: ' + escapeHtml(d.recorded_quantity) + "</span>" : "") +
        dateBadgeHtml(extractJsonContentDate(d)) +
        "</div>";
    }).join("");

    return '<section class="card span"><header class="card-h"><span class="card-t">Wyniki pilotów</span>' +
      '<span class="card-s">' + items.length + " plików · reports/pilot/</span></header>" +
      '<div class="card-b"><div class="legacy">' +
      (rows || '<p class="prose">Brak plików w reports/pilot/.</p>') + "</div>" +
      '<p class="note">Plik z jawnym <code>NEVER_FOR_INFERENCE</code> NIE jest wynikiem konfirmacyjnym — ' +
      "gwarancja ślepoty pilota (B4 §2 → „Wzmocnienie”, patrz też Specyfikacja Kanoniczna §2.11). Panel " +
      "pokazuje istnienie pliku i zadeklarowane pola <code>purpose</code>/<code>recorded_quantity</code>, " +
      "nie interpretuje wartości w środku.</p></div></section>";
  }

  function renderPc001(ctx) {
    var html = renderPc001DecisionRule(ctx.spec, ctx.specError) +
      renderPc001Gates(ctx.baselineText, ctx.baselineError, ctx.baselineCommitDate, ctx.powerAnalysisExists, ctx.pilotResults) +
      renderPc001Documents(ctx.reports, ctx.reportsError) +
      renderPc001PilotResults(ctx.pilotResults, ctx.pilotResultsError);
    setSectionHTML("pc001", html);
  }

  function renderTests(status, statusErr) {
    if (!status) {
      setSectionHTML("tests", missingArtifactHtml(ARTIFACTS.status, statusErr));
      return;
    }

    var tests = status.tests || {};
    var ci = status.ci || {};
    var validators = status.validators || {};

    // NAPRAWA CI-01/CI-01B (zgloszenia uzytkownika/audytora 2026-08-10/11):
    // "N passed / green" wygladalo identycznie niezaleznie od tego, ile
    // testow cicho zniknelo (importorskip NA POZIOMIE MODULU - brak scipy
    // dawal "1 skipped" w CI, nie "60 skipped", bo caly modul to jedna
    // pozycja kolekcji - sama liczba pominietych nie wystarczala jako
    // widocznosc). write_status.py liczy teraz TAKZE "collected" (z
    // niezaleznego przebiegu pytest --collect-only) i WYLICZA tests.status
    // (nie literal "green"): "red" gdy failed/errors>0, "unknown" gdy
    // collected nie do odczytania lub nie zgadza sie z suma kategorii (BRAK
    // ODCZYTU != ZERO), "warning" gdy skipped>0, "green" tylko gdy wszystko
    // policzone i zgadza sie. Panel pokazuje wprost, co przyszlo w polu.
    var skipped = tests.skipped || 0;
    var failed = tests.failed || 0;
    var errors = tests.errors || 0;
    var testsStatus = tests.status;
    var subParts = [];
    if (tests.collected != null) subParts.push("collected " + tests.collected);
    if (skipped) subParts.push(skipped + " skipped");
    if (failed) subParts.push(failed + " failed");
    if (errors) subParts.push(errors + " errors");
    if (testsStatus === "unknown") subParts.push("status: nieznany (rozjazd/brak danych collected)");
    var pytestSub = subParts.length ? "passed · " + subParts.join(" · ") : "passed";
    var testsColor = { green: "var(--ok)", warning: "var(--warn)", unknown: "var(--warn)", red: "var(--crit)" }[testsStatus] || "var(--crit)";
    var tiles = [
      { l: "pytest", val: tests.passed != null ? String(tests.passed) : "—",
        sub: pytestSub, c: testsColor },
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
    "reports/pilot": "reports/pilot/ — noty pilota PC-001 (dane liczbowe: sekcja PC-001)",
  };

  function renderReports(reports, reportsErr) {
    if (!reports || !reports.length) {
      // Zrodlem jest teraz raw fetch indeksu CI (nie GitHub API) - brak
      // artefaktu, nie limit zapytan.
      setSectionHTML("reports", missingArtifactHtml(ARTIFACTS.artifacts_index, reportsErr));
      return;
    }
    var byDir = {};
    reports.forEach(function (r) {
      var dir = r.path.indexOf("/") === -1 ? "" : r.path.slice(0, r.path.indexOf("/"));
      if (!byDir[dir]) byDir[dir] = [];
      byDir[dir].push(r);
    });
    var dirOrder = ["", "docs", "publications", "clos_academy", "reports/pilot"];
    Object.keys(byDir).forEach(function (d) { if (dirOrder.indexOf(d) === -1) dirOrder.push(d); });

    var html = dirOrder.filter(function (d) { return byDir[d] && byDir[d].length; }).map(function (dir) {
      var items = byDir[dir].sort(function (a, b) { return a.path < b.path ? -1 : 1; });
      var rowsHtml = items.map(function (r) {
        var url = "https://github.com/" + OWNER + "/" + REPO + "/blob/" + BRANCH + "/" + r.path;
        var descr = r.ok ? r.title : "błąd wczytania nagłówka";
        return '<div class="rep-row"><a class="rep-f" href="' + url + '" target="_blank" rel="noopener">' +
          escapeHtml(r.path) + "</a><span class=\"rep-d\">" + escapeHtml(descr) + "</span>" +
          dateBadgeHtml(r.date) + "</div>";
      }).join("");
      var label = REPORT_GROUP_LABELS[dir] || (dir + "/");
      return '<section class="card span"><header class="card-h"><span class="card-t">' + escapeHtml(label) + "</span>" +
        '<span class="card-s">' + items.length + " plików · gałąź " + escapeHtml(BRANCH) + "</span></header>" +
        '<div class="card-b"><div class="reports">' + rowsHtml + "</div></div></section>";
    }).join("") +
      '<section class="card span"><div class="card-b">' +
      '<p class="note">Lista odkrywana automatycznie w CI (scripts/generate_artifacts_index.py, listing ' +
      "katalogu głównego, docs/, publications/, clos_academy/, reports/pilot/ przy każdym commicie) — " +
      "opis każdego wpisu to pierwszy nagłówek H1 pliku, nie tekst wpisany w panel.js. Nowy plik .md w " +
      "jednym z tych katalogów pojawia się tu przy najbliższym commicie, bez zmiany kodu panelu. " +
      "Świadomie NIE rekurencyjne — pomija podkatalogi z danymi run-level " +
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

  // SPRINT v0.11.0 KROK 1 P2 (CTO 2026-07-26): przycisk "Generuj raport do
  // analizy". FETCHUJE gotowy plik reports/rerun_full_report_v0_11_0.md
  // (wygenerowany przez scripts/report_composer.py z danych re-runu) i
  // pobiera go jako Blob - ZERO skladania raportu w JS, zero liczb tutaj.
  // Jedno zrodlo prawdy raportu = generator Python; ten sam plik pozniej
  // (P2 KROK 2) wygeneruje pipeline po re-runie. Wpiete RAZ w
  // DOMContentLoaded (nie w loadAll - przycisk jest statyczny w index.html,
  // nie renderowany co 10 min).
  function downloadAnalysisReport() {
    var btn = document.getElementById("report-btn");
    var msg = document.getElementById("report-msg");
    var setMsg = function (text, cls) {
      if (!msg) return;
      msg.textContent = text;
      msg.className = "report-msg" + (cls ? " " + cls : "");
    };
    if (btn) btn.disabled = true;
    setMsg("Pobieranie…", "");
    fetchText(ARTIFACTS.report_md).then(function (text) {
      var blob = new Blob([text], { type: "text/markdown;charset=utf-8" });
      var url = URL.createObjectURL(blob);
      var a = document.createElement("a");
      a.href = url;
      a.download = "rerun_full_report_v0_11_0.md";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      setMsg("Pobrano rerun_full_report_v0_11_0.md", "ok");
    }).catch(function (err) {
      setMsg("Nie udało się pobrać raportu: " + ((err && err.message) || "błąd") +
        " (plik pojawia się po pushu — generuje go scripts/report_composer.py).", "err");
    }).then(function () {
      if (btn) btn.disabled = false;
    });
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
      artifactsIndex: fetchArtifactsIndex(),
      commits: fetchCommits(10),
      spec: fetchJSON(ARTIFACTS.spec),
      baselineText: fetchText(ARTIFACTS.baseline_hash),
      baselineCommitDate: fetchLastCommitDate(ARTIFACTS.baseline_hash),
      powerAnalysis: fetchJSON(ARTIFACTS.power_analysis),
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
    // Bundles/dokumenty/piloci pochodza teraz z JEDNEGO indeksu generowanego
    // w CI (fetchArtifactsIndex, raw fetch - bez limitu API) zamiast trzech
    // osobnych listowan katalogow GitHub API. Ksztalt idx.documents/.pilots/
    // .bundles jest celowo identyczny z tym, co dawniej zwracaly usuniete
    // fetchAllReports()/fetchAllPilotResults()/fetchAllBundles(), wiec
    // renderReports/renderPc001Documents/renderPc001PilotResults/
    // renderProvenance ponizej nie wymagaja zadnej zmiany logiki.
    loads.artifactsIndex.then(function (idx) {
      results.bundles = idx.bundles;
      results.reports = idx.documents;
      results.pilotResults = idx.pilots;
    }).catch(function (e) {
      results.bundlesError = e;
      results.reportsError = e;
      results.pilotResultsError = e;
    });
    loads.commits.then(function (v) { results.commits = v; }).catch(function (e) { results.commitsError = e; });
    loads.spec.then(function (v) { results.spec = v; }).catch(function (e) { results.specError = e; });
    loads.baselineText.then(function (v) { results.baselineText = v; }).catch(function (e) { results.baselineTextError = e; });
    loads.baselineCommitDate.then(function (v) { results.baselineCommitDate = v; }).catch(function () { results.baselineCommitDate = null; });
    loads.powerAnalysis.then(function () { results.powerAnalysisExists = true; })
      .catch(function () { results.powerAnalysisExists = false; });

    // Sekcja PC-001: czeka na spec/baseline/analizamocy/dokumenty(reports)/
    // wyniki pilotow - render dopiero gdy wszystkie sie rozstrzygna (sukces
    // lub blad, stad .catch zwracajacy null zamiast przerywac Promise.all),
    // zeby czesciowy sukces (np. spec OK, artifactsIndex niedostepny) nadal
    // wyrenderowal to, co sie udalo - renderPc001Documents/PilotResults
    // maja wlasne stany bledu per karta. Dokumenty i piloci pochodza z
    // jednego loads.artifactsIndex (patrz komentarz przy jego .then wyzej).
    Promise.all([
      loads.spec.catch(function () { return null; }),
      loads.baselineText.catch(function () { return null; }),
      loads.baselineCommitDate.catch(function () { return null; }),
      loads.powerAnalysis.then(function () { return true; }).catch(function () { return false; }),
      loads.artifactsIndex.catch(function () { return null; }),
    ]).then(function () {
      renderPc001({
        spec: results.spec, specError: results.specError,
        baselineText: results.baselineText, baselineError: results.baselineTextError,
        baselineCommitDate: results.baselineCommitDate,
        powerAnalysisExists: results.powerAnalysisExists,
        reports: results.reports, reportsError: results.reportsError,
        pilotResults: results.pilotResults, pilotResultsError: results.pilotResultsError,
      });
    });

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
      loads.artifactsIndex.then(function (idx) { return idx.bundles; }).catch(function () { return null; }),
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

    loads.artifactsIndex.then(function (idx) { return idx.documents; }).catch(function () { return null; }).then(function (reports) {
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
    // (loads.artifactsIndex.bundles), wiec zero dodatkowego zapytania.
    loads.artifactsIndex.then(function (idx) {
      var list = idx.bundles;
      var l11 = (list || []).filter(function (b) { return b.ok && b.name === "L1_1_pattern_echo"; })[0];
      updateFooter(l11 ? l11.meta : null);
    }).catch(function () { updateFooter(null); });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initNav();
    var reportBtn = document.getElementById("report-btn");
    if (reportBtn) reportBtn.addEventListener("click", downloadAnalysisReport);
    loadAll();
    // Pelne odswiezenie wszystkich danych co 10 minut...
    setInterval(loadAll, REFRESH_MS);
    // ...a sam WIEK danych w pulsie przeliczany co minute z juz pobranego
    // statusu (zero fetchu; guard - nie nadpisuj komunikatu bledu, gdy
    // status jeszcze/w ogole nie zostal pobrany).
    setInterval(function () { if (lastStatus) updatePulse(lastStatus); }, 60 * 1000);
  });
})();
