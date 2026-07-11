# Raport dla architekta — SPRINT v0.9, Priorytet 6 (Kroki 4–5, profil minimalny)

Status: **zaimplementowane, zweryfikowane, NIE zacommitowane.** Core
nietknięty. Nawiązuje do `RAPORT_P6_krok1-3_dla_architekta.md` (Kroki 1–3,
zacommitowane w `824416a` i `a02ac02`).

---

## Co zostało zrobione

`clos_scientist/competency_profile.py` rozdziela teraz wyjście
`build_capability_profile()` na **profil minimalny** i **profil pełny**,
zamiast jednej płaskiej listy 14 pojęć:

- **Profil minimalny (oficjalny)** = wyłącznie pojęcia, dla których
  WSZYSTKIE obecne genomy mają `ci95_valid=True`. Klasyfikacja
  (`_concept_validity_state`) jest jawnie udokumentowana jako lustro
  `clos_studio/panel/panel.js:competencyRowState()` — to samo pytanie
  zadane w dwóch miejscach (artefakt `.md`/`.json` i Panel na żywo) musi
  dawać tę samą odpowiedź.
- **Profil pełny** zachowuje wszystko: `valid` / `degenerate` /
  `insufficient_data` jako trzy rozłączne, wyczerpujące kategorie (test
  `test_full_profile_partitions_all_concepts_into_valid_degenerate_insufficient`
  pilnuje, że suma = 14, bez dziur i bez nakładania).

Nagłówek `.md` liczony z danych: `"Profil minimalny: {summary.valid_ci95}
osi z ważnym CI95 / {summary.total_concepts} pojęć"` — nic wpisane na
sztywno.

`clos_studio/panel/panel.js` (`renderCompetency`) renderuje teraz **dwie
osobne karty**: „Profil minimalny (oficjalny)" i „Profil pełny", obie
liczone z tego samego pobranego JSON, przy użyciu tej samej funkcji
`competencyRowState()`, która już istniała (nie wymagała zmiany logiki —
tylko podziału renderowania na dwie sekcje zamiast jednej).

---

## Wynik — dokładnie 5 osi profilu minimalnego

| Pojęcie | Lekcja | default | highly_plastic |
|---|---|---|---|
| Working Memory | L1.1 | 0.156712 (ci95_valid) | 0.173229 (ci95_valid) |
| Pattern Recognition | L1.1 | 0.151568 (ci95_valid) | 0.150072 (ci95_valid) |
| Pattern Retention | L1.1 | -0.000097 (ci95_valid) | 0.000098 (ci95_valid) |
| Energy Efficiency | L1.1 | 0.460800 (ci95_valid) | 0.413800 (ci95_valid) |
| Homeostatic Resilience | L1.2 | 15.4 (ci95_valid) | **brak** (100% cenzury) |

Profil pełny dodatkowo pokazuje:
- **Zdegenerowane (2):** Adaptation, Stability — zmierzone, ale
  `ci95_valid=False` dla obu genomów (znana przyczyna: pusty
  `snapshot_engine`, patrz `RAPORT_P5_L1.2_dla_architekta.md`).
- **Insufficient data (7):** Perception, Attention, Long-term Memory,
  Prediction, Exploration, Generalization, Planning — brak lekcji/
  mechanizmu.

---

## Weryfikacja

- **pytest -q:** `282 passed` (277 + 5 nowych testów `TestMinimalProfile`),
  `test_step_regression` sprawdzony jawnie osobno — zielony.
- **3 walidatory:** `validate_publication.py` OK (6 bundli),
  `validate_artifacts.py` OK (2 raporty), `validate_panel.py` OK (zero
  wklejonych metryk mimo nowego kodu renderującego w `panel.js`).
- **Panel Badacza w przeglądarce** (lokalne lustro danych, żeby nie czekać
  na push): potwierdzone dwie karty — „Profil minimalny (oficjalny)" 5/14,
  „Profil pełny" zmierzone 7/14 · ważne CI95 5/14. Homeostatic Resilience
  poprawnie w minimalnym (tylko `default`), Adaptation/Stability i
  Perception poprawnie w pełnym.

## git diff --stat (nieskomitowane)

```
clos_scientist/competency_profile.py | 127 +++++++--
clos_studio/panel/panel.js           |  94 ++++---
publications/competency_profile.json | 519 ++++++++++++++++++++++++++++++++++-
publications/competency_profile.md   |  50 +++-
tests/test_competency_profile.py     |  54 +++-
5 files changed, 762 insertions(+), 82 deletions(-)
```

## Co dalej

Priorytet 7 (IDIO-MORPH — dokument hipotezy, status README/ROADMAP na
"Research Grade Infrastructure for Artificial Ontogenesis") i
`RAPORT_v0.9.md` (raport końcowy sprintu) pozostają do zrobienia.
