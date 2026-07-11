# Raport dla architekta — SPRINT v0.9, Priorytet 6 (Kroki 1–3) + Odkrycie #1

Status: **Krok 1 zacommitowany (`824416a`). Kroki 2–3 zaimplementowane,
zweryfikowane, NIE zacommitowane** — zatrzymanie na wyraźne żądanie przed
Krokiem 4 (profil minimalny). Core nietknięty przez cały priorytet.

---

## Krok 1 — porządek w raportach (zacommitowany)

`reports/shock_recovery_report.json` (506 B) porównany bajtowo z
`reports/academy/L1_2_shock_recovery.json` (26 585 B):

- SHA256 różne, 1019 linii różnicy w `diff`.
- **Nie duplikat.** To osobny, mniejszy plik — surowy wynik pojedynczego
  `run_experiment("shock_recovery", ...)` z wcześniejszego, eksploracyjnego
  testu podczas implementacji L1.2 (ten sam artefakt, który udokumentował
  pusty `snapshot_engine`: `stability_score:0.0`, `phases` same zera).

Zgodnie z instrukcją ("jeśli inny — commituj oba") skomitowany razem z
`RAPORT_P5_L1.2_dla_architekta.md` w commicie `824416a`.

---

## Krok 2 — 14. pojęcie: Homeostatic Resilience

Dodane do `clos_academy/cognitive_ontology.md` (nieskomitowane). Pełna
definicja:

**(a) Opis poznawczy:** Zdolność systemu do **osiągnięcia i utrzymania**
pasma homeostazy po stochastycznej perturbacji — niezależnie od tego, czy
Brain był w tym paśmie PRZED perturbacją. Ta sama metryka mierzy dwa różne
zjawiska w zależności od stanu wyjściowego:
- BYŁ w paśmie przed perturbacją → metryka mierzy **powrót** (recovery);
- NIE BYŁ w paśmie przed perturbacją → metryka mierzy **pierwsze
  osiągnięcie/ustanowienie** (establishment), nie odzyskanie.

Które z dwóch zjawisk mierzy dany przebieg, rozstrzyga się **z danych**
(`pre_shock_in_band_fraction`), nie z góry.

**(b) Mierzalny korelat:** `time_to_sustained_band` (lub `recovery_time`,
zależnie od przypadku powyżej) — `clos_academy/lesson_L1_2.py`,
`compute_recovery_time()`; pasmo wprost z progów w `regulate()`. Formalna
definicja: `publications/preregistration_L1_2.json`.

**(c) Lekcja:** L1.2 (primary endpoint). **Obecny wynik L1.2 to przypadek
osiągnięcia, NIE powrotu**: `pre_shock_in_band_fraction = 0.0` dla obu
genomów (próg rozstrzygający: 0.8) — hipoteza "Brain odzyskuje homeostazę"
skorygowana w raporcie L1.2 na "Brain **osiąga/ustanawia** homeostazę po
szoku", zgodnie z regułą `pre_shock_band_check` z prerejestracji.

