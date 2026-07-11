# CLOS — Cognitive Life Operating System (Incubator)

**Status: Research Grade Infrastructure for Artificial Ontogenesis.**

CLOS grows small "brains" (`BrainTissue`) from genomes, runs them against
deterministic and stochastic world scenarios, and measures cognitive
mechanisms through preregistered lessons ("Academy") with honest statistics
(CI95, `n_effective`, Glass's delta, Cohen's d — see
[clos_curriculum/laboratory/statistics.py](clos_curriculum/laboratory/statistics.py)).

This is not a "Publication Ready" or "Production Ready" system, and it is
not a claim of "Artificial Mind" — CLOS studies measurable *ontogenesis*
(how a Brain's internal state develops under a genome and an environment),
not general intelligence. Two lessons exist (L1.1 "Pattern Echo", L1.2
"Shock Recovery"), measuring 14 cognitive concepts total — the **minimal
competency profile** (concepts with `ci95_valid=True` for every genome
present) is currently **5 of 14**; see
[Cognitive Academy](#cognitive-academy) below for exactly which, and which
of the rest are explicitly `insufficient_data` vs measured-but-degenerate.

## What's frozen, what isn't

**Core Brain Runtime behavior is frozen, not the files themselves** (this
changed in v0.9 — see `SPRINT_v0.9.md`'s "nowy inwariant"). `clos_brain/`
(incl. `clos_brain/runtime/`, `clos_brain/tissue.py`), `clos_kernel/`,
`genome/`, `birth/` may only change **additively**, and only when a
regression test proves existing behavior is byte-identical before/after
(see `tests/golden_step_baseline.json`,
`tests/test_partial_step.py::TestStepRegression`). The one sanctioned
addition so far is `BrainRuntime.partial_step()`
([clos_brain/brain_runtime.py](clos_brain/brain_runtime.py),
[docs/spec_partial_step.md](docs/spec_partial_step.md)) — `step()` itself
has zero behavior changes.

Actively developed: `clos_academy/`, `clos_scientist/`, `clos_curriculum/`,
`clos_studio/`, CI, docs, tests.

## Running tests

```bash
pip install -r requirements.txt
pip install pytest
pytest -q
```

CI ([.github/workflows/ci.yml](.github/workflows/ci.yml)) runs on every
push/PR: `pytest -q`, then three artifact validators:

```bash
python scripts/validate_publication.py   # every Publication Bundle has full provenance
python scripts/validate_artifacts.py     # reports match their preregistration + scenario stochasticity
python scripts/validate_panel.py         # clos_studio/panel/panel.js has zero hardcoded metrics/hashes
```

On a successful run on `v0.7.2-scientific-integrity`, CI also writes
`reports/status.json` (test count, validator results, commit, timestamp)
back to the repo — this is what the [Panel Badacza](#panel-badacza) reads
for its "Testy i CI" section, instead of the GitHub API.

## Module structure

| Module | Role |
|---|---|
| `genome/` | Genome Engine — genome definitions and gene expression. |
| `birth/` | Birth Engine — instantiates a Brain from a genome. |
| `clos_kernel/` | Kernel Runtime — tick loop, snapshots, event bus. **Core, behavior frozen.** |
| `clos_brain/` | Brain Runtime — perception, prediction, plasticity, precision, homeostasis, action, `partial_step()`. **Core, behavior frozen** (additive changes only, regression-tested). |
| `clos_world/` | World Runtime — stimulus generators/scenarios (`stable_world`, `noise_world`, `drift_world`, `shock_world`). |
| `clos_academy/` | Cognitive Academy — lessons (L1.1 "Pattern Echo", L1.2 "Shock Recovery") + [cognitive_ontology.md](clos_academy/cognitive_ontology.md). |
| `clos_scientist/` | Metrics, experiment reports, Capability Analyzer, Competency Profile builder. |
| `clos_curriculum/` | Statistics lab (CI95, Glass's delta, Cohen's d), curriculum levels. |
| `clos_studio/` | Matrix runner, Publication Bundle builder, provenance/artifact management, [Panel Badacza](#panel-badacza) (`clos_studio/panel/`). |
| `clos_cli/` | CLI entry points. |
| `clos_research/`, `clos_dashboard/`, `clos_tower/` | Supporting benchmark/dashboard tooling. |
| `publications/` | Publication Bundles (full provenance) + prerejestracje. |
| `reports/` | Generated Academy/experiment reports + `status.json` (CI-written). |
| `scripts/` | CI validators (`validate_publication.py`, `validate_artifacts.py`, `validate_panel.py`) + `write_status.py`. |
| `docs/` | Design specs and research hypotheses for not-yet-implemented work (`spec_partial_step.md` implemented in v0.9; `idio_morph_hypothesis.md` is hypothesis-only, zero code). |
| `tests/` | pytest suite. |

## Cognitive Academy

- [clos_academy/cognitive_ontology.md](clos_academy/cognitive_ontology.md) —
  the single authoritative definition of every cognitive concept used
  anywhere in Academy reports (Perception, Attention, Pattern Recognition,
  Pattern Retention, Working Memory, Long-term Memory, Prediction,
  Adaptation, Exploration, Generalization, Planning, Stability, Energy
  Efficiency, Homeostatic Resilience — 14 total). Every future lesson and
  metric refers back to this document.
- [publications/competency_profile.md](publications/competency_profile.md) —
  two profiles, generated purely from `reports/academy/*.json` by
  [clos_scientist/competency_profile.py](clos_scientist/competency_profile.py)
  (no hand-editing): the **minimal profile** (official — only concepts
  where every present genome has `ci95_valid=True`, currently 5/14), and
  the **full profile** (all 14, with `measured`-but-degenerate and
  `insufficient_data` kept as separate, explicit categories — nothing
  hidden).
- [publications/preregistration_L1_1.json](publications/preregistration_L1_1.json) /
  [publications/preregistration_L1_2.json](publications/preregistration_L1_2.json) —
  the preregistered hypothesis, primary/secondary endpoints, and statistical
  plan for each lesson, kept in sync with
  [clos_academy/lesson_L1_1.py](clos_academy/lesson_L1_1.py) /
  [clos_academy/lesson_L1_2.py](clos_academy/lesson_L1_2.py).
- [docs/idio_morph_hypothesis.md](docs/idio_morph_hypothesis.md) — four
  open research questions about representation (dynamic encoding, morphic
  compression, idiosyncratic semantics, metabolic memory cost).
  Hypothesis only — zero production code.

## Panel Badacza

**[https://gozimek79-debug.github.io/SST-Incubator/](https://gozimek79-debug.github.io/SST-Incubator/)**

A static, read-only dashboard ([clos_studio/panel/](clos_studio/panel/):
`index.html` + `panel.css` + `panel.js`, no build step, no framework)
hosted on GitHub Pages ([.github/workflows/pages.yml](.github/workflows/pages.yml)).
It shows the same 7 views as this README's data — Overview, Lekcje i wyniki,
Profil kompetencji, Porównanie genomów, Prowenancja, Testy i CI, Raporty —
by fetching JSON directly from this repo in the visitor's browser. It does
not run anything and does not embed any metric in its source: every number
comes from `fetch()` against `raw.githubusercontent.com` (reports,
publications, prerejestracje) and `reports/status.json` (test count, CI
status — written by CI itself, see above). `scripts/validate_panel.py`
enforces this in CI by scanning `panel.js` for hardcoded floats/hashes/counts
and failing the build if it finds one.

**How it refreshes:** there is nothing to redeploy for data changes. The
panel reads live on every page load — push new reports/publications/status
to `v0.7.2-scientific-integrity` and reload the page. Pages itself only
needs to redeploy when `clos_studio/panel/` (the HTML/CSS/JS) changes, which
`pages.yml` does automatically on every push to that branch.

**Known limitation:** the commit timeline (Overview) and the legacy-bundle
listing (Prowenancja) use the GitHub API, which is rate-limited to 60
requests/hour per IP for unauthenticated callers — on a page with many
visitors sharing an egress IP this can 403. Those two widgets degrade to an
explicit "limit API" notice in that case; every other section (reports,
competency profile, provenance of the L1.1 bundle, test/CI status) reads
from `raw.githubusercontent.com` instead and is unaffected.

## Roadmap

See [ROADMAP.md](ROADMAP.md).
