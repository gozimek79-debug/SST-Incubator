# Spec: `BrainRuntime.partial_step()`

**Status: proposal only. Not implemented. Does not authorize any change to
`clos_brain/`.** This document exists to be reviewed and either accepted,
rejected, or revised before any Core work starts (earliest: v0.9).

## 1. Motivation

`BrainRuntime.step()` ([clos_brain/brain_runtime.py](../clos_brain/brain_runtime.py))
is a fixed 7-step pipeline:

```
1. perceive         (clos_brain/runtime/perception.py)
2. predict           (clos_brain/runtime/prediction.py)
3. compute_error      (clos_brain/runtime/precision.py)
4. compute_precision   (clos_brain/runtime/precision.py)
5. regulate            (clos_brain/runtime/homeostasis.py)
6. update_memory        (clos_brain/runtime/plasticity.py)
7. apply_decay (every 10th tick) (clos_brain/runtime/plasticity.py)
```

Lesson L1.1 needs a "silence" phase: ticks where the Brain receives no
external stimulus and must rely on memory alone. `step()` has no way to
express "run the pipeline but skip step 1" — `perceive()` always sets
`last_input`, so there's no sanctioned way to leave it `None` without
either (a) modifying `perceive()` to accept a sentinel value, or (b)
reimplementing the pipeline outside Core.

v0.8.2 tried (a) — a `-1.0`/`None` sentinel threaded through `perceive()` —
and rejected it: it changed Core behavior (however slightly) during a
period where Core is meant to be frozen and auditable byte-for-byte against
a known-good baseline.

The current workaround is (b):
[clos_academy/echo_runtime.py](../clos_academy/echo_runtime.py)'s
`silent_step()` reimplements the 7-step pipeline at the Academy layer,
calling the same frozen primitives (`predict`, `compute_error`,
`compute_precision`, `regulate`, `update_memory`, `apply_decay`) directly,
but skipping `perceive()` and instead setting `brain.last_input = None`
itself before calling `predict()`. This works — L1.1 passes, Core is
untouched — but it has three real costs:

- **Duplication.** The step order in `silent_step()` must be kept
  manually in sync with `BrainRuntime.step()`. They have already diverged
  once by omission risk (nothing enforces it structurally); a future Core
  change to step order silently desyncs the two.
- **Escapes the "Core owns the pipeline" invariant.** Any future lesson
  that needs a different partial pipeline (e.g. skip `update_memory` to
  test pure prediction without learning) has to write its own
  hand-rolled copy of `BrainRuntime.step()`, multiplying the duplication
  and divergence risk.
- **Not reviewable as a single Core contract.** Reviewers auditing
  `clos_brain/` for Core-freeze compliance also have to separately audit
  every Academy-layer pipeline reimplementation to confirm it actually
  matches frozen behavior — the freeze boundary becomes fuzzy.

`partial_step()` is proposed as the sanctioned, single place this
capability would live, so lessons declare *what to skip*, not *how to
reimplement the pipeline*.

## 2. Proposed interface

```python
class BrainRuntime:
    @staticmethod
    def partial_step(
        brain: BrainTissue,
        sensory_input: Optional[float],
        seed: int,
        tick: int,
        skip_steps: frozenset[str] = frozenset(),
    ) -> BrainTissue:
        ...
```

- `sensory_input: Optional[float]` — `None` means "no external stimulus
  this tick" (replaces the current `echo_runtime.py` pattern of setting
  `brain.last_input = None` after the fact).
- `skip_steps` — a set drawn from a **closed, named** enum of the 7
  existing pipeline steps (not arbitrary strings):

  ```python
  class PipelineStep(str, Enum):
      PERCEIVE = "perceive"
      PREDICT = "predict"
      COMPUTE_ERROR = "compute_error"
      COMPUTE_PRECISION = "compute_precision"
      REGULATE = "regulate"
      UPDATE_MEMORY = "update_memory"
      APPLY_DECAY = "apply_decay"
  ```

  `partial_step()` runs the same 7 steps, in the same order, as `step()`,
  skipping exactly the ones named in `skip_steps`. It calls the same
  frozen primitives `step()` calls — no new logic, no reimplementation.

- `step()` becomes (conceptually) `partial_step(..., skip_steps=frozenset())`
  — i.e. `step()` can be reimplemented in terms of `partial_step()` with an
  empty skip set, or left as-is with `partial_step()` added alongside it.
  Either way, **the 7-step body must have exactly one implementation**,
  not two that can drift.

