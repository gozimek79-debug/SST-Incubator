# SPECYFIKACJA KANONICZNA PC-001 — v1.0

**Od:** audytor niezależny · **Dla:** CTO
**Status:** **PROJEKT do przeglądu.** Nie zamrożona, nie w `CRITICAL_FILES_PC_001`.
**Podstawa:** kolejność ustalona przez CTO, pkt 1 (konsolidacja PC-001) · warunek konstrukcyjny
CTO: *„ma być INDEKSEM z odnośnikami do aneksów, nie kopią"* · zasada C-001 (§0.2, do zatwierdzenia)
**Weryfikacja:** wszystkie adresy w tym dokumencie sprawdzone na świeżym klonie gałęzi
`v0.7.2-scientific-integrity`; procedura odtworzenia w §9.

---

## 0. Czym ten dokument jest — i czym celowo nie jest

### 0.1 Rola

PC-001 jest opisany przez zestaw dokumentów zamrożonych w różnym czasie i różnymi decyzjami.
Część z nich **poprawia** wcześniejsze, nie mogąc ich usunąć — bo zamrożone źródła są chronione
hashem i muszą pozostać nienaruszone jako ślad. Skutek: czytelnik, który otworzy prerejestrację
i przeczyta ją w dobrej wierze, przeczyta **stan nieaktualny**, bez żadnego ostrzeżenia w samym
dokumencie.

Ten dokument jest **jednym adresem**, pod którym widać:

1. **co obowiązuje** i pod jakim adresem to żyje (§2),
2. **co zmienił każdy aneks** (§3),
3. **co w zamrożonych źródłach jest już nieobowiązujące** — i co obowiązuje zamiast (§4),
4. **co jest otwarte** (§5).

Punkt 3 jest właściwym powodem istnienia tego dokumentu. Punkty 1, 2 i 4 dałoby się złożyć
z lektury źródeł; punktu 3 **nie da się** — wymaga porównania dokumentów zamrożonych w różnym
czasie, czyli dokładnie tej pracy, która przy braku indeksu jest wykonywana od nowa przez
każdego kolejnego czytelnika, za każdym razem z ryzykiem pominięcia.

### 0.2 Zasada C-001 — Specyfikacja Kanoniczna nie przechowuje wartości

> **Specyfikacja Kanoniczna nie zawiera żadnej wartości, którą da się automatycznie wyliczyć
> lub odczytać z repozytorium.**

**Wolno:** identyfikatory decyzji (`D-XXX`), identyfikatory zasad (`O-001`, `G-001`…),
identyfikatory kontroli (`K1`, `K3a`…), adresy plików, numery sekcji, nazwy symboli w kodzie,
definicje symboliczne (wzory bez podstawionych liczb), statusy będące **decyzjami** (np.
`ARCHITECTURE-LIMITED`), nazwy środowisk i lekcji.

**Nie wolno:** wartości progów, wartości podłóg, liczby plików krytycznych, liczby warunków,
liczby testów, liczby przebiegów, hashy, odsetków, wyników pomiarów, wartości parametrów
konfiguracyjnych.

**Dlaczego mechanicznie, a nie deklaratywnie.** Dokument z liczbami wymaga walidatora staleness
i dyscypliny aktualizacji; dokument bez liczb **nie może się rozjechać ze źródłem, bo nie ma
z czym**. To ten sam wzorzec, który w tym projekcie już zadziałał: runner pilota nie importuje
funkcji liczących podłogę, więc przeliczenie było *niemożliwe*, nie tylko niewykonane.
C-001 jest tą samą konstrukcją zastosowaną do dokumentacji.

**Konsekwencja dla czytelnika:** żeby poznać wartość, trzeba otworzyć adres. To jest koszt
zamierzony. Ergonomię zapewnia artefakt towarzyszący (§0.4), nie ten dokument.

### 0.3 Reguła rozstrzygania sporu

> Przy jakiejkolwiek rozbieżności między tym dokumentem a adresem, na który wskazuje,
> **rozstrzyga adres.** Ten dokument nie jest źródłem żadnego twierdzenia merytorycznego —
> jest wyłącznie mapą.

Rozszerza to D-017 (*źródłem prawdy jest implementacja, nie jej model*) z wielkości wyprowadzanych
na dokumentację: **źródłem prawdy jest zamrożony dokument lub kod, nie indeks je opisujący.**

### 0.4 Artefakt towarzyszący — Canonical Parameters Report

Wartości operacyjne (parametry, podłoga, stan baseline, skład rejestru plików krytycznych,
stan bramek) żyją w raporcie **generowanym z repozytorium**, nie w tym dokumencie.

- **Charakter:** artefakt pochodny, **niekanoniczny**, nieobjęty hashem, nieprzeznaczony do
  ręcznej edycji.
- **Zasada:** raport jest ważny wyłącznie dla commitu, z którego został wygenerowany, i musi
  ten commit podawać.
- **Skutek:** ani ten dokument, ani raport nie stanowią drugiego źródła prawdy. Pierwszy nie ma
  liczb; drugi nie ma trwałości.

---

## 1. Notacja adresów

| Zapis | Znaczenie |
|---|---|
| `plik §N` | sekcja N wskazanego dokumentu |
| `plik → "fragment"` | nagłówek albo wytłuszczony akapit wskazany nazwą (gdy dokument nie numeruje sekcji) |
| `plik::SYMBOL` | nazwana stała, funkcja lub klasa w module |
| `D-XXX` | decyzja CTO (identyfikator; treść w dokumencie, który się na nią powołuje) |

Skróty nazw plików używane dalej — pełne ścieżki względem katalogu głównego repo:

