# MSE→MAE: zasięg zmiany nazwy i dwa warianty (do decyzji CTO)

> **Status: ZREALIZOWANE — Wariant (c), rekomendacja audytora, 2026-07-15/16.**
> Ani (a) pełny rename, ani (b) alias-only — audytor zaproponował trzeci,
> hybrydowy wariant (szczegóły w §5 poniżej), zaimplementowany. Odpowiedź na
> pytanie 2 Zadania 1 CTO dla flagowego endpointu projektu (Working Memory /
> "MSE@50") to **NIE**: pole liczyło `abs()`, nie kwadrat
> (`clos_academy/lesson_L1_1.py:82`). Wartości **0.156712** (default) i
> **0.173229** (highly_plastic) są poprawnym, niezmienionym MAE — to była i
> jest naprawa NAZWY, nie pomiaru; obliczenie NIE zostało ruszone. §1-4
> poniżej to oryginalny zasięg/warianty (a)/(b) przygotowane do decyzji —
> zachowane jako zapis procesu, NIE zaktualizowane retroaktywnie.

## 0. Ważne rozróżnienie — DWIE różne metryki o nazwie "mse"

Repo zawiera **dwa niezależne mechanizmy**, oba nazwane "mse", i nie wolno
ich pomylić:

| | Metryka A (BŁĄD w nazwie) | Metryka B (poprawna, inny podsystem) |
|---|---|---|
| Gdzie | `clos_academy/lesson_L1_1.py` (lekcja L1.1, Pattern Echo) | `clos_scientist/metrics.py::mse()` |
| Formuła | `abs(prediction - pattern_signal)` — **wartość bezwzględna** | `mean((1.0 - energy)**2)` — **poprawnie kwadratowa** |
| Używane przez | `population_validation.py`, `capability_analyzer.py`, `panel.js`, prerejestracje L1.1 | `run_benchmark.py`, `clos_studio/execution/matrix_runner.py`, `clos_dashboard/*`, `clos_research/*`, `clos_curriculum/*` (generyczny pipeline benchmarkowy `full_benchmark_v1`, `EXP-*`) |
| Dotyczy tego zgłoszenia? | **TAK — to jest błąd** | **NIE — poprawna, nie ruszać** |

Warianty (a)/(b) niżej dotyczą **wyłącznie Metryki A** (pola z prefiksem
`mse_` w `lesson_L1_1.py` i tym, co z niego czyta).

---

## 1. Zasięg — wszystkie miejsca z "mse" jako etykietą (Metryka A)

### 1a. Kod źródłowy (definiuje/czyta klucz)

| Plik | Identyfikator | Rola |
|---|---|---|
| `clos_academy/lesson_L1_1.py:82` | `mse_vs_pattern = abs(...)` | definicja — sama formuła (MAE) |
| `clos_academy/lesson_L1_1.py:89` | `"mse_vs_pattern"` (telemetry) | definicja |
| `clos_academy/lesson_L1_1.py:100-103` | `mse_at_tick_50`, `mse_stimulus`, `mse_silence` | definicja (zmienne lokalne) |
| `clos_academy/lesson_L1_1.py:112` | `"metric": "mse_vs_pattern_after_stimulus_removal"` | definicja — nazwa primary_endpoint |
| `clos_academy/lesson_L1_1.py:113` | `"mse_stimulus_phase"`, `"mse_silence_phase"` (klucze output) | definicja — **te dwa klucze to sedno zgłoszenia** |
| `clos_academy/population_validation.py:38,41` | `"Working Memory (MSE@50)"`, `"mse_stimulus_phase"` | konsument (etykieta + odczyt klucza) |
| `clos_scientist/capability_analyzer.py:76` | `r["mse_stimulus_phase"]` | konsument |
| `clos_academy/cognitive_ontology.md` | `mse_stimulus_phase`/`mse_silence_phase`/`mse_at_tick_50` (spec, nie kod) | formalna specyfikacja nazwy pola |

**3 pliki kodu** definiują/czytają klucz bezpośrednio (`lesson_L1_1.py`,
`population_validation.py`, `capability_analyzer.py`).

### 1b. Wygenerowane artefakty (JSON)

