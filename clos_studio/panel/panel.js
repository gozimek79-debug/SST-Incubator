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
    metadata: "publications/L1_1_pattern_echo/metadata.json",
    prereg: "publications/preregistration_L1_1.json",
    status: "reports/status.json",
  };

  var C = {
    chA: "#4FC8E0", chB: "#A98CFF", ok: "#5FC98C", warn: "#F2B049",
    mut: "#78879A", txt: "#E8EDF3",
  };

  /* ---------- sekcje (musi byc zgodne z index.html) ---------- */
  var SECTIONS = ["overview", "lessons", "competency", "genomes", "provenance", "tests", "reports"];
  var SECTION_LABELS = {
    overview: "Przegląd", lessons: "Lekcje i wyniki", competency: "Profil kompetencji",
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

  function fetchLegacyBundles() {
    var listUrl = API_BASE + "/contents/publications?ref=" + BRANCH;
    return fetch(listUrl).then(function (res) {
      if (!res.ok) {
        var e = new Error("HTTP " + res.status);
        e.sourceUrl = listUrl;
        throw e;
      }
      return res.json();
    }).then(function (entries) {
      var dirs = entries.filter(function (en) {
        return en.type === "dir" && en.name.indexOf("EXP-") === 0;
      });
      return Promise.all(dirs.map(function (d) {
        return fetchJSON("publications/" + d.name + "/metadata.json")
          .then(function (meta) { return { name: d.name, meta: meta, ok: true }; })
          .catch(function (err) { return { name: d.name, error: err, ok: false }; });
      }));
    });
  }

  function fetchCommits(limit) {
    var url = API_BASE + "/commits?sha=" + BRANCH + "&per_page=" + (limit || 10);
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

  /* ================= SVG chart: MSE@50 ± CI95 ================= */
  function mseChartSvg(genomeRows) {
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
      'aria-label="MSE po 50 tickach ciszy, srednia z przedzialem ufnosci 95%, per genom">' +
      gridSvg + barsSvg + "</svg>"
    );
  }

  /* ================= renderery sekcji ================= */

  function competencyRowState(c) {
    if (c.status !== "measured") return "insufficient";
    var genomeKeys = Object.keys(c.genomes || {});
    var allValid = genomeKeys.length > 0 && genomeKeys.every(function (g) { return c.genomes[g].ci95_valid === true; });
    return allValid ? "valid" : "degenerate";
  }

  function renderOverview(ctx) {
    var comp = ctx.competency;
    var report = ctx.report;
    var commits = ctx.commits;
    var status = ctx.status;

    var measured = comp ? comp.summary.measured : null;
    var total = comp ? comp.summary.total_concepts : null;
    var validCount = comp ? comp.concepts.filter(function (c) { return competencyRowState(c) === "valid"; }).length : null;
    var lessonsCount = report ? 1 : 0;

    var tiles = [
      { l: "Status", val: "Research Grade Infrastructure", sub: "deklaracja repo, nie liczba", c: "var(--chA)", wide: true },
      { l: "Testy", val: status && status.tests ? String(status.tests.passed) : "—",
        sub: status ? "passed · reports/status.json" : "reports/status.json niedostępny", c: "var(--ok)" },
      { l: "CI", val: status && status.ci ? status.ci.conclusion : "—",
        sub: status ? "per-commit, po walidatorach" : "reports/status.json niedostępny",
        c: status && status.ci && status.ci.conclusion === "success" ? "var(--ok)" : "var(--crit)" },
      { l: "Core", val: "frozen", sub: "zasada sprintu (clos_brain/, clos_kernel/, genome/, birth/)", c: "var(--chA)" },
      { l: "Lekcje", val: lessonsCount ? String(lessonsCount) : "—", sub: lessonsCount ? "wczytanych raportów Academy" : "brak danych", c: "var(--txt)" },
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
      timelineHtml = '<div class="state state-error"><p>Nie udało się pobrać historii commitów z GitHub API.</p>' +
        '<p class="state-detail">' + escapeHtml((ctx.commitsError && ctx.commitsError.message) || "") + "</p></div>";
    }
    var timelineCard = '<section class="card span"><header class="card-h">' +
      '<span class="card-t">Ostatnie commity</span><span class="card-s">gałąź ' + escapeHtml(BRANCH) +
      " · GitHub API</span></header><div class=\"card-b\">" + timelineHtml + "</div></section>";

    setSectionHTML("overview", '<div class="tiles" style="grid-column:1/-1">' + tilesHtml + "</div>" + timelineCard + statusNotice);
  }

  function renderLessons(report, prereg, reportErr, preregErr) {
    var notices = "";
    if (!report) notices += missingArtifactHtml(ARTIFACTS.report, reportErr);
    if (!prereg) notices += missingArtifactHtml(ARTIFACTS.prereg, preregErr);
    if (!report && !prereg) { setSectionHTML("lessons", notices); return; }

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

    var head =
      '<section class="card span"><header class="card-h"><span class="card-t">' +
      escapeHtml((prereg && prereg.lesson_id) || (report && report.lesson) || "L1.1") + " — " +
      escapeHtml((report && report.title) || (prereg && prereg.title) || "") + "</span>" +
      '<span class="card-s">' + escapeHtml(scenario) + " · kontrola: " + escapeHtml(control) + "</span></header>" +
      '<div class="card-b">' +
      (prereg ? '<p class="prose"><b>Hipoteza.</b> ' + escapeHtml(prereg.hypothesis) + "</p>" : "") +
      '<div class="kv">' +
      '<div><span>Primary endpoint</span><b>' + escapeHtml((prereg && prereg.primary_endpoint && prereg.primary_endpoint.metric) || "—") +
      (prereg && prereg.primary_endpoint ? " @ " + prereg.primary_endpoint.measurement_tick : "") + "</b></div>" +
      '<div><span>Kryterium PASS</span><b>' + (passCond ? "MSE@50 &lt; " + fmtNum(passCond.mse_at_tick_50_max, 2) : "—") + "</b></div>" +
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
        '<section class="card span"><header class="card-h"><span class="card-t">MSE @ 50 · średnia ± CI95</span>' +
        '<span class="card-s">scenariusz: ' + escapeHtml(scenario) + "</span></header>" +
        '<div class="card-b">' + mseChartSvg(rows) +
        '<p class="note">Kontrola <code>' + escapeHtml(control) + "</code> jest deterministyczna (n_effective=1, " +
        "CI95 nie dotyczy) — punkt odniesienia, nie źródło wariancji.</p></div></section>";
    }

    setSectionHTML("lessons", notices + head + chartHtml);
  }

  function renderCompetency(comp) {
    if (!comp) return;
    var measured = comp.summary.measured, total = comp.summary.total_concepts;
    var valid = comp.concepts.filter(function (c) { return competencyRowState(c) === "valid"; }).length;

    var rows = comp.concepts.map(function (c) {
      var state = competencyRowState(c);
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

      return '<div class="crow ' + state + '"><div class="crow-head"><span class="crow-k">' + escapeHtml(c.concept) + "</span>" +
        '<span class="pill" style="color:' + color + ";border-color:" + color + '55">' + label +
        (c.source_lesson ? " · " + escapeHtml(c.source_lesson) : "") + "</span></div>" + body + "</div>";
    }).join("");

    var html =
      '<section class="card span"><header class="card-h"><span class="card-t">Instrument kompetencji</span>' +
      '<span class="card-s">zmierzone ' + measured + "/" + total + " · ważne CI95 " + valid + "/" + total +
      ' — luki są jawne, nie ukryte</span></header><div class="card-b"><div class="comp">' + rows + "</div></div></section>";
    setSectionHTML("competency", html);
  }

  function renderGenomes(comp) {
    if (!comp) return;
    var rows = comp.concepts.filter(function (c) { return competencyRowState(c) === "valid"; });
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
    setSectionHTML("genomes", html);
  }

  function renderProvenance(metadata, legacy, legacyError, metadataError) {
    var bundleCard = "";
    if (metadata) {
      bundleCard =
        '<section class="card span"><header class="card-h"><span class="card-t">Bundle L1.1 — prowenancja</span>' +
        '<span class="card-s">odtwarzalność eksperymentu</span></header><div class="card-b"><dl class="prov">' +
        ["experiment_id", "git_commit", "config_hash", "manifest_hash", "timestamp", "total_runs", "clos_version", "reproducible"]
          .map(function (k) {
            var v = metadata[k];
            var shown = (k === "git_commit" || k === "config_hash" || k === "manifest_hash") ? truncHash(v) :
              (k === "timestamp" ? String(v).replace("T", " ") :
              (k === "reproducible" ? (v ? "✓ true" : "✗ false") : String(v)));
            return "<div><dt>" + k + "</dt><dd>" + escapeHtml(shown) + "</dd></div>";
          }).join("") +
        "</dl></div></section>";
    } else {
      bundleCard = missingArtifactHtml(ARTIFACTS.metadata, metadataError);
    }

    var legacyCard;
    if (legacy && legacy.length) {
      legacyCard =
        '<section class="card span"><header class="card-h"><span class="card-t">Bundle legacy (pre-0.7.2)</span>' +
        '<span class="card-s">oznaczone, prowenancja nie fabrykowana · GitHub API</span></header>' +
        '<div class="card-b"><div class="legacy">' + legacy.map(function (item) {
          if (!item.ok) {
            return '<div class="leg-row"><code>' + escapeHtml(item.name) + '</code>' +
              '<span class="leg-note" style="color:var(--crit)">nie wczytano metadata.json</span></div>';
          }
          var m = item.meta;
          var tag = m.provenance || "brak flagi provenance";
          return '<div class="leg-row"><code>' + escapeHtml(m.experiment_id || item.name) + "</code>" +
            '<span class="pill" style="color:var(--mut);border-color:#78879A55">' + escapeHtml(tag) + "</span>" +
            '<span class="leg-note">git_commit: ' + (m.git_commit ? escapeHtml(truncHash(m.git_commit)) : "pusty (nie zgadywany)") + "</span></div>";
        }).join("") + "</div></div></section>";
    } else {
      legacyCard = '<section class="card span"><div class="card-b"><div class="state state-error">' +
        "<p>Nie udało się wylistować legacy bundli przez GitHub API.</p>" +
        '<p class="state-detail">' + escapeHtml((legacyError && legacyError.message) || "") + "</p></div></div></section>";
    }

    setSectionHTML("provenance", bundleCard + legacyCard);
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

  function renderReports() {
    var reports = [
      { f: "RAPORT_KONCOWY_v0.8.4.md", d: "Raport końcowy sprintu v0.8.4 — uczciwa ocena gotowości" },
      { f: "publications/preregistration_L1_1.json", d: "Prerejestracja L1.1 (noise_world)" },
      { f: "publications/competency_profile.md", d: "Profil kompetencji + karty genomów" },
      { f: "clos_academy/cognitive_ontology.md", d: "Ontologia — 13 pojęć poznawczych" },
      { f: "docs/spec_partial_step.md", d: "Specyfikacja partial_step() (pod v0.9)" },
      { f: "README.md", d: "Status projektu, jak uruchomić testy, struktura modułów" },
      { f: "ROADMAP.md", d: "v0.7.x → v0.8.4 → v0.9 → v1.0" },
    ];
    var rowsHtml = reports.map(function (r) {
      var url = "https://github.com/" + OWNER + "/" + REPO + "/blob/" + BRANCH + "/" + r.f;
      return '<div class="rep-row"><a class="rep-f" href="' + url + '" target="_blank" rel="noopener">' +
        escapeHtml(r.f) + "</a><span class=\"rep-d\">" + escapeHtml(r.d) + "</span></div>";
    }).join("");

    var html =
      '<section class="card span"><header class="card-h"><span class="card-t">Artefakty i raporty</span>' +
      '<span class="card-s">gałąź ' + escapeHtml(BRANCH) + "</span></header>" +
      '<div class="card-b"><div class="reports">' + rowsHtml + "</div>" +
      '<p class="note">Lista wybranych plików dokumentacyjnych, utrzymywana ręcznie (jak spis treści) — ' +
      "linki prowadzą wprost do repo na GitHubie. To ścieżki, nie metryki naukowe.</p></div></section>";
    setSectionHTML("reports", html);
  }

  function updateTopPills(metadata, commits, status) {
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
    foot.innerHTML = "Dane: gałąź <code>" + escapeHtml(BRANCH) + "</code>" +
      (ts ? " · bundle L1.1 wygenerowany " + escapeHtml(ts) : "") +
      " · panel czyta na żywo z <code>reports/academy/</code> i <code>publications/</code>, żadna liczba nie jest wpisana na sztywno.";
  }

  /* ================= orkiestracja ================= */
  function loadAll() {
    var loads = {
      report: fetchJSON(ARTIFACTS.report),
      competency: fetchJSON(ARTIFACTS.competency),
      metadata: fetchJSON(ARTIFACTS.metadata),
      prereg: fetchJSON(ARTIFACTS.prereg),
      status: fetchJSON(ARTIFACTS.status),
      legacy: fetchLegacyBundles(),
      commits: fetchCommits(10),
    };

    var results = {};

    loads.report.then(function (v) { results.report = v; }).catch(function (e) { results.reportError = e; });
    loads.prereg.then(function (v) { results.prereg = v; }).catch(function (e) { results.preregError = e; });
    loads.metadata.then(function (v) { results.metadata = v; }).catch(function (e) { results.metadataError = e; });
    loads.status.then(function (v) { results.status = v; }).catch(function (e) { results.statusError = e; });
    loads.competency.then(function (v) { results.competency = v; }).catch(function (e) {
      sectionError("competency", ARTIFACTS.competency, e);
      sectionError("genomes", ARTIFACTS.competency, e);
    });
    loads.legacy.then(function (v) { results.legacy = v; }).catch(function (e) { results.legacyError = e; });
    loads.commits.then(function (v) { results.commits = v; }).catch(function (e) { results.commitsError = e; });

    Promise.all([
      loads.report.catch(function () { return null; }),
      loads.prereg.catch(function () { return null; }),
    ]).then(function (vals) {
      renderLessons(vals[0], vals[1], results.reportError, results.preregError);
    });

    loads.competency.then(function (comp) {
      renderCompetency(comp);
      renderGenomes(comp);
    }).catch(function () {});

    Promise.all([
      loads.metadata.catch(function () { return null; }),
      loads.legacy.catch(function () { return null; }),
    ]).then(function (vals) {
      renderProvenance(vals[0], vals[1], results.legacyError, results.metadataError);
    });

    loads.status.then(function (s) { renderTests(s, null); })
      .catch(function (e) { renderTests(null, e); });

    renderReports();

    Promise.all([
      loads.competency.catch(function () { return null; }),
      loads.report.catch(function () { return null; }),
      loads.commits.catch(function () { return null; }),
      loads.status.catch(function () { return null; }),
    ]).then(function (vals) {
      renderOverview({
        competency: vals[0], report: vals[1], commits: vals[2], status: vals[3],
        commitsError: results.commitsError, statusError: results.statusError,
      });
      updateTopPills(results.metadata, vals[2], vals[3]);
    });

    loads.metadata.then(function (m) { updateFooter(m); }).catch(function () { updateFooter(null); });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initNav();
    loadAll();
  });
})();