| Skrót | Ścieżka |
|---|---|
| **PC-001** | `publications/preregistration_PC_001.md` |
| **A1 … A5** | `publications/preregistration_PC_001_ANEKS_{1..5}_2026-07-28.md` |
| **W2-SPEC** | `publications/specyfikacja_W2_2026-07-28.md` |
| **FLOOR** | `publications/analiza_floor_model_2026-07-28.md` |
| **B4** | `publications/NOTATKA_B4_ANALIZA_MOCY_2026-07-28.md` |
| **W2-REPORT** | `publications/W2_completion_report_2026-07-28.md` |
| **GOV** | `docs/GOVERNANCE_RULES.md` |
| **CONFIG** | `clos_scientist/pc_001_experiment_config.py` |
| **ENDPOINT** | `clos_scientist/w2_endpoint.py` |
| **FLOOR-MOD** | `clos_world/floor_model.py` |
| **HALT** | `execution_package_v0_11/validators/hard_halt.py` |
| **K7-MOD** | `clos_scientist/fallback_branch_diagnostic.py` |
| **STATS** | `clos_curriculum/laboratory/statistics.py` |

Każdy z powyższych dokumentów ma bliźniaczy plik `.json`. **Markdown jest kanoniczny**
(A2 → „Zamrożenie"); JSON jest odwzorowaniem. Adresy w tym indeksie wskazują markdown.

---

## 2. Rejestr normatywny

### 2.1 Tożsamość eksperymentu

| Element | Adres |
|---|---|
| Co eksperyment testuje i czego **nie** testuje | PC-001 §1 |
| Zakres wykonania (lekcja, genomy, środowiska) | PC-001 §2.3, zmodyfikowany przez A3 §5 — patrz §4 |
| Deklaratywna konfiguracja eksperymentu (D-012) | CONFIG::EXPERIMENT_CONFIG |
| Nazwa konfiguracji rozdzielająca protokół od dynamiki świata | W2-SPEC §1 |
| Dopuszczalne i niedopuszczalne sformułowania wyniku | PC-001 §6 → „Język raportowania"; A1 → „Do decyzji CTO" |

### 2.2 Protokół

| Element | Adres |
|---|---|
| Lekcja, długość przebiegu, mierzalne okno | CONFIG::EXPERIMENT_CONFIG, CONFIG::MEASURABLE_WINDOW_TICKS |
| Okna `W_early` / `W_late` | CONFIG::W_EARLY_TICKS, CONFIG::W_LATE_TICKS |
| Dowód, że lekcja opisuje protokół, nie dynamikę świata | W2-SPEC §1 (weryfikacja w `clos_academy/lesson_L1_2.py`) |
| Rola L1.1 (wspierająca, poza regułą decyzyjną) | PC-001 §4 |
| Środowisko Primary | CONFIG::EXPERIMENT_CONFIG → `environments.primary`; uzasadnienie: A3 §5 |
| Środowiska kontrolne | CONFIG::EXPERIMENT_CONFIG → `environments.K3`, `environments.K4` |

### 2.3 Primary Endpoint (W2)

| Element | Adres |
|---|---|
| Definicja `PE_red(t) = max(0, PE(t) − floor)` | W2-SPEC §2.2 |
| Definicja `redukcja_W2 = (W_early_red − W_late_red) / W_early_red` | W2-SPEC §2.3 |
| Warunek A (kierunek, `β < 0`) i Warunek B (wielkość) | W2-SPEC §2.3; pierwotne brzmienie: PC-001 §2.1 |
| Testy statystyczne i korekta FDR | PC-001 §2.2; implementacja: STATS |
| Uzasadnienie dwuwarunkowości | PC-001 §2.1 → „Uzasadnienie dwuwarunkowości" |
| Pochodzenie progu wielkości (konwencja, nie literatura) | A1 → „Zmiana 4" |
| Obsługa `INSUFFICIENT_DATA` | PC-001 §2.1; implementacja: ENDPOINT::classify_run |
| Implementacja endpointu | ENDPOINT::compute_pe_reducible, ENDPOINT::compute_w2_reduction |

> **Uwaga adresowa:** próg Warunku B **nie ma adresu w kodzie** — jest wyłącznie tekstem
> w prerejestracji. Patrz znalezisko §6.1.

### 2.4 Podłoga nieredukowalna i procedura V-C

| Element | Adres |
|---|---|
| Zakaz wyprowadzenia analitycznego, nakaz wyprowadzenia numerycznego | W2-SPEC §2.1; zasada: GOV → D-017 |
| Procedura wyznaczenia podłogi | FLOOR-MOD::floor_at_tick, FLOOR-MOD::floor_profile |
| Wyprowadzenie liczby realizacji z kryterium precyzji | FLOOR §6; wartość domyślna: FLOOR-MOD::DEFAULT_N |
| Test ważności V-C (`bias_roznicowy` vs tolerancja) | W2-SPEC §2.1a; implementacja: ENDPOINT::select_floor_model |
| Mechaniczność decyzji o modelu podłogi (brak ścieżki operatorskiej) | W2-SPEC §2.1a, §4 (test W2-T7) |
| Zamrożona podłoga środowiska Primary | CONFIG::FROZEN_FLOOR_NOISE_WORLD |
| Kontrola odtwarzalności i zachowanie przy rozjeździe | ENDPOINT::verify_frozen_floor_env, ENDPOINT::FrozenFloorMismatchError; tolerancja: CONFIG::FLOOR_ENV_VERIFICATION_TOLERANCE |
| Rozłączność zakresu seedów użytego do wyznaczenia podłogi | CONFIG::FROZEN_FLOOR_NOISE_WORLD → `seed_range` |

### 2.5 Mały mianownik

| Element | Adres |
|---|---|
| Uzasadnienie progu minimalnego mianownika | W2-SPEC §3.1; wartość: CONFIG::MIN_DENOMINATOR |
| Klasyfikacja przebiegu VALID / FLOOR_LIMITED | W2-SPEC §3.2; implementacja: ENDPOINT::classify_run |
| FLOOR_LIMITED jako **wynik**, nie brak danych | W2-SPEC §3.2 |
| Bezpiecznik przeciw skażeniu doborem próby (komórka → INCONCLUSIVE) | W2-SPEC §3.3; wartość: CONFIG::FLOOR_LIMITED_CELL_THRESHOLD; implementacja: ENDPOINT::classify_cell |
| Warunek A liczony także dla FLOOR_LIMITED | W2-SPEC §3.4 |

### 2.6 Reguła decyzyjna

**Brzmienie obowiązujące:** A1 → „Zaktualizowana reguła decyzyjna", zmodyfikowane statusami
z A4 i A5. Pierwotne, **nieobowiązujące** brzmienie: PC-001 §6 (patrz §4).

| Warunek | Definicja pod adresem | Status | Adres statusu |
|---|---|---|---|
| **A** — kierunek trendu | W2-SPEC §2.3 (na `PE_red`) | aktywny | — |
| **B** — wielkość redukcji | W2-SPEC §2.3 (na `PE_red`) | aktywny | — |
| **FDR** — istotność po korekcie | PC-001 §2.2 | aktywny | — |
| **K1** — surogat z przetasowaniem | PC-001 §5 → „K1"; na `PE_red`: W2-SPEC §5 | aktywny | — |
| **K3a** warunek 1 — wzrost PE po wstrząsie | PC-001 §5 → „K3" | **aktywny** | A5 → „Warunek 1 K3a" |
| **K3a** warunek 2 — ponowna adaptacja | PC-001 §5 → „K3" | **SUSPENDED PENDING WINDOW REDEFINITION** | A5 → „Status" |
| **K3b** — skracanie czasu readaptacji | A1 → „Zmiana 1" | **ARCHITECTURE-LIMITED** — zdefiniowana, niewykonywana, nieusunięta, wraca po CLOS v0.12 | A4 → „Jeden temat" |
| **K4** — brak efektu w czystym szumie **oraz** separacja | A1 → „Zmiana 3"; wzmocnienie przez W2: W2-SPEC §5 | aktywny | — |
| **K5** — ablacja surogatowa | PC-001 §5 → „K5"; na `PE_red`: W2-SPEC §5 | aktywny | — |
| **K6** — sprzężenie predykcji z wejściem | A1 → „Zmiana 2" | aktywny | — |

**Zastrzeżenia wiążące, których nie wolno pominąć przy raportowaniu:**

| Zastrzeżenie | Adres |
|---|---|
| K6 jest warunkiem **koniecznym, nie wystarczającym** | A1 → „Zmiana 2", uwaga interpretacyjna (D-007 pkt 1) |
| K3 i K6 muszą być raportowane w **osobnych sekcjach** | A1 → „Zmiana 2" |
| K4 przy W2 jest częściowo tautologiczna i musi być tak opisana | W2-SPEC §5, uwaga do K4 |
| K1 i K5 to **surogaty analityczne**, nie ingerencje w system | PC-001 §5 → „K5"; PC-001 §8 pkt 3 |

### 2.7 Poza regułą decyzyjną

| Element | Charakter | Adres |
|---|---|---|
| **K2** (`stable_world`) | przesłanka **opisowa**, poza inferencją statystyczną | PC-001 §5 → „K2" (D-005 pkt 4) |
| **K7** (gałąź awaryjna `predict()`) | **pomiar raportowany**, nie warunek | A2 → „Zmiana 7"; implementacja: K7-MOD::k7_fallback_branch_fraction |
| Progi interpretacyjne K7 i ich konwencyjne pochodzenie | — | A2 → „Zmiana 7", „Interpretacja"; implementacja: K7-MOD::interpret_k7_fraction |
| Ograniczenia metody K7 (oszacowanie **dolne**, heurystyka) | — | A2 → „Ograniczenia metody" |
| Obsługa przypadku „K7 nieobliczalny" | — | A2 → „Ograniczenia metody" pkt 1; K7-MOD::default_prediction_depth |
| Zagrożenie T7, które K7 adresuje | — | A2 → „Zmiana 6" |

### 2.8 Klasyfikacja wyniku

| Element | Adres |
|---|---|
| Trójwartościowa klasyfikacja WSPARTA / INCONCLUSIVE / NIE WSPARTA | A1 → „Zasada konserwatywnej interpretacji" (D-007 pkt 2) |
| Zakaz prezentowania INCONCLUSIVE jako wsparcia — także w streszczeniach | A1 → tamże |
| Wynik negatywny musi być raportowany **łącznie z osiągniętą mocą** | PC-001 §7; A1 → „Uwaga o mocy" |
| Zakaz zapisu `MEASURED_BUT_NULL` bez mocy | PC-001 §7 |
| Tabela zagrożeń T1–T7 → kontrola rozstrzygająca | PC-001 §3; zaktualizowana: A1 → „Zaktualizowana tabela Threats"; T7: A2 → „Zmiana 6" |
| Problem otwarty: redukcja PE vs jakość zachowania (niemierzone) | PC-001 §3 → akapit końcowy; PC-001 §8 pkt 4 |

### 2.9 Parametry prerejestrowane

Wszystkie poniższe są **parametrami PC-001, nie globalnymi stałymi CLOS** (D-018 pkt 3) —
przyszły eksperyment może mieć inne, ale wymaga wtedy własnej prerejestracji.

| Parametr | Adres wartości | Adres uzasadnienia |
|---|---|---|
| Tolerancja biasu podłogi | CONFIG::FLOOR_BIAS_TOLERANCE | W2-SPEC §2.1a; FLOOR §3 |
| Minimalny mianownik | CONFIG::MIN_DENOMINATOR | W2-SPEC §3.1 |
| Próg FLOOR_LIMITED w komórce | CONFIG::FLOOR_LIMITED_CELL_THRESHOLD | W2-SPEC §3.3 |
| Okna pomiarowe | CONFIG::W_EARLY_TICKS, CONFIG::W_LATE_TICKS | PC-001 §2.1 |
| Mierzalne okno | CONFIG::MEASURABLE_WINDOW_TICKS | CONFIG, komentarz nad symbolem |
| Zamrożona podłoga środowiska Primary | CONFIG::FROZEN_FLOOR_NOISE_WORLD | W2-REPORT §5 |
| Tolerancja kontroli odtwarzalności podłogi | CONFIG::FLOOR_ENV_VERIFICATION_TOLERANCE | FLOOR §6 |
| Liczba realizacji / początek zakresu seedów podłogi | FLOOR-MOD::DEFAULT_N, FLOOR-MOD::DEFAULT_SEED_START | FLOOR §6 |
| **Próg wielkości redukcji (Warunek B)** | **brak adresu w kodzie** | A1 → „Zmiana 4" · **znalezisko §6.1** |

### 2.10 Governance obowiązujące PC-001

| Zasada | Treść pod adresem |
|---|---|
| **O-001** — Observation First | GOV → „O-001" |
| **G-001** — Typ M vs Typ I (oba warunki jednocześnie) | GOV → „G-001" |
| **G-002** — źródłem decyzji jest wpływ na mierzalność | GOV → „G-002" |
| **G-003** — sześć wymagań dla nowej kontroli, w tym klasyfikacja typu danych | GOV → „G-003" |
| **G-004** — zakaz modyfikacji Core, by kontrola stała się wykonalna | GOV → „G-004" |
| **D-017** — źródłem prawdy jest implementacja, nie jej model | GOV → „D-017" |
| Testy historyczne G-001 i G-003 na rzeczywistych decyzjach | GOV §5, §6 |
| **D-020 (wariant B)** — kolejna niespójność idzie do PC-002, chyba że czyni endpoint niemierzalnym | brak adresu w repo · **znalezisko §6.3** |

### 2.11 Mechanizmy ochronne

| Mechanizm | Adres |
|---|---|
| Rejestr plików krytycznych + uzasadnienie **per pozycja** | HALT::CRITICAL_FILES_PC_001 (komentarze nad listą i przy pozycjach) |
| Kryterium członkostwa w rejestrze | `execution_package_v0_11/hashes/pc_001_baseline_hash.txt`, nagłówek |
| Algorytm hasha i jego przypięcie | HALT::compute_files_hash_v2; `tests/test_hard_halt_hash_algorithm.py` |
| Powód, dla którego baseline nie jest literałem w HALT | `execution_package_v0_11/hashes/pc_001_baseline_hash.txt`, nagłówek |
| Zakaz domyślnej wartości baseline do czasu B5 | HALT::enforce_hard_halt_v2 |
| Kontrola odtwarzalności podłogi | ENDPOINT::verify_frozen_floor_env |
| Test usuwalności Observation Layer | `tests/test_observer_removability.py` |
| Istnienie i czytelność dokumentów prerejestracji | `tests/test_pc_001_hash_registry.py` |
| Rozłączność seedów: pilot / podłoga / konfirmacja | B4 → „Rozdzielność seedów"; CONFIG::FROZEN_FLOOR_NOISE_WORLD; `reports/pilot/*.json` → `seeds_used`, `confirmatory_seeds_start` |
| Gwarancja ślepoty pilota (zapis wyłącznie `W_early_red`) | B4 §2 → „Wzmocnienie"; `reports/pilot/pilot_W_early_red_noise_world.json` → `recorded_quantity`, `NEVER_FOR_INFERENCE` |

### 2.12 Powierzchnia wykonawcza objęta rejestrem plików krytycznych

Sekcje 2.1–2.11 adresują **kryteria i parametry**. Rejestr plików krytycznych chroni ponadto
warstwę, która te kryteria **wykonuje** — jej zmiana zmieniłaby liczby produkowane przez
eksperyment, nie zmieniając ani jednego dokumentu prerejestracji. Ta podsekcja istnieje po to,
by żadna pozycja rejestru nie była chroniona, a nieopisana (test §9 nr 5).

| Warstwa | Adres | Rola |
|---|---|---|
| **Core — ZAMROŻONY od v0.1** | `clos_brain/`, `birth/`, `genome/` | badany system; **nie wolno go modyfikować, by kontrola stała się wykonalna** (GOV → „G-004") |
| Observation Layer | `clos_kernel/snapshot_engine.py` | zapis `prediction`, `input`, `prediction_error`; precedens O-001 (GOV → „O-001") |
| Definicje środowisk | `clos_world/scenarios.py`, `clos_world/world_runtime.py` | generatory `(tick, seed) → wartość`; **źródło podłogi** wyznaczanej numerycznie (GOV → „D-017") |
| Populacja genomów | `clos_curriculum/laboratory/population.py` | zestaw genomów przebiegu; zweryfikowane w A5 jako niezmieniające `prediction_depth` |
| Testy statystyczne | STATS | implementacje testów reguły decyzyjnej; walidowane przeciw bibliotece zewnętrznej, która **celowo pozostaje poza repo** (HALT, komentarz nad rejestrem) |
| Protokoły lekcji | `clos_academy/lesson_L1_2.py` (Primary), `clos_academy/lesson_L1_1.py` (wspierająca) | scenariuszowo-niezależne protokoły; dowód niezależności: W2-SPEC §1 |
| Pipeline wykonawczy | `execution_package_v0_11/runners/pipeline.py`, `execution_package_v0_11/runners/aggregate_results.py` | uruchomienie przebiegów i agregacja wyników |
| Egzekwowanie Hard Halt | HALT | rejestr, algorytm hasha, bramka wejścia |

**Poza rejestrem celowo** (decyzja CTO, uzasadnienie: HALT, komentarz przy pozycji): runnery
jednorazowe, które **wyznaczyły** wartość, ale nie są kodem stosowanym przy każdym przebiegu —
runner wyznaczający podłogę i runner pilota. Ich wyniki są chronione przez zamrożenie **wartości**
w CONFIG, nie przez hash kodu.

---

## 3. Mapa aneksów — co każdy zmienił

| Dokument | Wprowadza | Nie zmienia |
|---|---|---|
| **A1** | K3b (nowa kontrola), K6 (nowa kontrola), K4 przeformułowane na separację, jawne pochodzenie progu wielkości, wskazana ścieżka artefaktu analizy mocy, kategoria INCONCLUSIVE, zagrożenie T6 | Primary Endpoint (nadal na surowym PE w tym momencie) |
| **A2** | zagrożenie T7, K7 jako pomiar raportowany, wymagania techniczne dla K7 | **regułę decyzyjną** — A2 stwierdza to wprost |
| **A3** | diagnozę trafności konstrukcyjnej, odrzucenie W1, wybór wariantu W2, rekomendację przeniesienia Primary do środowiska stacjonarnego | okien pomiarowych, progu wielkości, kontroli K1–K7 co do istnienia |
| **W2-SPEC** | formalną definicję W2, procedurę V-C, obsługę małego mianownika, wymagania weryfikacyjne, wpływ W2 na każdą kontrolę | okien pomiarowych (stwierdza to wprost w §6), progu wielkości, liczby seedów |
| **A4** | status K3b: ARCHITECTURE-LIMITED; zastrzeżenie o nieporównywalności dwóch pomiarów cenzurowania | definicji K3b; statusu Homeostatic Resilience w v0.11 (D-025E: **bez zmian**) |
| **A5** | status warunku 2 K3a: SUSPENDED PENDING WINDOW REDEFINITION; klasyfikację Typ M; dowód mechanizmu | definicji warunku 2 K3a; statusu warunku 1 K3a (pozostaje aktywny); **nie proponuje nowych okien** |

**Kolejność czytania dla kogoś nowego:** PC-001 §1 → A3 §2 (dlaczego endpoint się zmienił) →
W2-SPEC §2 (czym jest endpoint dziś) → A1 „Zaktualizowana reguła decyzyjna" → A4 i A5 (statusy) →
§4 poniżej (co po drodze przestało obowiązywać).

---

## 4. Mapa treści nieobowiązujących w zamrożonych źródłach

**To jest sekcja o najwyższym priorytecie przy przeglądzie.** Każda pozycja to fragment, który
w zamrożonym dokumencie **wygląda na obowiązujący**, a nie jest. Źródeł nie wolno poprawiać
(hash), więc ostrzeżenie musi żyć tutaj.

| # | Adres | Co tam stoi | Dlaczego nie obowiązuje | Co obowiązuje zamiast |
|---|---|---|---|---|
| 1 | PC-001 §2.1 | Primary Endpoint zdefiniowany na **surowym** `PE` | zastąpione wariantem W2 | W2-SPEC §2.2–2.3 |
| 2 | PC-001 §2.3 | środowiska inferencyjne bez środowiska stacjonarnego | Primary przeniesiony do środowiska stacjonarnego | A3 §5; CONFIG::EXPERIMENT_CONFIG |
| 3 | PC-001 §5 → „K3" warunek 2 | kryterium ponownej adaptacji jako aktywne | zawieszone (Typ M, błąd projektu pomiaru) | A5 → „Status" |
| 4 | PC-001 §5 → „K4" | brak wymogu separacji | wzmocnione o separację statystyczną | A1 → „Zmiana 3" |
| 5 | PC-001 §6 | reguła decyzyjna w brzmieniu pierwotnym | rozszerzona, następnie zmodyfikowana statusami | A1 → „Zaktualizowana reguła decyzyjna" + A4 + A5 |
| 6 | PC-001 §3 | tabela zagrożeń bez T6 i T7 | uzupełniona dwukrotnie | A1 → „Zaktualizowana tabela Threats"; A2 → „Zmiana 6" |
| 7 | A3 §1.1 | podłoga fazy powstrząsowej wyprowadzona **analitycznie** | założenie nieobciętego rozkładu fałszywe (D-017) | wyprowadzenie numeryczne: FLOOR-MOD; **uwaga: dla tego środowiska podłoga numeryczna nie została wyznaczona** — §6.2 |
| 8 | A3 §3, tabela podłóg | podłogi wszystkich środowisk wyprowadzone analitycznie | jw. — **w źródle jest korekta**, ale dopiero **pod** tabelą | FLOOR-MOD; W2-REPORT §3 |
| 9 | W2-SPEC §3.1 | uzasadnienie minimalnego mianownika **odniesione do podłogi analitycznej** | odniesienie oparte na wielkości unieważnionej przez D-017; **korekta na końcu dokumentu tego fragmentu nie obejmuje** | wartość parametru pozostaje w mocy (konwencja); **uzasadnienie wymaga przeliczenia** — §6.2 |
| 10 | W2-SPEC §7 pkt 3 | pytanie do CTO z podaną wartością podłogi | wartość analityczna, pytanie rozstrzygnięte przez D-018/D-019 | CONFIG::FROZEN_FLOOR_NOISE_WORLD |
| 11 | B4 §3, tabela projektu pilota | środowiska pilota bez środowiska stacjonarnego; liczba seedów jako **wartość początkowa, nie zamrożona** | pilot powtórzony pod W2 w środowisku Primary | `reports/pilot/pilot_W_early_red_noise_world.json` → `supersedes`; W2-REPORT §7 |
| 12 | B4 §4 pkt 6 | K3b-1 na liście testów do analizy mocy | K3b niewykonywana w PC-001 | A4 |
| 13 | B4 §6 | cała procedura reakcji na „K3b niewykonalny mocowo" (trzy opcje, kolejność wiążąca) | wyczerpana — K3b zawieszona decyzją D-026, nie przeprojektowana | A4 |
| 14 | B4 §7, wiersz B4a | opis pilota w brzmieniu sprzed W2 | pilot powtórzony | W2-REPORT §7 → „Ponowny pilot jest konieczny" |
| 15 | A1 → „Zmiana 1" | K3b jako warunek reguły decyzyjnej | zdefiniowana, ale **niewykonywana** | A4 |
| 16 | A1 → „Zmiana 5" | ścieżka artefaktu analizy mocy | ścieżka nadal obowiązuje; **artefakt nie istnieje** | §5 pkt 3 |

**Wzorzec wspólny dla pozycji 7–10:** wielkości wyprowadzone analitycznie zostały unieważnione
przez D-017, ale **korekty w źródłach są umieszczone lokalnie** — pod tabelą albo na końcu
dokumentu — i nie obejmują wszystkich miejsc, w których ta sama wielkość została użyta jako
przesłanka. To nie jest zarzut wobec korekt (dokumenty były już zamrożone); to jest powód,
dla którego mapa §4 musi istnieć.

---

## 5. Stan otwarty

| # | Pozycja | Status | Adres / uwaga |
|---|---|---|---|
| 1 | **Okna K3a** | otwarte, **świadomie odłożone** (decyzja CTO). Warunek naprawialny bez dotykania Core | A5 → „Status"; zadanie: **K3a Window Design Study**, artefakt projektowy **poza PC-001** |
| 2 | **`PC_001_BASELINE`** | TBD — liczony jako **ostatni** krok, gdy cały pipeline istnieje | `execution_package_v0_11/hashes/pc_001_baseline_hash.txt` |
| 3 | **Artefakt analizy mocy** | ścieżka prerejestrowana, plik **nie istnieje** | A1 → „Zmiana 5" |
| 4 | **Pilot Final** | zaplanowany; parametry **nieudokumentowane w repo** | znalezisko §6.4 |
| 5 | **Monte Carlo (B4b)** | zaprojektowany, niewykonany; walidacja symulatora **obowiązkowa przed użyciem wyników** | B4 §4, §4a |
| 6 | **Bramka wejścia (B6)** | niewykonana | B4 §7 |
| 7 | **Hard Halt eksperymentu** | **POZOSTAJE** (Hard Halt W2 zdjęty decyzją D-019) | W2-REPORT → nagłówek, §7 |

**Kolejność wykonania ustalona przez CTO** (ten dokument jest pozycją 1):

```
1. Specyfikacja Kanoniczna v1.0     ← ten dokument
2. K3a Window Design Study          ← osobny artefakt projektowy, POZA PC-001
3. Pilot Final
4. B4b Monte Carlo
5. B5 baseline → B6 bramka → START
```

**Zasada wiążąca dla pozycji 2** (uzasadnienie CTO): **nie projektować okien „na sucho".**
Cztery razy z rzędu przyczyną problemu było to, że projekt pomiaru nie odpowiadał dynamice
badanego zjawiska — K3b, podłoga analityczna, nasycenie entropii, okna K3a. Zaprojektowanie
nowych okien bez badania powtórzyłoby ten wzorzec.

---

## 6. Znaleziska audytora przy konsolidacji

Cztery pozycje wykryte **wyłącznie** dlatego, że konsolidacja wymusiła zestawienie każdego
parametru z jego adresem. Żadna nie jest zarzutem wobec wcześniejszej pracy; wszystkie są
konsekwencją tego, że dokumenty zamrażano w kolejności, w jakiej powstawały.

### 6.1 Próg Warunku B nie ma adresu w kodzie

**Stan:** pozostałe parametry prerejestrowane (§2.9) żyją jako nazwane stałe w CONFIG i są
importowane przez ENDPOINT. Próg wielkości redukcji — parametr o **największej konsekwencji
dla wyniku** — istnieje wyłącznie jako **tekst prozą** w PC-001 i A1.

**Zweryfikowane:** ENDPOINT liczy `redukcja_W2`, ale **nie porównuje jej z progiem** — to
porównanie w repo nie istnieje. Powstanie dopiero na etapie kodu ewaluacji reguły decyzyjnej.

**Ryzyko:** kod ewaluacji wpisze próg **literałem**, bez mechanicznego związku z prerejestracją.
Hash chroni wtedy tekst i kod **osobno**, a nie ich zgodność. Rozjazd między nimi byłby
niewykrywalny przez istniejące mechanizmy — dokładnie ta klasa błędu, którą wykrył test
negatywny nr 3 w W2-SPEC §4 (implementacja pobierająca podłogę bez odejmowania jej).

**Rekomendacja (decyzja CTO — audytor nie commituje):** wprowadzić próg jako nazwaną stałą
prerejestrowaną w CONFIG, obok pozostałych, wraz z odnośnikiem do A1 → „Zmiana 4" w komentarzu.

**Okno czasowe jest zamknięte i krótkie.** CONFIG jest członkiem rejestru plików krytycznych,
więc zmiana łamie hash — ale `PC_001_BASELINE` **nie jest jeszcze policzony**, więc dziś nie ma
czego złamać. Ta sama struktura argumentu co dopuszczalność aneksów: **dopuszczalne dziś,
niedopuszczalne po B5.**

### 6.2 Uzasadnienie minimalnego mianownika opiera się na wielkości unieważnionej

**Stan:** W2-SPEC §3.1 uzasadnia wartość minimalnego mianownika, odnosząc ją do najmniejszej
niezerowej podłogi w zestawie — wielkości wyprowadzonej **analitycznie**. D-017 unieważnił tę
klasę wyprowadzeń. Korekta na końcu W2-SPEC dotyczy wymagania weryfikacyjnego i środowiska
Primary; **§3.1 nie jest nią objęty**.

**Zweryfikowane:** podłoga numeryczna została wyznaczona **wyłącznie dla środowiska Primary**
(jeden runner, jedna zamrożona wartość). Dla środowiska kontrolnego K3 podłoga numeryczna
w repo nie istnieje.

**Co z tego wynika — i czego nie wynika:** **wartość** parametru pozostaje w mocy. Jest
konwencją przyjętą z góry, a wartością konwencji jest jej niezmienność, nie trafność
uzasadnienia (ta sama logika co przy progu wielkości, A1 → „Zmiana 4"). Zmiana wartości byłaby
niedopuszczalna. Nieaktualne jest **uzasadnienie**, nie parametr.

**Rekomendacja:** odnotować w §4 (pozycja 9 — zrobione) i **nie zmieniać wartości**. Jeśli CTO
uzna, że uzasadnienie ma zostać przeliczone, jest to zadanie na PC-002 albo na osobną notatkę —
nie zmiana parametru bieżącego protokołu.

### 6.3 D-020 nie ma adresu w repo

**Stan:** D-020 (wariant B) — *„po zamknięciu fazy projektowania kolejna niespójność idzie do
PC-002, chyba że czyni endpoint niemierzalnym"* — jest regułą **proceduralną o tej samej wadze
co G-001**, a jedyny jej ślad to wzmianka w commicie zamykającym fazę projektowania. GOV zawiera
O-001 i G-001…G-004, nie zawiera D-020.

**Ryzyko:** GOV jest w rejestrze plików krytycznych właśnie dlatego, że kryteriów klasyfikacji
nie wolno zmienić po fakcie. D-020 rozstrzyga, **czy poprawkę w ogóle rozpatrywać w bieżącym
protokole** — czyli działa *przed* G-001. Reguła wcześniejsza w kolejności stosowania jest słabiej
chroniona niż reguła, którą warunkuje.

**Rekomendacja:** dopisać D-020 do GOV, wzorem pozostałych zasad (treść + test historyczny).
To samo okno czasowe co §6.1 — GOV jest w rejestrze, baseline nie jest policzony.

### 6.4 Parametry Pilota Final nie mają artefaktu

**Stan:** kolejność wykonania przewiduje Pilot Final z parametrami różnymi od poprzedniego
pilota (inna liczba seedów, drugie środowisko), uzasadnionymi obserwacją niestabilności
oszacowania wariancji. Analogicznie B4b ma używać wariancji dwupoziomowej z podanym stosunkiem
składowych.

**Zweryfikowane:** **żaden z tych parametrów ani żadna z tych obserwacji nie występuje
w repozytorium** — ani w dokumentach, ani w artefaktach `reports/pilot/`, ani w kodzie. Istnieją
wyłącznie w dokumencie przekazania kontekstu.

**Dlaczego to jest problem, a nie drobiazg:** B4 §3 dopuszcza zwiększenie liczby seedów, ale
warunkuje je obejrzeniem rozkładu — i wolno to zrobić **tylko dlatego**, że mierzona wielkość
nie niesie informacji o efekcie. Ta dopuszczalność opiera się na **konkretnej przesłance**
(jaki rozkład zaobserwowano, jak niestabilne było oszacowanie). Bez artefaktu przesłanka jest
niesprawdzalna, a decyzja o liczbie seedów staje się nieodróżnialna od dobrania jej po fakcie.

**Rekomendacja:** przed Pilotem Final zapisać notatkę z uzasadnieniem parametrów, wzorem B4 —
z jawnym wskazaniem, z którego artefaktu pochodzi obserwacja niestabilności. Jeśli obserwacja
pochodzi z ponownej analizy istniejącego artefaktu pilota, wystarczy wskazać tę analizę.
**Ten dokument celowo nie przytacza tych liczb** (C-001, a niezależnie od C-001 — nie mają źródła).

---

## 7. Czego ten dokument nie rozstrzyga

- **Nie zmienia żadnego kryterium.** Zmiana kryterium wymaga datowanego aneksu, przed obejrzeniem
  danych, których dotyczy (PC-001 §12).
- **Nie proponuje okien K3a** — to osobne zadanie projektowe, poza PC-001 (§5 pkt 1).
- **Nie klasyfikuje znalezisk z §6 jako Typ M ani Typ I** — klasyfikacja jest decyzją CTO
  na podstawie analizy audytora (GOV → G-001, „Role").
- **Nie przechowuje żadnej wartości** (C-001).
- **Nie zastępuje żadnego dokumentu.** Wszystkie źródła pozostają w mocy pod swoimi adresami.

---

## 8. Warunki utrzymania

Ten dokument wymaga aktualizacji **wyłącznie** wtedy, gdy zmienia się jedno z:

1. **struktura reguły decyzyjnej** (warunek dodany, usunięty lub zmieniający status),
2. **adres** obowiązującej definicji (nowy aneks, przeniesienie parametru do kodu),
3. **stan pozycji otwartej** z §5,
4. **zawartość mapy §4** (nowe źródło częściowo unieważnione).

Nie wymaga aktualizacji, gdy zmienia się **wartość** czegokolwiek — to jest cała korzyść z C-001.

**Wersjonowanie:** zmiana w §2 lub §4 → nowa wersja mniejsza (v1.1). Zmiana zasady C-001 albo
roli dokumentu → wersja większa (v2.0).

**Format:** markdown jest kanoniczny, JSON jest jego **mechanicznym odwzorowaniem**
(`spec_md_to_json.py`). JSON nie jest pisany ręcznie i nie może być: walidator **regeneruje
odwzorowanie z bieżącego markdowna w pamięci i porównuje je strukturalnie** z plikiem JSON
w repo. Wykrywa to zarówno ręczną edycję JSON-a, jak i JSON pochodzący ze starszej wersji
markdowna. Ręczna edycja jest wykrywalna, nie tylko zabroniona.

> **Dlaczego regeneracja, a nie skrót markdowna zapisany w JSON.** Skrót wymagałby wpisania
> do JSON-a wartości wyliczalnej z repozytorium, czyli **odstępstwa od C-001** — a odstępstwo
> od zasady, choćby uzasadnione, jest początkiem jej erozji. Regeneracja daje ten sam efekt
> bez wyjątku i wykrywa **więcej**: skrót łapie zmianę markdowna bez regeneracji, regeneracja
> łapie to samo **oraz** ręczną edycję JSON-a przy nietkniętym markdownie.
>
> **Znane ograniczenie tego rozwiązania:** walidator zależy od konwertera, więc błąd
> w konwerterze jest wspólny obu stronom porównania — zgodność zachodzi, choć oba pliki są
> błędne. Skrót tej zależności nie miał. Ryzyko domyka wyłącznie **własny zestaw testów
> konwertera**, w tym test idempotencji; bez niego porównanie jest samopotwierdzające.

### 8.1 Członkostwo w rejestrze plików krytycznych — rekomendacja: NIE

**Rekomendacja audytora: nie włączać do `CRITICAL_FILES_PC_001`.** Trzy powody, w kolejności wagi.

**Po pierwsze — kryterium członkostwa jest zapisane i przemawia przeciw.** Brzmi ono: *„czy zmiana treści
tego pliku mogłaby zmienić liczby, które wyprodukuje eksperyment PC-001"*. Ten dokument nie
zawiera żadnej wartości (C-001) i nie jest importowany przez żaden kod — nie może zmienić
żadnej liczby. Włączanie do rejestru pozycji niespełniających kryterium **niszczy informacyjną
wartość samego rejestru**: dziś członkostwo znaczy jedną, sprawdzalną rzecz, a po dodaniu
wyjątku znaczyłoby „ważne zdaniem kogoś".

**Po drugie — hash chroni przed zmianą, a ten dokument wymaga ochrony przed *niepoprawnością*.**
Zamrożenie hashem jest właściwe dla kryteriów: mają nie zmieniać się wcale. Indeks jest inny —
**ma się zmieniać** za każdym razem, gdy dochodzi aneks (warunki utrzymania powyżej). Zamrożony indeks
rozjechałby się ze źródłami w pierwszym dniu, w którym stałby się nieaktualny, a hash nadal
byłby zielony. Hash wykryłby edycję, ale nie wykryłby **braku** edycji — a to jest dokładnie
ten tryb awarii, na który indeks jest podatny.

**Po trzecie — właściwa ochrona już istnieje i jest mocniejsza.** `validate_canonical_spec.py` w CI
wykrywa rozjazd indeksu ze źródłami: martwy odnośnik, usunięty symbol, pozycję rejestru
nieopisaną w §2, naruszenie C-001, ręcznie edytowany JSON. Hash tego nie potrafi. Dla mapy
**ciągła weryfikacja poprawności bije jednorazowe zamrożenie**.

**Rekomendacja operacyjna:** wpiąć walidator do CI obok istniejących testów, jako warunek
zielonej gałęzi. Wymaga to commitu `validate_canonical_spec.py` i `spec_md_to_json.py`
do repo — one same nie muszą być w rejestrze z tego samego powodu co ten dokument.

**Zastrzeżenie, którego audytor nie ukrywa:** przy tej decyzji mapa §4 **nie jest** chroniona
przed cichym przeredagowaniem. Ktoś mógłby usunąć wiersz mówiący, że dany fragment nie
obowiązuje, i żaden test tego nie złapie — bo testy sprawdzają, czy adresy się rozwiązują,
nie czy mapa jest kompletna. **Kompletności §4 nie da się dziś sprawdzić mechanicznie.**
Jeśli CTO uzna to ryzyko za przeważające, właściwą odpowiedzią jest włączenie do rejestru
**mimo** niespełnienia kryterium — ale wtedy z jawnym zapisem, że jest to wyjątek i dlaczego,
żeby kryterium nie erodowało po cichu.

---

## 9. Weryfikowalność

Ten dokument jest sprawdzalny **mechanicznie**, nie przez lekturę:

Walidator: `validate_canonical_spec.py` — uruchamiany przeciw świeżemu klonowi. Przekazany razem
z tym dokumentem, **jeszcze nie w repo** (audytor nie commituje); walidator odnotowuje ten stan
jawnie i przestanie go zgłaszać dopiero po commicie przez wykonawcę.

| # | Test | Co wykrywa |
|---|---|---|
| 1 | każdy adres pliku istnieje w repo | odnośnik do nieistniejącego pliku |
| 2 | każdy adres `plik §N` / `plik → "fragment"` rozwiązuje się do istniejącej sekcji | odnośnik do nieistniejącej sekcji |
| 3 | każdy adres `plik::SYMBOL` rozwiązuje się do istniejącego symbolu | odnośnik do usuniętej lub przemianowanej stałej |
| 4 | **test negatywny C-001:** dokument nie zawiera liczby w kontekście wartości parametru | naruszenie zasady zero-wartości |
| 4b | **test negatywny testu nr 4:** wstrzyknięte sondy (próg, podłoga, liczność, odsetek) **muszą** zostać złapane | filtr C-001 rozluźniony wyjątkami do stanu dekoracji |
| 5 | każda pozycja rejestru plików krytycznych jest osiągalna z §2 | luka w indeksie — plik chroniony, ale nieopisany |
| 6 | **test negatywny testu nr 5:** usunięcie adresu z §2 **musi** zepsuć test nr 5 | czy test nr 5 w ogóle działa |
| 7 | JSON niezgodny z odwzorowaniem regenerowanym z bieżącego markdowna | JSON edytowany ręcznie albo pochodzący ze starszej wersji dokumentu |

Testy 4b i 6 istnieją, bo w tym projekcie pięciokrotnie okazało się, że **walidator bez testu
negatywnego jest dekoracją**: indeks deklarujący, że nie zawiera wartości, wygląda dokładnie tak
samo jak indeks, który je zawiera — dopóki się tego nie sprawdzi.

Test 4b nie jest ozdobnikiem. Filtr rozpoznający „liczbę w kontekście wartości" musi odróżnić ją
od numeracji sekcji, identyfikatorów kontroli, dat w ścieżkach i odsyłaczy z polską odmianą.
Każdy dodany wyjątek zbliża filtr do przepuszczania wszystkiego — **test 4b jest jedyną rzeczą,
która to zatrzymuje**, i musi zostać uruchomiony po każdej zmianie filtra.

**Stan na moment przekazania:** wszystkie testy PASS na świeżym klonie. Wynik testów 5 i 2 był
początkowo negatywny i wymusił dwie realne poprawki dokumentu (uzupełnienie §2.12 o powierzchnię
wykonawczą, doprecyzowanie notacji `→ "fragment"` w §1) — walidator zadziałał, zanim dokument
trafił do przeglądu.

---

*Dokument nie zawiera żadnej wartości liczbowej pochodzącej z repozytorium (C-001, §0.2).
Wszystkie adresy zweryfikowane na świeżym klonie; procedura weryfikacji w §9.
Audytor nie commituje — pliki przekazane do decyzji CTO i wykonania przez wykonawcę.*