- `reports/academy/L1_1_pattern_echo.json` — zawiera `mse_stimulus_phase`/
  `mse_silence_phase` (40 przebiegów). Regenerowany przez
  `clos_academy/publish_L1_1.py`.
- `publications/L1_1_pattern_echo/runs/run_0000.json` … `run_0039.json`
  (**40 plików**) — te same klucze, ten sam generator.
- `reports/population/population_validation_v0_10_1.json` — **BEZ** surowego
  klucza `mse_*`; ma tylko etykietę wyświetlania `"Working Memory (MSE@50)"`.
- `publications/competency_profile.json`/`.md` — **ZERO** wystąpień
  `"mse"` — `capability_analyzer.py` przemianowuje pole na "Pattern
  Recognition" PRZED zapisem, więc surowa nazwa nie wycieka do tego artefaktu.

Razem: **41 plików JSON** z surowym kluczem `mse_*`, wszystkie mechanicznie
regenerowalne (nie ręcznie edytowane), wartości liczbowe bez zmian przy
regeneracji.

### 1c. Czytelnicy (panel, walidatory, testy — regresja przy zmianie)

| Plik | Co robi z kluczem |
|---|---|
| `clos_studio/panel/panel.js:203,248,341,356,358` | `mseChartSvg()`, aria-label, **`passCond.mse_at_tick_50_max`** (czyta z prerejestracji), nagłówek karty "MSE @ 50" |
| `tests/test_new_environments_p2.py` | `L1_1_EXECUTION_FIELDS` zawiera dosłowne `"mse_stimulus_phase"`, `"mse_silence_phase"` — golden regression |
| `tests/test_observer_removability.py` | to samo, ten sam cel |
| `tests/test_capability_analyzer.py` | asercja `"Pattern Recognition": "mse_stimulus_phase"` |
| `scripts/validate_panel.py`, `validate_artifacts.py` | **BEZ** literalnego sprawdzania klucza `mse_*` — bezpieczne |

**3 pliki testów + panel.js** złamałyby się przy zmianie nazwy klucza bez
jednoczesnej aktualizacji.

### 1d. Prerejestracje (dokumenty rządzące, część "zamrożona")

| Plik | Pole | Status |
|---|---|---|
| `publications/preregistration_L1_1.json` | `"metric": "mse_after_stimulus_removal"`, `"mse_at_tick_50_max"`, `"mse_at_tick_50_min"` | **formalna, zamrożona** (BRAMKA v0.9.3) |
| `publications/preregistration_L1_1_v0.8.json` | to samo | wcześniejsza zamrożona wersja |
| `publications/preregistration_v0_10_1_population.json` | prosa + `"Working Memory (MSE@50)"` | referencja, nie definicja |
| `publications/preregistration_v0_11_0_power_reproduction.json` | prosa (`mse_stimulus_phase`, `mse_vs_pattern_after_stimulus_removal`) | referencja |

**2 dokumenty formalnie definiują nazwę pola jako kryterium bramki** — zmiana
tutaj to zmiana ZATWIERDZONEGO dokumentu audytowego, nie tylko kodu.

### 1e. Dokumentacja narracyjna (prosa, ~13 plików)

`docs/VALIDITY_REPORT.md` (już zawiera pełny opis TEGO DOKŁADNIE błędu —
sekcja Pattern Recognition, Krok 2 P1 tego sprintu — to jest już
udokumentowane, nie nowe odkrycie w kodzie dokumentacji), `docs/REPLICATION.md`,
`docs/CURRENT_SCIENTIFIC_LIMITS.md`, `docs/ROBUSTNESS_MATRIX.md`,
`docs/spec_partial_step.md`, `docs/spec_snapshot_observer.md`,
`RAPORT_KONCOWY_v0.8.4.md`, `RAPORT_v0.10.md`, `SPRINT_v0.8.5.md`,
`SPRINT_v0.9.md`, `README.md`, `ROADMAP.md` — wzmianki "MSE@50" w prozie/
tabelach, kosmetyczne, nie wpływają na działanie kodu.

---

## 2. Dwa warianty do decyzji CTO