Przy okazji zaktualizowany nagłówek dokumentu (wcześniej mówił "istnieje
jedna lekcja: L1.1" — nieaktualne po L1.2; teraz wymienia obie).

---

## Krok 3 — CapabilityAnalyzer: refaktor na relację N:M

**Architektura:** `CONCEPT_METRIC_MAP` mapuje teraz pojęcie → **lista**
`{lesson, extract}` (wcześniej: pojedynczy dict). `analyze_concept()`
agreguje wartości ze wszystkich lekcji na liście per genom, filtruje
`None` (np. runy ucenzurowane) przed liczeniem CI95 — nie liczy ich jako 0.

**Kompatybilność wsteczna:** pole `source_lesson` zostało jako string (jak
dotąd — `"L1.1"`, albo `", "`-złączone przy wielu lekcjach), więc
`clos_scientist/competency_profile.py` i `clos_studio/panel/panel.js`
(Panel Badacza, już wdrożony na GitHub Pages) **nie wymagają żadnej
zmiany**. Nowe, listowe pole `source_lessons` dodane addytywnie obok.

### Regresja krytyczna — dowód

Migawka `build_capability_profile()` zapisana PRZED edycją pliku, porównana
pole-po-polu z wynikiem PO refaktorze (ignorując wyłącznie nowe, addytywne
pole `source_lessons`, którego przed refaktorem nie było):

```
Working Memory:      IDENTICAL=True
Pattern Recognition: IDENTICAL=True
Pattern Retention:   IDENTICAL=True
Energy Efficiency:   IDENTICAL=True
```

Dodatkowo: nowy, stały test regresji
`test_protected_l1_1_concepts_unchanged_by_refactor`
(`tests/test_capability_analyzer.py`) porównuje te same 3 z 4 pojęć
(Pattern Recognition, Pattern Retention, Energy Efficiency) niezależnie,
bezpośrednio z surowego `reports/academy/L1_1_pattern_echo.json` — nie
tylko jednorazowa migawka, ale trwała ochrona w CI. Working Memory miało
już taki test wcześniej (`test_working_memory_value_matches_report`).

### Homeostatic Resilience zasilone z L1.2

```json
{
  "concept": "Homeostatic Resilience",
  "status": "measured",
  "source_lesson": "L1.2",
  "source_lessons": ["L1.2"],
  "genomes": {
    "default": {
      "value": 15.4, "std": 4.247875,
      "ci95_low": 12.76714, "ci95_high": 18.03286,
      "n": 10, "n_effective": 7, "ci95_valid": true
    }
  },
  "genome_comparison": null
}
```

- `default`: ważny CI95 (jak wymagano).
- `highly_plastic`: **nieobecny** w `genomes` — 100% cenzury w L1.2, zero
  wartości (nie `null`, nie `0`, po prostu brak klucza).
- `genome_comparison`: **`null`**, jawnie — Cohen's d nieobliczalny (jedna
  grupa pusta), nie fałszywe `0.0`.

### Nowe testy

- `TestHomeostaticResilienceFromL12` — 2 testy (measured/absent, Cohen's d
  None).
- `TestConceptMetricMapIsNtoM` — 2 testy (kształt listowy `CONCEPT_METRIC_MAP`
  na stałe; regresja 3 pojęć L1.1 z surowego raportu).
- `tests/test_capability_analyzer.py::test_all_concepts_present_and_match_ontology_names`
  zaktualizowany o "Homeostatic Resilience" (14 pojęć).
- `tests/test_competency_profile.py` — 4 asercje `== 13` → `== 14`
  (`competency_profile.py` samo w sobie nie wymagało zmian kodu — tylko
  liczba pojęć w testach).

---

## Stan testów

| Sprawdzenie | Wynik |
|---|---|
| `pytest -q` | **277 passed** (273 + 4 nowe) |
| `test_step_regression` | zielony, sprawdzony jawnie osobno |
| Core (`clos_brain/`, `clos_kernel/`, `genome/`, `birth/`) | nietknięty |

## git diff --stat (nieskomitowane)

```
clos_academy/cognitive_ontology.md    |  49 ++++++++++++-
clos_scientist/capability_analyzer.py | 127 ++++++++++++++++++++++------------
tests/test_capability_analyzer.py     |  62 ++++++++++++++++-
tests/test_competency_profile.py      |  12 ++--
4 files changed, 196 insertions(+), 54 deletions(-)
```

## Co dalej (nie zrobione, czeka na decyzję)

Krok 4–5 (profil minimalny — Competency Profile ograniczony wyłącznie do
pojęć z `ci95_valid=True`, pełny profil zachowuje zdegenerowane/
insufficient_data jako osobną kategorię) — celowo wstrzymane, zgodnie z
instrukcją "ZATRZYMAJ SIĘ po Kroku 3".
