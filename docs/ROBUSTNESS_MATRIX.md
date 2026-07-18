# Robustness Matrix — kiedy ufać metryce, kiedy nie

> **⚠ STATUS DANYCH: Exploratory Dataset v0.10 (SPRINT_v0.11.0.md).** Ta
> macierz jest zbudowana na populacji n=10/genom (v0.10.1 P3), o ktorej
> analiza mocy (v0.11.0 P0) wykazala bardzo niska moc wykrywania efektow
> innych niz ogromne po korekcie na wielokrotne porownania (patrz
> `publications/preregistration_v0_11_0_power_reproduction.json`). **Macierz
> NIE jest poprawiana ani wycofywana** — kazdy ✔/✘/◐ ponizej pozostaje
> prawdziwym zapisem tego, co wykryto na n=10. Kolumny dotyczace genomu/
> srodowiska/seeda maja status **Measurement/Construct validity: aktualny**;
> **Power/Confirmatory validity: PENDING** do czasu re-run zatwierdzonego
> przez CTO (Wariant A/B/C — decyzja w toku).

**Status: SPRINT_v0.10.1.md P5 (Zadanie 4 CTO).** Dokument dla przyszłych
autorów eksperymentów: tabela każda z 7 zmierzonych osi × {genom, środowisko,
seed, obserwacja, refaktoryzacja}. Każdy ✔/✘/◐ wynika z konkretnych danych
P2/P3 (referencje w tekście pod tabelą) — żaden nie jest założeniem. **✘ jest
oczekiwanym, cennym wynikiem, nie porażką dokumentu** (SPRINT_v0.10.1.md,
zasada nadrzędna). Osie insufficient_data (Perception, Attention, Long-term
Memory, Prediction, Exploration, Generalization, Planning) są pominięte —
nie ma czego wpisać do macierzy dla pomiaru, który nie istnieje.

---

## KRYTYCZNE: mierzalność ≠ dyskryminacja (dwie osobne kolumny, nie jedna)

**Nie wolno łączyć tych dwóch pytań w jeden symbol ✔/✘** —
`docs/VALIDITY_REPORT.md` §"Kluczowe odkrycie" pokazuje dlaczego: Working
Memory jest **100% MIERZALNA** (realna wariancja międzyseedowa, CI95 ważne
dla każdego z 23 genomów) ale **0% DYSKRYMINUJĄCA** (zero z 253 par genomów
przeżywa korektę FDR). Jeden zlany symbol ✔ dla obu pytań naraz
skłoniłby czytelnika do wniosku **odwrotnego** do danych — "Working Memory
działa dobrze i widać w niej różnice między genomami" — podczas gdy prawda
to "Working Memory działa dobrze, ale w tej próbce nie widać w niej różnic
między genomami". Stąd w tabeli niżej kolumna "Genom" jest rozbita na dwie:
**Genom (mierzalność)** i **Genom (dyskryminacja)**.

---

## Tabela główna

Legenda: ✔ = potwierdzone pozytywnie danymi · ✘ = potwierdzone negatywnie
(fragile/brak sygnału) danymi · ◐ = częściowe/mieszane, zależne od kontekstu
· — = nie dotyczy (metryka nie istnieje w tym kontekście, patrz name-gate).

| Metryka | Genom (mierzalność) | Genom (dyskryminacja, FDR) | Środowisko | Seed | Obserwacja | Refaktoryzacja |
|---|---|---|---|---|---|---|
| Pattern Recognition | ✔ 100% (2/2 środ.) | ✘ 0/253 w obu | ✔ spójna w 2/2 testowanych | ✔ | ✔ | ✔ (3/3 refaktory) |
| Pattern Retention | ✔ 100% (2/2 środ.) | ✘ 0/253 w obu | ✔ spójna w 2/2 testowanych | ✔ | ✔ | ✔ (3/3 refaktory) |
| Working Memory | ✔ 100% (2/2 środ.) | ✘ 0/253 w obu | ✔ spójna w 2/2 testowanych | ✔ | ✔ | ✔ (3/3 refaktory) |
| Stability | ✔ 100% (4/4 środ. nie-kontr.) | ✔ 22-92% par, silnie | ✔ spójna w 4/4 testowanych | ✔ | ✔¹ | ◐² |
| Adaptation | ✘ 35-43% (L1.1) / 0% (L1.2) | ✔ gdy mierzalna | ✘ silnie zależna od lekcji/env | ◐³ | ✔¹ | ◐² |
| Energy Efficiency | ◐ 39-100% zależnie od kontekstu | ✔ gdy mierzalna | ✘ silnie zależna od lekcji/env | ◐³ | ✔ | ✔ (3/3 refaktory) |
| Homeostatic Resilience | ✘ 21.7% | ✔ 8/10 par (mała próba) | ✘ tylko 1/3 środ.⁵ | ◐³ | ✔ | ✔⁴ |