- `silent_step()` in `echo_runtime.py` would become a thin wrapper:
  `BrainRuntime.partial_step(brain, sensory_input=None, seed=seed, tick=tick, skip_steps={PipelineStep.PERCEIVE})`.

## 3. Contract

- **Step order is fixed and not a parameter.** `skip_steps` removes steps;
  it never reorders them. Reordering is out of scope for this spec.
- **`PERCEIVE` is skip-safe by construction today**, because `predict()`
  already handles `last_input is None` / empty `sensory_buffer` (falls
  back to a neutral prediction or buffer memory — see
  [clos_brain/runtime/prediction.py](../clos_brain/runtime/prediction.py)),
  and `compute_error()` already no-ops when `last_input is None` (see
  [clos_brain/runtime/precision.py:18](../clos_brain/runtime/precision.py)).
  Skipping `PERCEIVE` requires no Core change — the frozen primitives
  already tolerate it.
- **Skipping any other step is NOT presumed safe** and is out of scope for
  this spec. `PREDICT`, `COMPUTE_ERROR`, `COMPUTE_PRECISION`, `REGULATE`,
  `UPDATE_MEMORY`, `APPLY_DECAY` each write fields later steps or later
  ticks read (`last_prediction`, `prediction_error_buffer`, `precision`,
  `energy`/`entropy`, `memory`). Skipping any of them needs its own
  written analysis of what breaks downstream before it is added to the
  set of steps a lesson is allowed to skip — this spec only certifies
  `PERCEIVE` as safe-to-skip, because that is the one case with an
  existing, tested workaround (`echo_runtime.py`) to validate against.
- **No new state, no new fields on `BrainTissue`.** `partial_step()` is an
  orchestration wrapper around the existing 7 calls; it does not add
  anything for the skipped step to leave behind.
- **`skip_steps` is validated against the closed `PipelineStep` enum** —
  passing an unrecognized value raises, rather than silently doing
  nothing (fails loud, not silent).

## 4. Impact on determinism

`step()` seeds `random.seed(seed + tick)` once per tick, before running the
pipeline. `partial_step()` must do the same, **regardless of which steps
are skipped**, so that:

- A run with `skip_steps=frozenset()` (i.e. equivalent to plain `step()`)
  produces byte-identical output to `step()` for the same
  `(brain, sensory_input, seed, tick)` — this is the regression test that
  proves `partial_step()` is not silently a different function.
- A run with `skip_steps={PERCEIVE}` produces byte-identical output to the
  current `echo_runtime.silent_step()` for the same inputs — this is the
  regression test that proves the migration doesn't change L1.1's results.

Skipping a step changes *which fields get written*, not the RNG draw
sequence for steps that do run — e.g. skipping `PERCEIVE` means
`compute_error()` still consumes the RNG state exactly as it would
otherwise (it doesn't use `random` directly today, but the invariant is:
unskipped steps must behave identically to their behavior inside `step()`,
seed draw included).

## 5. Test plan (for whenever this is implemented — not now)

1. **Equivalence to `step()`:** for a fixed `(brain, sensory_input, seed,
   tick)`, `partial_step(skip_steps=frozenset())` output ==
   `step()` output, field-by-field.
2. **Equivalence to `echo_runtime.silent_step()`:** for a fixed
   `(brain, seed, tick)`, `partial_step(sensory_input=None, skip_steps={PERCEIVE})`
   output == current `silent_step()` output, field-by-field.
3. **L1.1 regression:** re-run `clos_academy/lesson_L1_1.py` with
   `silent_step()` replaced by the `partial_step()` wrapper; primary
   endpoint (`mse_at_tick_50`), `n_effective`, and `ci95_valid` per genome
   must be unchanged from the current `reports/academy/L1_1_pattern_echo.json`.
4. **Invalid `skip_steps` rejected:** passing a value not in `PipelineStep`
   raises, not silently ignored.
5. **`skip_steps` beyond `{PERCEIVE}` explicitly unsupported/raises** until
   each additional step gets its own written safety analysis (§3) —
   the initial implementation should refuse them rather than silently
   allow something no one has verified.

## 6. Explicitly out of scope for this spec

- Implementing `partial_step()` itself (this document is the proposal to
  review, not a merge-ready PR).
- Skipping any step other than `PERCEIVE`.
- Reordering the pipeline.
- Any change to `clos_brain/`, `clos_kernel/`, `genome/`, or `birth/` —
  writing this spec does not unfreeze Core.