### Wariant (a) — PEŁNA ZMIANA NAZWY (`mse_*` → `mae_*` wszędzie)

**Zakres zmiany:** 3 pliki kodu (`lesson_L1_1.py`, `population_validation.py`,
`capability_analyzer.py`) + 3 pliki testów + `panel.js` (klucz + etykieta
"MAE @ 50") + regeneracja 41 plików JSON (`reports/academy/L1_1_pattern_echo.json`,
40× `publications/L1_1_pattern_echo/runs/*.json`) + **nowa, wersjonowana
poprawka** (nie edycja w miejscu) dla `preregistration_L1_1.json`.

**Dowód nieszkodliwości:** wartości liczbowe bajtowo niezmienione
(0.156712/0.173229/próg 0.5) — to czysty rename, zero zmiany obliczenia,
weryfikowalne tym samym testem regresji co teraz (`test_genome_params_regression.py`
działa na wartościach, nie na nazwach kluczy).

**Ryzyko:**
- Dotyka **opublikowanych, zreplikowanych** artefaktów — ślepa replikacja
  audytora (Linux/Python 3.12, `docs/REPLICATION.md`) była wykonana
  względem STARYCH nazw kluczy; rename bez jasnego, wersjonowanego
  uzasadnienia w CHANGELOG mógłby wyglądać jak "przepisywanie historii"
  publikacji, nie jak korekta.
- `preregistration_L1_1.json` to zatwierdzona BRAMKA (v0.9.3) — zmiana pola
  w niej wymaga formalnej poprawki/aneksu, nie cichej edycji.
- Każdy zewnętrzny konsument, który już zapisał się na klucz `mse_stimulus_phase`
  (np. przyszły reviewer replikujący ponownie), dostanie inny klucz bez
  ostrzeżenia, jeśli nie przeczyta CHANGELOG.

**Co widzi recenzent:** w pełni spójna, poprawna terminologia od kodu po
publikację — najsilniejszy sygnał rzetelności ("naprawili to, gdy znaleźli"),
ALE wymaga przekonującego, jawnego zapisu PRZEJŚCIA (stara nazwa → nowa,
z datą i uzasadnieniem), inaczej wygląda na cichą korektę historii.

### Wariant (b) — ALIAS + JAWNA DOKUMENTACJA (klucze zostają)

**Zakres zmiany:** 1 plik kodu (`lesson_L1_1.py`) — dodanie pola
`"metric_definition": "mean absolute error (MAE), NOT MSE — historical misnomer, verified SPRINT_v0.11.0.md"`
obok `mse_stimulus_phase`/`mse_silence_phase`/`primary_endpoint` w output
dict; opcjonalnie dopisek w `panel.js` (tekst, nie klucz) i wzmianka w
`preregistration_L1_1.json` jako ANEKS (nowe pole, nie edycja
istniejącego). `docs/VALIDITY_REPORT.md` już ma pełny opis (Krok 2) —
zero dodatkowej pracy tam.

**Ryzyko:**
- Klucz **nadal kłamie** w każdym miejscu, gdzie ktoś czyta JSON bez
  czytania `metric_definition`/dokumentacji — dokładnie to przydarzyło się
  audytorowi PRZEZ 6 SPRINTÓW, mimo dostępu do kodu i cytowania "MSE@50" w
  raportach. Jawna dokumentacja obok kłamliwego klucza nie gwarantuje, że
  ktoś ją przeczyta przed zacytowaniem klucza.
- Nie usuwa problemu "cisza gorsza niż błąd" w łagodniejszej formie: nazwa
  wciąż aktywnie sugeruje złą operację statystyczną każdemu, kto widzi tylko
  klucz (np. w szybkim `grep`, w cudzym skrypcie analitycznym, w abstrakcie
  przyszłej publikacji, jeśli ktoś skopiuje nazwę pola bez namysłu).

**Co widzi recenzent:** recenzent, który dokładnie czyta
`metric_definition`/`VALIDITY_REPORT.md`, dostaje pełną, uczciwą informację
natychmiast, bez ryzyka dla ciągłości opublikowanych artefaktów. Recenzent,
który tylko przegląda JSON/panel pobieżnie, nadal zobaczy `"mse_stimulus_phase"`
i może błędnie zacytować "MSE" — tak jak już się zdarzyło.