Kolumna "Środowisko" pokrywa WYŁĄCZNIE środowiska z pełną analizą
populacyjną P3 (`noise_world`/`stable_world`/`drift_world` dla L1.1;
`shock_world`/`stable_world`/`drift_world` dla L1.2). **5 dodatkowych
środowisk z P2** (`high_noise_world`, `recurring_shock_world`,
`weak_shock_world`, `long_stable_shock_world`, `unpredictable_world`) mają
TYLKO dowód usuwalności obserwatora + regresję + telemetrię (smoke-test na
2 genomach × 3 seedy) — **NIE mają pełnej analizy ROBUST/FRAGILE per
metryka na populacji 23 genomów.** To jest jawna luka pokrycia (patrz
"Czego ta macierz NIE pokrywa" na końcu), nie przeoczenie.

¹ Adaptation/Stability SĄ produktem Observation Pipeline (liczone z
`snapshot_diagnostics`) — "✔" tu znaczy: mechanizm producenta (Read-Only
Observer) jest dowiedziony jako nie-wpływający na Execution, NIE że sama
wartość jest niezmienna między obserwacją włączoną/wyłączoną (przeciwnie —
MUSI się zmieniać, patrz `docs/architecture.md` §2).
² Formuła (`detect_phases()`/`stability_index()`) nie zmieniła się przez
żaden refaktor — ale WARTOŚCI legalnie zmieniły się w v0.10 (obserwator
włączony pierwszy raz dostarczył realne dane zamiast zawsze-zero) — to
zamierzona naprawa długu, nie regresja, stąd ◐ zamiast ✔.
³ Seed-oś dla tych metryk jest w praktyce tym samym pytaniem co
"Genom (mierzalność)" (n_effective per genom) — ◐ odzwierciedla, że część
populacji ma wysoką n_effective, część nie (patrz kolumna mierzalności).
⁴ Regresja formalna istnieje dla primary_endpoint na `shock_world`
(`tests/test_genome_params_regression.py`), ale NIE dla pozostałych 2
środowisk (`stable_world`/`drift_world`), gdzie pole w ogóle nie istnieje —
regresja "pusta" tam jest trywialnie prawdziwa, nie testowana wprost.
⁵ W SPRINT_v0.10.1.md P2 ta luka nazywała się "name-gate": brak endpointu w
`stable_world`/`drift_world` (żaden z nich, słusznie — brak zdarzenia
perturbacyjnego) był METODOLOGICZNIE POMIESZANY z osobnym, prawdziwym
name-gate bugiem (`weak_shock_world`/`long_stable_shock_world` też
pomijane, mimo że MAJĄ pojedynczą perturbację). SPRINT_v0.11.0.md P2
naprawił bug (`clos_world.scenarios.has_single_perturbation()`, patrz
`VALIDITY_REPORT.md` sekcja Homeostatic Resilience) — TA linia (1/3 środ. w
już przeprowadzonej populacji P3) pozostaje niezmieniona, bo dotyczy
`stable_world`/`drift_world`, które genuinely nie mają zdarzenia do
zmierzenia, nie były objęte bugiem.

---

## Genom (mierzalność) — źródło danych

`reports/population/population_validation_v0_10_1.json`, 23 genomy (20 LHS
+ 3 anchor), próg `n_effective≥5` (`preregistration_v0_10_1_population.json`).
Dokładne liczby per (lekcja, środowisko) — patrz `docs/VALIDITY_REPORT.md`,
sekcje per oś. Skrót:

- **Zawsze ✔ niezależnie od genomu:** Pattern Recognition, Pattern
  Retention, Working Memory (w `noise_world`/`drift_world`); Stability
  (we wszystkich 4 nie-kontrolnych kontekstach).
- **Zawsze ✘ niezależnie od genomu:** Adaptation w L1.2 (0/23, wszystkie
  środowiska — strukturalny name-gate/okno-przed-szokiem, nie
  genomo-zależny).
- **Zależne od konkretnego genomu:** Adaptation w L1.1 (35-43%), Energy
  Efficiency (39-100%), Homeostatic Resilience (21.7%) — patrz
  `VALIDITY_REPORT.md` dla hipotezy post-hoc (`decay_rate`, nieprzetestowanej
  niezależnie) o tym, KTÓRE konkretnie genomy wypadają ✘.

## Genom (dyskryminacja) — źródło danych

Ta sama próbka, Welch's t-test + Benjamini-Hochberg FDR (q=0.05) między
wszystkimi parami genomów z `valid_population=True`
(`clos_curriculum/laboratory/statistics.py:welch_t_test`,
`benjamini_hochberg`). **Wzorzec nieoczywisty:** metryki idealnie mierzalne
(Pattern Recognition/Retention/Working Memory) mają ZERO dyskryminacji;
metryki tylko częściowo mierzalne (Adaptation/Energy Efficiency/Homeostatic
Resilience) dyskryminują SILNIE wśród genomów, które akurat przechodzą próg
mierzalności. To sugeruje: tam gdzie mechanizm degeneruje się selektywnie
(zależnie od genomu), ta sama selektywność koreluje z realną różnicą między
ocalałymi genomami — ale to obserwacja, nie dowód przyczynowy.

## Środowisko — źródło danych

