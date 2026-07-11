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

## v0.9 — `partial_step()`, `core/` debt, L1.2, minimal profile (this sprint)

New project invariant: we protect the **behavior** of the system, not the
files (see README "What's frozen, what isn't"; `SPRINT_v0.9.md`). Core may
now change, but only additively, and only behind a regression test proving
existing behavior is unchanged.

- `core/` (dead code — 5 files, 0 imports from outside itself) removed.
- `BrainRuntime.partial_step()` implemented as an additive extension of
  `step()` ([docs/spec_partial_step.md](docs/spec_partial_step.md)). Only
  `PERCEIVE` is certified skippable; anything else raises
  `NotImplementedError` (explicitly uncertified, not a wrong value).
  `tests/golden_step_baseline.json` + `test_step_regression` protect
  `step()`'s exact output, generated on the commit *before* `partial_step()`
  existed, so the test can't compare the code to itself.
- [clos_academy/echo_runtime.py](clos_academy/echo_runtime.py) refactored
  onto `partial_step(skip={PERCEIVE})` — the hand-rolled pipeline
  duplication is gone; L1.1 verified byte-identical after the refactor
  (all 40 `run_*.json` files unchanged).
- **L1.2 "Shock Recovery"** — second Academy lesson, primary endpoint
  structurally different from L1.1 (`recovery_time` /
  `time_to_sustained_band`, not MSE). Preregistration
  ([publications/preregistration_L1_2.json](publications/preregistration_L1_2.json))
  gives a formal, mathematical endpoint definition: homeostasis band,
  observation window, censoring rule, and a data-driven threshold
  (`pre_shock_band_check`, 0.8) deciding whether the endpoint measures
  "recovery" or "establishment" of homeostasis.
- Capability Analyzer refactored to an **N:M** relation (concept → list of
  lessons) — required to absorb L1.2 without breaking L1.1; the 4 concepts
  fed only by L1.1 verified byte-identical before/after the refactor.
- Competency Profile: **minimal profile** (only `ci95_valid=True`, 5/14)
  split from the **full profile** (all 14, with degenerate/
  `insufficient_data` as explicit, separate categories).
- [docs/idio_morph_hypothesis.md](docs/idio_morph_hypothesis.md) — four
  open research questions about representation, zero code.
- Status: **"Research Grade Infrastructure for Artificial Ontogenesis"** —
  no "Artificial Mind" framing anywhere in the repo (verified by grep).
- Honest limitations (see `RAPORT_v0.9.md`): `highly_plastic` in L1.2 is
  100% censored (never recovers within the observation window — a real
  result, not a bug). Adaptation/Stability are still degenerate, and now
  root-caused: `kernel.snapshot_engine` is always empty because no lesson
  calls `kernel.run_tick()` — a known debt, **not fixed in this sprint**.

## v0.10 — Predictive Coding, Latent Space

Not started. Depends on:
- New lessons beyond L1.1/L1.2, to raise the minimal Competency Profile's
  count past 5/14 and give Predictive Coding / Latent Space work something
  to be measured against.
- Possibly new `PipelineStep` entries in `partial_step()` if this work
  needs to skip/reorder more than `PERCEIVE` — architecturally unblocked
  (see [docs/idio_morph_hypothesis.md](docs/idio_morph_hypothesis.md) §2),
  but each new certified-skippable step needs its own safety analysis
  first, same as `PERCEIVE` did.

## v1.0 — Evolution Engine

Not started. Genome mutation/selection across generations, evaluated
through the same Academy / Capability Analyzer / Competency Profile
machinery built in v0.8.4–v0.9 — no new, parallel scoring system.