---

## 3. Co NIE zostało zrobione (historyczne, w momencie przygotowania §1-2)

- Obliczenie (`abs()` w `lesson_L1_1.py:82`) **nie zostało zmienione** —
  0.156712/0.173229 pozostają nietknięte (nadal prawda po §5).
- W momencie przygotowania tego dokumentu żaden wariant nie był jeszcze
  wybrany. **Od §5 poniżej: wybrany i zaimplementowany Wariant (c).**

---

## 4. Czy ten sam wzorzec (nazwa obiecuje więcej niż formuła) występuje gdzie indziej?

Sprawdzone (formuły już sformalizowane w `docs/VALIDITY_REPORT.md` Krok 2 —
**to NIE są nowe odkrycia tego zgłoszenia**, ale potwierdzają, że wzorzec
jest systemowy, nie odosobniony do MSE):

- **`stability_score`** (`clos_scientist/metrics.py`, `1/(std_entropy+std_error+1e-6)`,
  `error=|1-energy|`) — nazwa "Stability" jest szeroka/interpretacyjna, nie
  tak MECHANICZNIE fałszywa jak MSE→MAE (nie ma tu "złej operacji
  matematycznej", jest PROXY + skala odwrotna nieliniowa). Mismatch łagodniejszy.
- **`final_energy` / etykieta "Energy Efficiency"** (`population_validation.py`,
  `capability_analyzer.py`) — **NIE ISTNIEJE żadna formuła efektywności**:
  to surowa wartość energii w OSTATNIM ticku (`round(tissue.energy, 6)`), nie
  stosunek/wydajność żadnego rodzaju. W pewnym sensie ten mismatch jest
  **WIĘKSZY** niż MSE/MAE — MSE/MAE przynajmniej mierzy poprawny RODZAJ
  wielkości (błąd predykcji), tylko złą operację statystyczną;
  "Energy Efficiency" nie mierzy efektywności/stosunku w ogóle. Już
  oznaczone w `VALIDITY_REPORT.md` (Krok 2) jako "największy mismatch
  nazwa/pomiar spośród 7 zmierzonych osi".
- **Sprawdzone i WYKLUCZONE:** żadna INNA metryka nie ma tego SAMEGO
  mechanicznego błędu (kwadrat zamiast wartości bezwzględnej, lub odwrotnie).
  Druga funkcja o nazwie `mse` w repo (`clos_scientist/metrics.py::mse()`,
  używana przez generyczny pipeline benchmarkowy — `run_benchmark.py`,
  `clos_studio/execution/matrix_runner.py`, `clos_dashboard/*`) jest
  **poprawnie kwadratowa** — nie pomylić z Metryką A.

**Wniosek:** wzorzec "nazwa obiecuje więcej niż formuła dostarcza" jest
systemowy (Stability, Energy Efficiency, Homeostatic Resilience — patrz
`VALIDITY_REPORT.md` — wszystkie już udokumentowane w Kroku 2 tego sprintu),
ale MSE/MAE jest JEDYNYM przypadkiem o charakterze mechanicznego błędu
matematycznego (zła operacja: kwadrat vs abs) możliwym do jednoznacznego
zweryfikowania w kodzie — stąd odrębne, węższe pytanie od CTO.

**Aktualizacja 2026-07-16/17:** audytor potwierdził w kodzie, że Energy
Efficiency (`final_energy`) jest GORSZYM przypadkiem niż MSE/MAE — to nie
błąd NAZWY (zła operacja na tej samej wielkości), tylko błąd KATEGORII
(efektywność = stosunek; `final_energy` = poziom w jednym punkcie czasu; w
kodzie nie ma żadnej formuły efektywności, i nie ma czego dzielić przez
energię, bo `act()` jest echem — system nie ma wyjścia). To pytanie
ONTOLOGICZNE (czy pojęcie "Energy Efficiency" w ogóle powinno istnieć w tej
formie), nie nazewnicze — rozstrzygane OSOBNO, patrz
`docs/ENERGY_EFFICIENCY_ONTOLOGY_DECISION.md`. Nie mieszane z Wariantem (c)
poniżej, mimo wspólnego pochodzenia (ten sam audyt formalnych definicji, P1).

---

## 5. Decyzja: Wariant (c) — rekomendacja audytora, zaimplementowana

Ani (a) pełny rename, ani (b) alias-only. Audytor zaproponował wariant
hybrydowy, przyjęty i zrealizowany:

1. **Zamrożone prerejestracje NIE edytowane.** `publications/preregistration_L1_1.json`
   i `_v0.8.json` pozostają z historyczną nazwą `mse_*` — ślad audytowy
   ważniejszy niż czysty dokument. Zamiast edycji: nowy, datowany aneks
   `publications/preregistration_L1_1_ANEKS_2026-07-15_MSE_do_MAE.json`
   (osobny plik, cross-referencing oryginałów, `amendment_date: 2026-07-15`).
2. **Nazwa zmieniona W KODZIE, od teraz.** `clos_academy/lesson_L1_1.py`
   (definicja + wszystkie lokalne zmienne), `clos_academy/population_validation.py`,
   `clos_scientist/capability_analyzer.py`, `clos_studio/panel/panel.js`
   (etykiety wyświetlania + nazwa funkcji `mseChartSvg`→`maeChartSvg`;
   `passCond.mse_at_tick_50_max` CELOWO NIE zmienione — czyta nazwę pola z
   zamrożonej prerejestracji), `clos_academy/cognitive_ontology.md` (spec
   pojęć). Klucze: `mse_stimulus_phase`→`mae_stimulus_phase`,
   `mse_silence_phase`→`mae_silence_phase`,
   `mse_vs_pattern_after_stimulus_removal`→`mae_vs_pattern_after_stimulus_removal`.
   Wartości liczbowe (0.156712/0.173229) bez zmian — zweryfikowane testem
   regresji (`tests/test_genome_params_regression.py`, 408/408 testów
   zielonych po zmianie).
3. **Stare artefakty zostają — FORMALIZOWANE 2026-07-17 (aktualizacja po
   decyzji CTO).** `publications/L1_1_pattern_echo/` (40 plików runs, już
   opublikowany/zreplikowany bundle — blind replication Linux/Python 3.12)
   NIE regenerowane, zachowuje stare klucze `mse_*`. To już NIE jest tylko
   nieformalna decyzja "zostawmy jak jest" — `metadata.json` ma teraz
   jawne `"frozen": true` + `"frozen_reason"` + `"regeneration_expected_diff"`
   (dokładny opis co konkretnie zmieniłoby się przy regeneracji), status
   `"Frozen Historical Artifact"`. Egzekwowane przez nowy walidator
   `scripts/validate_bundle_freshness.py` — `frozen=true` jest JEDYNYM
   dopuszczalnym wyjątkiem od zasady "kod==artefakt"
   (`clos_studio/publication/bundle.py`), kontrolowanym równie rygorystycznie
   jak sama reguła (frozen bez pełnego uzasadnienia = FAIL, 4 scenariusze
   testowe w `tests/test_bundle_freshness_validator.py`). Wyjątek: `reports/academy/L1_1_pattern_echo.json`
   — to wewnętrzny golden-baseline dla testów regresyjnych (nie publikowany
   externally), regenerowany (`python -m clos_academy.lesson_L1_1`), zawiera
   teraz `mae_*`, wartości identyczne.
4. **`clos_scientist/metrics.py::mse()` nietknięta** — poprawna, kwadratowa,
   niezwiązana z tym znaleziskiem.

Zaktualizowane testy golden-field-list (analogicznie do Kroku 3/P2):
`tests/test_new_environments_p2.py`, `tests/test_observer_removability.py`,
`tests/test_capability_analyzer.py`. `docs/VALIDITY_REPORT.md` (sekcje
Pattern Recognition, Pattern Retention, Working Memory) i
`clos_academy/cognitive_ontology.md` zaktualizowane do nowych nazw, z
zachowaniem zapisu historii odkrycia. Wszystkie 4 walidatory zielone. Nic z
tego nie zostało zacommitowane — czeka na Twoje OK.
