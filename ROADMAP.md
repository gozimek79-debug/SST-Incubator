# CLOS Roadmap

Status labels used in this document are factual, not marketing: a line item
is either done (with the artifact that proves it), in progress, or not
started. No "Publication Ready" / "Production Ready" claims — see
[README.md](README.md).

## v0.7.x — Scientific integrity foundation

- CI95 / `n_effective` / Glass's delta statistics with an explicit
  pseudoreplication guard
  ([clos_curriculum/laboratory/statistics.py](clos_curriculum/laboratory/statistics.py)).
- Core Brain Runtime frozen (`clos_brain/`, `clos_kernel/`, `genome/`,
  `birth/`).
- L1.1 "Pattern Echo" lesson passes with real seed-to-seed variance
  (end of pseudoreplication in the primary endpoint).

## v0.8.4 — Infrastructure integrity (this sprint)

- L1.1 preregistered on `noise_world`; `stable_world` kept as a separate,
  deterministic control baseline for Glass's delta
  ([publications/preregistration_L1_1.json](publications/preregistration_L1_1.json)).
- Publication Bundle with full provenance (`git_commit`, `config_hash`,
  `manifest_hash`, `timestamp`, `experiment_id`); legacy `EXP-*` bundles
  tagged `provenance: "legacy-pre-0.7.2"`, not fabricated.
- CI ([.github/workflows/ci.yml](.github/workflows/ci.yml)) +
  `scripts/validate_publication.py` + `scripts/validate_artifacts.py`,
  running on every push/PR.
- [clos_academy/cognitive_ontology.md](clos_academy/cognitive_ontology.md) —
  single source of truth for cognitive terms, replacing an earlier,
  inconsistent draft.
- Capability Analyzer + Competency Profile: 6/13 concepts measured from
  L1.1, 7/13 explicitly `insufficient_data`
  ([publications/competency_profile.md](publications/competency_profile.md)).
- [docs/spec_partial_step.md](docs/spec_partial_step.md) — specification
  only, no implementation, no Core changes.

## v0.8.5 — Panel Badacza (Studio, read-only)

- [clos_studio/panel/](clos_studio/panel/) — static, no-build dashboard
  (`index.html` + `panel.css` + `panel.js`), hosted on GitHub Pages
  ([.github/workflows/pages.yml](.github/workflows/pages.yml)):
  [https://gozimek79-debug.github.io/SST-Incubator/](https://gozimek79-debug.github.io/SST-Incubator/).
  Read-only tool in the Studio layer — it does not run experiments or write
  anything back to the repo; it only fetches and displays artifacts that
  already exist (reports, publications, `reports/status.json`).
- `reports/status.json` written by CI (`scripts/write_status.py`) only after
  a fully green `pytest` + all three validators — the panel's "Testy i CI"
  reads this instead of the GitHub API, avoiding the 60-req/hour
  unauthenticated rate limit for that specific data.
- `scripts/validate_panel.py` — CI gate against hardcoded metrics in
  `panel.js` (floats, hashes, the literal test count), same "no drift
  between code and data" discipline as `validate_artifacts.py`.
- See [RAPORT_v0.8.5.md](RAPORT_v0.8.5.md) for the honest account of what
  it took to get GitHub Pages actually serving this (environment branch
  policy, competing auto-generated workflows) and what is *not* covered by
  automated verification (panel.js's JS-rendered output, as opposed to its
  static HTML shell).

## v0.9 — Predictive Coding, Latent Space

Not started. Depends on:
- A sanctioned way to skip Core pipeline steps without touching
  `clos_brain/` behavior — either `BrainRuntime.partial_step()` per
  [docs/spec_partial_step.md](docs/spec_partial_step.md), or an equivalent
  reviewed Core extension. The current workaround
  ([clos_academy/echo_runtime.py](clos_academy/echo_runtime.py)) only
  covers the single case L1.1 needs (silence = skip perception).
- New lessons beyond L1.1, to raise the Competency Profile's `measured`
  count past 6/13 and give Predictive Coding / Latent Space work something
  to be measured against.

## v1.0 — Evolution Engine

Not started. Genome mutation/selection across generations, evaluated
through the same Academy / Capability Analyzer / Competency Profile
machinery built in v0.8.4 — no new, parallel scoring system.
