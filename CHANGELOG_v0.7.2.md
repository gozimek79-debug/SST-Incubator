# CLOS v0.7.2 — Scientific Integrity Patch

Branch: `v0.7.2-scientific-integrity`
Baza: HEAD `main` (SST-Incubator, v0.7.1)
Zakres: naprawy integralności naukowej i reprodukowalności. **Core CLOS
(Kernel, Brain, Genome, Birth, Runtime) nie został naruszony** — zgodnie z
Konstytucją CLOS. Zmiany dotyczą warstwy World (dokumentacja/oznaczenia),
metrologii, provenance i testów.

Wynik testów: **235 passed** (225 oryginalnych + 10 nowych testów ważności).

---

## Decyzja projektowa (PRIORYTET 1 → opcja A)

`stable_world` jest odtąd formalnie **deterministycznym środowiskiem
kontrolnym (Control Environment)**. Zerowa wariancja między seedami jest
cechą OCZEKIWANĄ, nie błędem. Do wklejenia w LessonManifest / dokumentację:

> Stable World jest środowiskiem kontrolnym (Control Environment). Zgodnie z
> projektem jego przebieg jest całkowicie deterministyczny. Wszystkie seedy
> powinny dawać identyczny wynik. Zerowa wariancja jest oczekiwaną cechą
> eksperymentu i stanowi potwierdzenie reprodukowalności bazowej mechaniki Brain.

Konsekwencja metodologiczna (wymuszona w kodzie): dla środowiska kontrolnego
**nie raportujemy cross-seed CI95** (punkt to nie przedział), a effect size
liczymy przez **Glass's delta** względem kontroli.

---

## Naprawione

1. **[BLOCKER] `clos_kernel/kernel.py`** — brak importu `typing.List`.
   Na świeżym klonie (Python 3.12) psuł zbieranie testów → suite w ogóle nie
   startował. Dodano `List` do importu. Bez tego twierdzenie „225 passed"
   nie było prawdą wobec zacommitowanego HEAD.

2. **[P1] `clos_world/scenarios.py` + `generators.py`** — usunięto nieprawdziwe
   docstringi („z pełnym wykorzystaniem seedu"). `stable_world` oznaczony jako
   kontrolny; dodano `CONTROL_ENVIRONMENTS` i `is_control()`, by reszta systemu
   wykrywała determinizm programowo, a nie po komentarzu.

3. **[P1/P2] `clos_curriculum/laboratory/statistics.py`** — metrologia świadoma
   kontroli:
   - `compute_ci95` zwraca `deterministic`, `ci95_valid`, `n_effective`,
     `interpretation`. Przy std=0 CI jest jawnie oznaczone jako niedotyczące.
   - `n_effective` (liczba distinct) chroni przed **pseudoreplikacją** —
     3 identyczne runy to n_eff=1, nie n=3.
   - `glass_delta()` — poprawny effect size przy porównaniu z deterministyczną
     kontrolą (Cohen's d jest tam mylący).
   - `metrology_report()` — pełny blok na jeden warunek.
   Zmiany są ADDYTYWNE — istniejące klucze i sygnatury zachowane.

4. **[P6] `clos_studio/publication/bundle.py`** — provenance:
   - `git_commit` wypełniany automatycznie (`git rev-parse HEAD`), gdy pusty.
   - dodano `config_hash` (sha256 kanonicznego manifestu) i flagę `reproducible`.
   Usuwa lukę: dotąd `metadata.json` miał `git_commit: ""` → run nie był
   w pełni odtwarzalny.

5. **[nowe] `tests/test_scientific_integrity.py`** — 10 testów WAŻNOŚCI:
   kontrola deterministyczna (oczekiwana), shock stochastyczny (std>0),
   flagowanie zdegenerowanego CI, wykrywanie pseudoreplikacji, Glass's delta
   względem kontroli, regresja importu Kernela.

---

## ZNANE, NIENAPRAWIONE (świadomie — wymaga Twojej decyzji lub compute)

- **`drift_world` ignoruje seed**, ale NIE jest oznaczony jako kontrolny —
  jak dawny bug stable. Do rozstrzygnięcia: kontrolny (dodaj do
  `CONTROL_ENVIRONMENTS`) czy stochastyczny (dodaj seed-zależny komponent).
  Oznaczone w docstringu jako known limitation.
- **[P5] Brak eksportu `events.jsonl`** — Observation Engine liczy zdarzenia
  w locie, ale nie zapisuje ich do artefaktów. Panel Observations w oknie
  wizualizacyjnym pozostaje pusty do czasu dodania eksportu.
- **Brak telemetrii per-tick** — artefakty są tylko podsumowaniami runu; nie da
  się narysować serii czasowej bez dodania zrzutu snapshotów.
- **Regeneracja danych** — istniejące artefakty w `publications/` i `datasets/`
  NIE zostały przeliczone. Po zastosowaniu patcha odpal ponownie eksperymenty,
  by manifesty dostały `config_hash`/`git_commit`, a raporty — flagi CI.
- **„Gotowość do publikacji"** — to nie flaga w kodzie. Wymaga większego n na
  warunkach stochastycznych, pre-rejestracji hipotez i replikacji.

---

## Jak zastosować

```bash
git checkout -b v0.7.2-scientific-integrity
git apply v0.7.2-scientific-integrity.patch
python -m pytest -q          # oczekiwane: 235 passed
```