P3 (`clos_academy/population_validation.py`, `LESSON_ENVIRONMENTS`): L1.1
× {`noise_world`, `stable_world`, `drift_world`}, L1.2 × {`shock_world`,
`stable_world`, `drift_world`}. `stable_world` we WSZYSTKICH przypadkach
0% mierzalności — **oczekiwane i poprawne** (środowisko deterministyczne,
`n_effective=1` z definicji dla każdego genomu), nie liczone jako "✘ tej
metryki", tylko jako potwierdzenie, że mechanizm pseudoreplikacji działa.
Rzeczywisty sygnał "✔/✘ środowiskowy" w tabeli powyżej pochodzi z porównania
`noise_world`/`shock_world` (podstawowy) vs `drift_world` (nowy,
eksploracyjny) — metryki takie jak Adaptation/Energy Efficiency/Homeostatic
Resilience zmieniają klasyfikację (czasem znacząco) między tymi dwoma, co
kwalifikuje je jako "✘ silnie zależna od środowiska" w tabeli.

## Seed — źródło danych

`n_effective` (`_n_effective()`, `clos_curriculum/laboratory/statistics.py`)
liczone jako liczba DYSTYNKTYWNYCH wartości wśród 10 seedów per genom —
mechanizm ochrony przed pseudoreplikacją, ten sam od v0.7.2. Dowód, że
mechanizm działa poprawnie: `stable_world` (deterministyczny) daje
`n_effective=1` dla KAŻDEGO z 23 genomów, na KAŻDEJ metryce, bez wyjątku —
gdyby to nie było prawdą, wskazywałoby na błąd w samym liczniku
`n_effective`, nie w metryce.

## Obserwacja — źródło danych

Dowód usuwalności (`docs/architecture.md` §2-3): `tests/test_observer_removability.py`
(v0.10 P1/P2, L1.1 40/40 + L1.2 podzbiór) i
`tests/test_new_environments_p2.py` (v0.10.1 P2, 31 testów, 6 środowisk ×
2 lekcje × 2 genomy × 3 seedy) — pola Execution bajtowo identyczne z
obserwatorem włączonym/wyłączonym w KAŻDYM sprawdzonym przypadku, bez
wyjątku. To dowód o MECHANIZMIE (Read-Only Observer), nie per-metryka —
stąd ✔ jest jednolite dla wszystkich 7 osi.

## Refaktoryzacja — źródło danych

Trzy niezależne refaktory, każdy z formalnym testem regresyjnym:

1. **v0.9 `partial_step()`** (`tests/test_partial_step.py`,
   `tests/test_capability_analyzer.py::test_protected_l1_1_concepts_unchanged_by_refactor`) —
   3 pojęcia zasilane wyłącznie z L1.1 (Pattern Recognition, Pattern
   Retention, Energy Efficiency) zweryfikowane jako bajtowo identyczne
   przed/po refaktorze N:M.
2. **v0.10 Read-Only Observer** (`tests/test_observer_removability.py`) —
   pola Execution (w tym `mse_stimulus_phase`, `memory_decay_rate`,
   `primary_endpoint`, `final_energy`) bajtowo identyczne; Adaptation/
   Stability CELOWO się zmieniły (naprawa długu, nie regresja — stąd ◐, nie
   ✔, w tabeli głównej dla tych dwóch).
3. **v0.10.1 `genome_params`** (`tests/test_genome_params_regression.py`) —
   pełne słowniki wyników (obejmujące Pattern Recognition/Retention/Working
   Memory/Energy Efficiency/Homeostatic Resilience na `shock_world`)
   porównane run-po-runie z już zacommitowanymi raportami — zero różnicy.

**Nie testowano:** wpływu żadnego z tych 3 refaktorów na 5 nowych środowisk
P2 w kontekście regresji WARTOŚCI metryk (tylko usuwalność/telemetria/brak
zmiany w L1.1/L1.2 pierwotnych scenariuszach) — patrz luka pokrycia niżej.

---

## Czego ta macierz NIE pokrywa (jawne, nie ukryte)

- **5 z 9 istniejących środowisk nie ma pełnej analizy populacyjnej**
  (tylko smoke-test P2) — kolumna "Środowisko" w tabeli głównej opisuje
  wyłącznie 3 środowiska per lekcję z P3.
- **Żadna metryka nie była testowana na TRZECIEJ, strukturalnie innej
  lekcji** poza L1.1/L1.2 — macierz odporności "między lekcjami" ma tylko
  2 punkty danych (L1.1, L1.2), nie populację lekcji.
- **Próg `n_effective≥5` i próg GENOME-ROBUST 80%** są prerejestrowanymi
  wyborami projektowymi (uzasadnionymi, ale wyborami) — inny próg dałby
  inny rozkład ✔/✘ w kolumnach mierzalności. Macierz jest wrażliwa na te
  stałe, nie jest "obiektywnym faktem" niezależnym od metodologii.
- **Hipotezy post-hoc** (korelacja z `decay_rate` z `VALIDITY_REPORT.md`)
  NIE są tu użyte do przewidywania ✔/✘ dla nowych genomów — tabela opisuje
  TYLKO to, co zaobserwowano w tej konkretnej próbce 23 genomów.
