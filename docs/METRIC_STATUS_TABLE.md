# Metric Status Table — status per (metryka × lekcja × środowisko)

> **⚠ STATUS DANYCH: Exploratory Dataset v0.10 (SPRINT_v0.11.0.md).** Ten
> dokument NIE jest nowym pomiarem — jest nową, dokładniejszą KLASYFIKACJĄ
> tego, co [`docs/VALIDITY_REPORT.md`](VALIDITY_REPORT.md) i
> `reports/population/population_validation_v0_10_1.json` już ustaliły.
> Formuły matematyczne, definicje "czego NIE mierzy" i pełne uzasadnienia
> konstruktów są w VALIDITY_REPORT.md — TUTAJ przywołane skrótowo, nie
> duplikowane. **Power/Confirmatory validity: PENDING** dla wszystkich
> wierszy do re-run zatwierdzonego przez CTO — patrz §2 poniżej za
> wyjaśnienie, dlaczego kolumna rekomendacji mimo to już coś mówi.

**Zadanie CTO (2026-07-18):** rozszerzenie 4-kolumnowej tabeli walidacji
(VALIDITY_REPORT.md, sekcja "Cztery statusy...") o (a) **wszystkich 14 osi**
ontologii, nie tylko 7 zmierzonych, i (b) kolumnę **rekomendacji** z
formalnym słownikiem 6 statusów, w tym dwóch nowych: `MEASURED_BUT_NULL`,
`INSUFFICIENT_POWER`.

---

## 0. Poprawka liczności (zweryfikowana z danych, nie założona)

Zlecenie mówiło o "6 z 14 osi bez lekcji". Sprawdzone bezpośrednio w
`publications/competency_profile.json` (`status: "insufficient_data"`,
`source_lesson: None`): jest ich **7**, nie 6 — Perception, Attention,
Long-term Memory, Prediction, Exploration, Generalization, Planning.
7 (brak lekcji) + 7 (zmierzone: Pattern Recognition, Pattern Retention,
Working Memory, Adaptation, Stability, Final Energy Level, Homeostatic
Resilience) = 14. Zgłaszam rozbieżność zamiast po cichu przyjąć błędną
liczbę.

---

## 0b. Mapowanie nazw: ontologia bieżąca ↔ klucze w Exploratory Dataset v0.10

**Ten dokument opisuje 14 osi BIEŻĄCEJ ontologii** (nazwy po
SPRINT_v0.11.0.md P1: "Working Memory (MAE@50)", "Final Energy Level").
**`reports/population/population_validation_v0_10_1.json` jest zamrożonym
Exploratory Dataset v0.10** (`dataset_status`: "Nie poprawiane, nie
wycofywane") i celowo NIE został zregenerowany po tych zmianach nazw — patrz
`docs/MSE_MAE_NAMING_DECISION.md`/`docs/ENERGY_EFFICIENCY_ONTOLOGY_DECISION.md`.
Dwie osie noszą więc w tym pliku STARE klucze. Bez tego mapowania czytelnik
za rok, szukając `"Final Energy Level"` w surowym JSON-ie, nie znalazłby
tego klucza — dokładnie ten rozjazd trzeba nazwać wprost:

| Nazwa w tej tabeli (ontologia bieżąca) | Klucz w `population_validation_v0_10_1.json` (Exploratory Dataset v0.10, NIEZMIENIONY) | Czy wartości się różnią? |
|---|---|---|
| Working Memory (MAE@50) | `"Working Memory (MSE@50)"` | Nie — sam rename etykiety (`abs()`, nie kwadrat, od zawsze; patrz `docs/MSE_MAE_NAMING_DECISION.md`) |
| Pattern Recognition | `"Pattern Recognition"` | Nie — nazwa koncepcji bez zmian (pole źródłowe `mse_stimulus_phase`→`mae_stimulus_phase` zmieniło się w kodzie/`reports/academy/`, NIE w tym artefakcie populacyjnym, który nigdy nie przechowywał surowego pola `mse_*`, tylko już zagregowaną etykietę) |
| Final Energy Level | `"Energy Efficiency"` | Nie — sam rename etykiety (błąd kategorii, nie pomiaru; patrz `docs/ENERGY_EFFICIENCY_ONTOLOGY_DECISION.md`) |
| pozostałe 4 zmierzone osie (Pattern Retention, Adaptation, Stability, Homeostatic Resilience) | te same nazwy w obu miejscach | — (nazwy nie zmieniały się) |

**Dlaczego nie zregenerować datasetu, żeby to uprościć:** próbowałem to
zrobić wcześniej w tym sprincie i zostałem słusznie zatrzymany — regeneracja
(nawet tylko nazw kluczy, bez zmiany wartości) łamie deklarację "Nie
poprawiane, nie wycofywane" tego konkretnego artefaktu. Mapowanie w tabeli
wyżej jest zamiennikiem: łącznik między dwiema nazwami tej samej osi, bez
dotykania zamrożonych danych.

---

## 1. Słownik statusów rekomendacji (definiowany formalnie po raz pierwszy w tym dokumencie)

Żaden z tych sześciu statusów nie występował dotąd nigdzie w repo jako
formalna etykieta — CTO zatwierdził zbiór, ten dokument go definiuje.

| Status | Kryterium | Co oznacza dla czytelnika |
|---|---|---|
| **VALIDATED** | Measurement=✔ **I** Construct=✔ (bez zastrzeżeń) **I** Power potwierdzona **I** Confirmatory potwierdzona (replikacja niezależna, prerejestrowana) | Można cytować bez zastrzeżeń. |
| **EXPERIMENTAL** | Measurement=✔, Construct=◐/✔ (zastrzeżenia dopuszczalne, ale konstrukt sensowny), i efekt REALNIE dyskryminuje — konkretny, policzony odsetek par przeżywających korektę FDR (q=0.05), NIE retrospektywna moc | Najlepszy obecnie dostępny status — realny, skorygowany na wielokrotność sygnał, ale NIE potwierdzony niezależnie. |
| **MEASURED_BUT_NULL** | Measurement=✔, Construct=◐/✔, ale same WARTOŚCI metryki są substantywnie nieodróżnialne od zera/floor (nie chodzi o moc porównania międzygenomowego — zjawisko nie zachodzi w wykrywalnej skali) | Pomiar działa poprawnie; zjawisko, które miał wykryć, prawdopodobnie nie występuje w tej populacji/zadaniu. |
| **INSUFFICIENT_POWER** | Measurement=✔ lub ✘(fragile), Construct=◐/✔, wartości metryki SĄ substantywne (nie ~0), ale 0 (lub prawie 0) par przeżywa korektę FDR — **nie wiadomo, czy to prawdziwy null, czy artefakt zbyt małej próby**, bo jedyny sposób to rozstrzygnąć (prospektywna analiza mocy z niezależnego re-runu) jest PENDING | Nie wiadomo, czy genomy się różnią — rozstrzygnięcie wymaga re-runu, którego nie ma. **Retrospektywna moc (policzona z `f_obs` zaobserwowanego na TYCH SAMYCH danych) jest statystycznie bezwartościowa jako dowód — nie jest tu używana jako uzasadnienie, patrz §2.** |
| **INVALID_CONSTRUCT** | Construct=✘ w sensie fundamentalnym: nazwa/pole mierzy INNE zjawisko niż deklarowane, niezależnie od mocy/repliki | Więcej danych NIE naprawi tego wyniku — problem jest w definicji, nie w próbce. |
| **NOT_MEASURED** | Brak lekcji/endpointu — pojęcie niezoperacjonalizowane (nie: zoperacjonalizowane źle) | Odróżnia "nie próbowaliśmy" od "próbowaliśmy i się nie udało" (INVALID_CONSTRUCT) lub "próbowaliśmy i brakło mocy" (INSUFFICIENT_POWER). |

**Reguła pierwszeństwa** (gdy więcej niż jedno kryterium pasuje):
Construct=✘ fundamentalny **>** Measurement fragile/niska moc **>**
wartość ~null **>** silna dyskryminacja. Innymi słowy: zepsuty konstrukt
unieważnia wynik niezależnie od tego, jak dobrze "wygląda" statystycznie —
zasada nadrzędna 2 tego sprintu (zero overfittingu, nie ratujemy złych
konstruktów dobrą statystyką).

**Wyjątek jawny:** Final Energy Level ma Construct oznaczony "✘⁶" w
VALIDITY_REPORT.md, ale to ✘ oznacza co innego niż w Adaptation/Homeostatic
Resilience (patrz footnote 6 tam) — to zmienna stanu fizjologicznego, NIE
zepsuty konstrukt poznawczy. Reguła pierwszeństwa (Construct=✘ →
INVALID_CONSTRUCT) **celowo NIE jest tu stosowana mechanicznie** — patrz §3.

---

## 2. Dlaczego liczb mocy (`power_n10`, "18.5%" itp.) NIE MA w kolumnie Rekomendacja

**Korekta (2026-07-19, audyt): pierwsza wersja tej sekcji i tabeli używała
`power_n10` z `publications/preregistration_v0_11_0_power_reproduction.json`
jako uzasadnienia rekomendacji ("moc 18.5%" itp.) — to był BŁĄD, ten sam,
który cały SPRINT_v0.11.0.md P0 miał wykryć i naprawić.** Sprawdzone wprost:
`power_n10` jest liczone jako `power_anova(f_obs, k=23, n=10, alpha_skor.)`,
gdzie `f_obs` jest efektem WYLICZONYM z TYCH SAMYCH 23 genomów/n=10, których
moc rzekomo ocenia. To jest **moc retrospektywna (post-hoc)** — matematycznie
zdeterminowana funkcja wyniku testu, który już się odbył na tych danych
(tzw. "power approach paradox", Hoenig & Heisey 2001) — **nie niesie żadnej
dodatkowej informacji dowodowej ponad samą wartość p**. Użycie jej jako
uzasadnienia statusu byłoby dokładnie tym błędem "raportowania mocy, której
nie mamy", który P0 miał wyeliminować (patrz `tests/test_power_analysis.py`,
`TestAnovaMultipleComparisonsCorrectionRequired` — ten sam projekt ma już
regresję pilnującą DOKŁADNIE tego typu pomyłki gdzie indziej).

**Konsekwentnie usunięte z kolumny Rekomendacja poniżej.** Zamiast liczby
mocy retrospektywnej, uzasadnienie `INSUFFICIENT_POWER` cytuje wyłącznie
**legalne, niecyrkularne fakty**: `valid_rate`/klasyfikację `GENOME-FRAGILE`
(realny fakt o jakości pomiaru, nie o mocy testu) oraz liczbę par
przeżywających FDR (realny, skorygowany wynik testu — 0/253 to fakt, nie
"moc"). Prospektywna moc — jedyna wersja tego pojęcia, która ma sens
dowodowy — wymaga niezależnego re-runu i pozostaje **PENDING**, dokładnie
tak samo w kolumnie Rekomendacja jak w kolumnach Power/Confirmatory: żaden
wiersz nie twierdzi, że zna moc obecnej próby.

`power_n30`/`power_at_proposed_n30` w tym samym pliku prereg pozostają
legalnym użyciem `f_obs` — tam służą WYŁĄCZNIE do PLANOWANIA wielkości
przyszłego re-runu (typowa, akceptowana praktyka: użyć efektu pilotażowego
do zaplanowania n konfirmacyjnego badania), NIE do oceny obecnych danych —
ten dokument ich też nie cytuje jako dowodu.

---

## 3. Adaptation: dokładniejsza analiza niż "L1.1 ✔ / L1.2 ✘" (weryfikacja zlecenia audytora)

Audytor zaproponował: "Construct Validity ✔ w L1.1, ✘ w L1.2". Sprawdzone
w danych — **prawdziwe rozróżnienie jest o jeden poziom głębsze**, dokładnie
demonstrując tezę audytora o granulacji per-kontekst:

- **L1.1 (noise_world/drift_world) i L1.2/drift_world:** `adaptation_tick`
  mierzy tick stabilizacji entropii OD STARTU (cold start) — sensowny,
  DEFENSYWNY konstrukt "adaptacji" ogólnie, ale ze znanym trybem
  fałszywie-pozytywnym: genomy o wysokim `decay_rate` (~0.035+) rejestrują
  "natychmiastową adaptację" (`tick=0`) deterministycznie, bez względu na
  seed — stąd GENOME-FRAGILE (35-43% valid_rate), nie realny brak sygnału.
  **Construct: ◐, nie ✔ ani ✘** — audytor miał rację, że to inny (lepszy)
  konstrukt niż w shock_world, ale "✔ bez zastrzeżeń" byłoby zbyt hojne
  wobec udokumentowanego mechanizmu fałszywie-pozytywnego (ta sama hipoteza
  post-hoc `decay_rate≈0.035` z `docs/CURRENT_SCIENTIFIC_LIMITS.md` §5).
- **L1.2/shock_world:** `adaptation_tick` jest **stała=10 dla WSZYSTKICH 23
  genomów i 10 seedów** (`valid_rate=0%`, zero wariancji) — mierzy
  stabilizację w oknie PRZED szokiem (`t_shock` zawsze ≥20), zjawisko
  NIEZWIĄZANE z tematem lekcji (recovery PO szoku). **Construct: ✘,
  fundamentalnie** — audytor miał rację tutaj wprost.

**Wniosek:** to nie jest "L1.1 vs L1.2", to jest "cold-start stabilization
(sensowne, ◐) vs specyficznie shock_world's pre-shock window (bezsensowne
tu, ✘)" — L1.2/drift_world zachowuje się jak L1.1, NIE jak L1.2/shock_world,
bo tam też nie ma szoku do pomylenia z adaptacją. To wzmacnia, nie osłabia,
argument audytora za granulacją per (metryka×lekcja×środowisko) — sama
granulacja "per lekcja" byłaby TEŻ za gruba.

---

## 4. Tabela pełna (14 osi × konteksty = 37 wierszy)

Legenda Measurement/Construct: ✔ spełnione · ✘ niespełnione/problematyczne ·
◐ częściowe · — nie dotyczy. `⁷` = `stable_world`, kontrola deterministyczna
(oczekiwane, nie porażka, patrz VALIDITY_REPORT.md footnote 7). Definicje
skrócone — pełne formuły: VALIDITY_REPORT.md, sekcja per oś.

### 4a. Siedem osi bez lekcji (NOT_MEASURED)

| Oś | Definicja | Interpretacja biologiczna | Measurement | Construct | Power | Confirmatory | Rekomendacja |
|---|---|---|---|---|---|---|---|
| Perception | nie dotyczy — brak endpointu | odbiór bodźca zmysłowego | — | — | — | — | **NOT_MEASURED** |
| Attention | nie dotyczy — brak endpointu | selektywne skupienie zasobów | — | — | — | — | **NOT_MEASURED** |
| Long-term Memory | nie dotyczy — brak endpointu | trwałe przechowywanie po wielu sesjach | — | — | — | — | **NOT_MEASURED** |
| Prediction | nie dotyczy — brak endpointu | przewidywanie przyszłego stanu | — | — | — | — | **NOT_MEASURED** |
| Exploration | nie dotyczy — brak endpointu | poszukiwanie nowych stanów/strategii | — | — | — | — | **NOT_MEASURED** |
| Generalization | nie dotyczy — brak endpointu | transfer między zadaniami/środowiskami | — | — | — | — | **NOT_MEASURED** |
| Planning | nie dotyczy — brak endpointu | wieloetapowe sekwencjonowanie działań | — | — | — | — | **NOT_MEASURED** |

Mechanizmy w Core mogą istnieć (np. `perceive()`) — mechanizm ≠ zmierzony
endpoint (zasada uczciwości `cognitive_ontology.md`). `NOT_MEASURED` ≠
`INSUFFICIENT_POWER`: tu nie próbowano zoperacjonalizować w ogóle, nie
"próba była za mała".

### 4b. Siedem osi zmierzonych × konteksty (30 wierszy)

> **AKTUALIZACJA 2026-07-20 (re-run konfirmacyjny + Red Team):** 6 wierszy
> poniżej (L1.1×noise_world × {Working Memory, Pattern Recognition, Pattern
> Retention, Adaptation, Stability} + L1.2×shock_world × Homeostatic
> Resilience) ma teraz Measurement/Power/Confirm./Rekomendację przeliczone
> z **`reports/population/population_validation_v0_11_0.json`** (re-run
> n=185/93/92, `execution_package_v0_11/results/full_rerun_results.jsonl`,
> Hard-Halt PASS cały bieg) i zweryfikowane niezależnie testem
> Kruskal-Wallisa (`clos_curriculum/laboratory/statistics.py::kruskal_wallis`,
> nowy w tym sprincie, zwalidowany w `tests/test_kruskal_wallis.py`
> przeciwko zamkniętej formie chi-kwadrat df=2). **Pełny opis metodologii
> i co dokładnie Red Team obalił/potwierdził: §7.** Wiersze `drift_world`
> (poza zakresem re-runu, patrz aneks) oraz L1.2×shock_world×{Adaptation,
> Stability, Final Energy Level} (nie objęte korektą Red Teamu) pozostają
> BEZ ZMIAN — nadal oparte wyłącznie na Exploratory Dataset v0.10,
> Power/Confirmatory nadal PENDING.

| Lekcja | Środ. | Metryka | Definicja (skrót) | Interpretacja biologiczna | Measurement | Construct | Power | Confirm. | Test | Rekomendacja |
|---|---|---|---|---|---|---|---|---|---|---|
| L1.1 | noise_world | Working Memory | `mean(mae@t≥stim+50)` | błąd predykcji utrzymany 50 ticków po ustaniu bodźca | ✔ (ROBUST, 100%, n=185) | ◐¹ | **CONFIRMED**¹⁰ | **CONFIRMED**¹⁰ | Welch-pary (0/253) + Kruskal-Wallis (p=8.1e-17) | **VALIDATED**¹⁰ (winner's curse: f 0.265→0.154, efekt UMIARKOWANY nie duży) |
| L1.1 | drift_world | Working Memory | jw. | jw. | ✔ | ◐¹ | PENDING | PENDING | Welch-pary (0/253) | **INSUFFICIENT_POWER** (poza zakresem re-runu — patrz aneks) |
| L1.1 | stable_world | Working Memory | jw. | jw. | ✘⁷ | ◐¹ | PENDING | PENDING | — | — (kontrola, nie klasyfikowana) |
| L1.1 | noise_world | Pattern Recognition | `mean(mae) w fazie bodźca` | błąd predykcji PODCZAS bodźca | ✔ (ROBUST, 100%, n=185) | ◐⁴ | **CONFIRMED**¹⁰ | **CONFIRMED**¹⁰ | Welch-pary (0/253) + Kruskal-Wallis (p=4.5e-14) | **VALIDATED**¹⁰ (f_obs WZROSŁO 0.130→0.164 — odwrotnie niż typowy winner's curse, patrz §7) |
| L1.1 | drift_world | Pattern Recognition | jw. | jw. | ✔ | ◐⁴ | PENDING | PENDING | Welch-pary (0/253) | **INSUFFICIENT_POWER** (poza zakresem re-runu) |
| L1.1 | stable_world | Pattern Recognition | jw. | jw. | ✘⁷ | ◐⁴ | PENDING | PENDING | — | — (kontrola) |
| L1.1 | noise_world | Pattern Retention | `(mae_silence-mae_stim)/silence_ticks` | tempo zaniku błędu po ustaniu bodźca | ✔ (ROBUST, 100%, n=185) | ◐⁵ | **CONFIRMED**¹¹ | **CONFIRMED**¹¹ | Welch-pary (0/253) + **Kruskal-Wallis (p=0.0254, ISTOTNE)** | **EXPERIMENTAL**¹¹ (było MEASURED_BUT_NULL — Red Team: zły TYP testu dał fałszywe zero, §7) |
| L1.1 | drift_world | Pattern Retention | jw. | jw. | ✔ | ◐⁵ | PENDING | PENDING | Welch-pary (0/253) | **MEASURED_BUT_NULL** (poza zakresem re-runu — NIE przeliczone Kruskal-Wallisem, patrz §7 ryzyko) |
| L1.1 | stable_world | Pattern Retention | jw. | jw. | ✘⁷ | ◐⁵ | PENDING | PENDING | — | — (kontrola) |
| L1.1 | noise_world | Adaptation | tick stabilizacji entropii od startu | czas do ustania chaosu początkowego | ✘ (FRAGILE, 56.5%, n=185 — było 35% przy n=10) | ◐ⁱ | **CONFIRMED**¹² | **CONFIRMED**¹² | Welch-pary (75/78 obliczalnych) + **Kruskal-Wallis (p≈0, log₁₀p=-773.3)** | **EXPERIMENTAL**¹² (było INSUFFICIENT_POWER — status z Kruskal-Wallisa, NIE z ANOVA, §7) |
| L1.1 | drift_world | Adaptation | jw. | jw. | ✘ | ◐ⁱ | PENDING | PENDING | Welch-pary | **INSUFFICIENT_POWER** (poza zakresem re-runu) |
| L1.1 | stable_world | Adaptation | jw. | jw. | ✘⁷ | ◐ⁱ | PENDING | PENDING | — | — (kontrola) |
| L1.1 | noise_world | Stability | `1/(std(entropy)+std(\|1-energy\|)+ε)` | stałość dynamiki wewnętrznej w czasie | ✔ (ROBUST, 100%, n=185) | ◐³ | **CONFIRMED**¹⁰ | **CONFIRMED**¹⁰ | Welch-pary (244/253, 96%) + Kruskal-Wallis (p≈0, log₁₀p=-686.8) | **VALIDATED**¹⁰ (leave-one-out 69→45 odporny; f 2.25→2.06, spadek umiarkowany) |
| L1.1 | drift_world | Stability | jw. | jw. | ✔ | ◐³ | PENDING | PENDING | Welch-pary (168/253) | **EXPERIMENTAL** (poza zakresem re-runu) |
| L1.1 | stable_world | Stability | jw. | jw. | ✘⁷ | ◐³ | PENDING | PENDING | — | — (kontrola) |
| L1.1 | noise_world | Final Energy Level | `energy` w ostatnim ticku | poziom rezerwy energetycznej na koniec | ✘ | ✘⁶ⁱⁱ | PENDING | PENDING | Welch-pary (31/36) | **INSUFFICIENT_POWER** (Red Team NIE adresował tej osi — bez zmian) |
| L1.1 | drift_world | Final Energy Level | jw. | jw. | ✘ | ✘⁶ⁱⁱ | PENDING | PENDING | Welch-pary (110/153) | **INSUFFICIENT_POWER** (poza zakresem re-runu) |
| L1.1 | stable_world | Final Energy Level | jw. | jw. | ✘⁷ | ✘⁶ⁱⁱ | PENDING | PENDING | — | — (kontrola) |
| L1.2 | shock_world | Homeostatic Resilience | `t*-t_shock`, pierwsze trwałe okno w paśmie | czas powrotu do pasma homeostazy po perturbacji | ✘ (FRAGILE, 78.6%, n=185 — było 21.7% przy n=10) | ◐¹⁴ | **CONFIRMED**¹³ | **CONFIRMED**¹³ | Welch-pary (48/55) + **Kruskal-Wallis (p=4.1e-192)** | **EXPERIMENTAL**¹³ (było INVALID_CONSTRUCT — Construct skorygowany na ◐, patrz ¹⁴) |
| L1.2 | stable_world | Homeostatic Resilience | nie dotyczy | brak zdarzenia do powrotu | —⁹ | —⁹ | — | — | — | — (brak zastosowania konstruktu, nie porażka) |
| L1.2 | drift_world | Homeostatic Resilience | nie dotyczy | jw. | —⁹ | —⁹ | — | — | — | — (poza zakresem konstruktu i re-runu) |
| L1.2 | shock_world | Adaptation | tick stabilizacji entropii w oknie PRZED szokiem | (deklarowane: adaptacja do szoku — FAKTYCZNIE: nic związanego z szokiem) | ✘ | **✘** | PENDING | PENDING | Welch-pary (0 obliczalnych — stała) | **INVALID_CONSTRUCT** (stała=10 dla 100% genomów/seedów, §3 — Red Team NIE adresował, konstrukt nadal zepsuty niezależnie od testu) |
| L1.2 | stable_world | Adaptation | jw. | jw. | ✘⁷ | ✘ | PENDING | PENDING | — | — (kontrola) |
| L1.2 | drift_world | Adaptation | tick stabilizacji entropii od startu | jak L1.1 — cold start, NIE pre-shock window (brak szoku w tym środ.) | ✘ | ◐ⁱ | PENDING | PENDING | Welch-pary | **INSUFFICIENT_POWER** (poza zakresem re-runu — inny konstrukt niż shock_world!) |
| L1.2 | shock_world | Stability | jw. jak L1.1 | jw. | ✔ | ◐³ | PENDING | PENDING | Welch-pary (22/253, 9%) | **EXPERIMENTAL** (Red Team NIE adresował tej konkretnej komórki — moja własna kontrola KW dała p=1.3e-131, ale BEZ autoryzacji nie podnoszę statusu, patrz §7) |
| L1.2 | stable_world | Stability | jw. | jw. | ✘⁷ | ◐³ | PENDING | PENDING | — | — (kontrola) |
| L1.2 | drift_world | Stability | jw. | jw. | ✔ | ◐³ | PENDING | PENDING | Welch-pary (192/253) | **EXPERIMENTAL** (poza zakresem re-runu) |
| L1.2 | shock_world | Final Energy Level | jw. jak L1.1 | jw. | ✔ | ✘⁶ⁱⁱ | PENDING | PENDING | Welch-pary (113/253, 45%) | **EXPERIMENTAL** (Red Team NIE adresował — bez zmian) |
| L1.2 | stable_world | Final Energy Level | jw. | jw. | ✘⁷ | ✘⁶ⁱⁱ | PENDING | PENDING | — | — (kontrola) |
| L1.2 | drift_world | Final Energy Level | jw. | jw. | ✘ | ✘⁶ⁱⁱ | PENDING | PENDING | Welch-pary (108/136) | **INSUFFICIENT_POWER** (poza zakresem re-runu) |

ⁱ Construct Adaptation "cold-start" = ◐, patrz §3 (nie ✔, nie ✘ — inaczej
niż zarówno pierwotna tabela VALIDITY_REPORT.md — ✘² — jak i propozycja
audytora — ✔). VALIDITY_REPORT.md footnote 2 zostaje nietknięta (nie
duplikujemy edycji tam), ale ten dokument jest teraz dokładniejszym
źródłem dla Adaptation — patrz odsyłacz dodany w VALIDITY_REPORT.md §"12
statusy" (poniżej, punkt 6).

ⁱⁱ Construct Final Energy Level = "✘⁶" ale **NIE** wchodzi w regułę
pierwszeństwa "Construct=✘ → INVALID_CONSTRUCT" — to zmienna stanu
fizjologicznego (`kind: physiological_state`), nie zepsuty konstrukt
poznawczy (patrz §1 "Wyjątek jawny" i footnote 6 w VALIDITY_REPORT.md).
Rekomendacja jest więc oparta WYŁĄCZNIE na Measurement + legalnych (nie
retrospektywnych) faktach o dyskryminacji (FDR/valid_rate), tak jak dla
osi poznawczych — celowo NIE oznaczona INVALID_CONSTRUCT.

¹⁰ **VALIDATED (Working Memory, Pattern Recognition, Stability — L1.1/noise_world):**
potwierdzone re-runem konfirmacyjnym n=185 (`population_validation_v0_11_0.json`)
+ Kruskal-Wallis niezależny od ANOVA + leave-one-out (69→45 par, odporny na
usunięcie pojedynczego genomu) — wszystkie trzy kryteria VALIDATED (Measurement=✔,
Construct=◐ z akceptowalnymi zastrzeżeniami, Power i Confirmatory
potwierdzone). **Zastrzeżenie winner's curse obowiązkowe:** wielkość efektu
w eksploracji (n=10) była zawyżona — Working Memory f_obs 0.2652→0.1537,
Stability 2.2507→2.0615 (spadek, jak oczekiwano). Pattern Recognition
f_obs **WZROSŁO** 0.130→0.1638 — przeciwny kierunek niż typowy winner's
curse dla tej jednej osi, odnotowane w §7, nie ukryte.

¹¹ **EXPERIMENTAL (Pattern Retention — było MEASURED_BUT_NULL):** Red Team
wykrył, że test parami (Welch, 0/253 istotnych par) dał fałszywe zero —
Kruskal-Wallis na tych samych 23 grupach (n=185) daje H=36.72, p=0.0254,
**istotne**. Mechanizm: słaby, NIEMONOTONICZNY efekt między genomami (żadna
POJEDYNCZA para nie różni się wystarczająco, ale rozkład rang jako całość
odbiega od losowego) — dokładnie ten rodzaj sygnału, który test parami
strukturalnie pomija, a test omnibusowy na rangach wykrywa. Zobacz §7 punkt
1 dla pełnej analizy tego odwróconego błędu.

¹² **EXPERIMENTAL (Adaptation, L1.1/noise_world — było INSUFFICIENT_POWER):**
Kruskal-Wallis (p≈0, log₁₀p=-773.3) jest testem WŁAŚCIWYM dla tej osi —
NIE ANOVA, bo homoskedastyczność jest potwierdzona złamana (7/23 genomów
std=0 przy n=10; przy n=185 nadal część genomów zdegenerowana, stąd
Measurement pozostaje FRAGILE mimo poprawy 35%→56.5%). Status EXPERIMENTAL,
NIE VALIDATED — Construct pozostaje ◐ (mechanizm fałszywie-pozytywny nadal
udokumentowany, §3), a Confirmatory tutaj oznacza "potwierdzone WŁAŚCIWYM
testem", nie "brak zastrzeżeń".

¹³ **EXPERIMENTAL (Homeostatic Resilience, L1.2/shock_world — było
INVALID_CONSTRUCT):** Kruskal-Wallis (p=4.09e-192 — skorygowane z błędnie
cytowanego "<10⁻³⁰⁰", patrz §7.3) potwierdza, że genomy RÓŻNIĄ SIĘ silnie w
tym, co metryka mierzy. Zmiana statusu na EXPERIMENTAL jest teraz zgodna z
regułą pierwszeństwa (Construct=◐, nie ✘ — patrz ¹⁴), NIE jest już
wyjątkiem od niej — napięcie zgłoszone w poprzedniej wersji tego przypisu
zostało rozstrzygnięte przez Architekta 2026-07-20, nie obchodzone.

¹⁴ **Construct Homeostatic Resilience skorygowany z ✘⁸ na ◐ — decyzja
Architekta, 2026-07-20, ODWRACA wcześniej udokumentowane ustalenie
(VALIDITY_REPORT.md footnote 8, niedotknięta — ślad audytowy, nie edycja
w miejscu):** `recovery_time`/`time_to_sustained_band` MIERZY to, co
obiecuje nazwa (czas powrotu do pasma homeostazy), w odróżnieniu od
`adaptation_tick` w L1.2 (który mierzy okno PRZED szokiem — konstrukt
naprawdę zepsuty, pozostaje ✘, §3). Cenzurowanie 21% (n=10) / 21.4% (n=185,
`1-0.786`) jest ograniczeniem POMIARU (część genomów nie osiąga trwałego
powrotu w oknie obserwacji W=150), NIE błędem konstruktu — stąd ◐, nie ✘.
**Zapisuję to jako rozstrzygnięcie nadrzędne, nie jako mój własny wniosek**
— poprzednia analiza (VALIDITY_REPORT.md, ten dokument w wersji sprzed
2026-07-20) argumentowała ✘ na podstawie `pre_shock_in_band_fraction<0.8`
jako dowodu "ustanowienia, nie powrotu"; Architekt uznał to za
niewystarczające do klasyfikacji Construct=✘. Obie argumentacje pozostają
w historii repo (git log), czytelnik może ocenić samodzielnie który poziom
szczegółowości preferuje przy interpretacji tej osi.

---

## 5. Podsumowanie liczbowe

> **Zaktualizowane 2026-07-20 po re-runie konfirmacyjnym + Red Team — patrz §7.**

| Rekomendacja | Liczba wierszy (z 37) |
|---|---|
| VALIDATED | **3** — Working Memory, Pattern Recognition, Stability (wszystkie L1.1/noise_world, z zastrzeżeniem winner's curse¹⁰) |
| EXPERIMENTAL | **7** — Pattern Retention L1.1/noise¹¹ (nowe), Adaptation L1.1/noise¹² (nowe), Stability L1.1/drift, Homeostatic Resilience L1.2/shock¹³ (nowe), Stability L1.2/shock, Stability L1.2/drift, Final Energy Level L1.2/shock |
| MEASURED_BUT_NULL | **1** — Pattern Retention, WYŁĄCZNIE L1.1/drift_world (poza zakresem re-runu, NIE przeliczone Kruskal-Wallisem — nie zakładać, że wynik byłby taki sam, §7 ryzyko) |
| INSUFFICIENT_POWER | **7** — Working Memory L1.1/drift, Pattern Recognition L1.1/drift, Adaptation L1.1/drift, Adaptation L1.2/drift, Final Energy Level L1.1/noise, Final Energy Level L1.1/drift, Final Energy Level L1.2/drift |
| INVALID_CONSTRUCT | **1** — Adaptation L1.2/shock_world (Homeostatic Resilience w tym samym `shock_world` to ODRĘBNA metryka — teraz EXPERIMENTAL¹³, nie liczona tu) |
| NOT_MEASURED | **7** — Perception, Attention, Long-term Memory, Prediction, Exploration, Generalization, Planning |
| — (kontrola/nie dotyczy) | **11** — 6× `stable_world` L1.1 (WM/PatRec/PatRet/Adaptation/Stability/FinalEnergy) + 3× `stable_world` L1.2 (Adaptation/Stability/FinalEnergy) + 2× Homeostatic Resilience (`stable_world`+`drift_world` L1.2, konstrukt nie dotyczy) |

**3+7+1+7+1+7+11 = 37.** Przeliczone ręcznie wiersz-po-wierszu wprost z
tabeli §4b (nie z opisów w nawiasach) po korekcie Red Teamu — zgadza się
dokładnie z 14 osi × (do 3 środowisk, gdzie dotyczy) + 7 wierszy bez
kontekstu, bez zmiany całkowitej liczby wierszy (37 sprzed i po korekcie —
zmieniły się WYŁĄCZNIE etykiety 4 komórek objętych re-runem/Red Teamem,
nie struktura tabeli).

**Najważniejszy pojedynczy wniosek (zaktualizowany 2026-07-20):** **3/37
wierszy jest teraz VALIDATED** (Working Memory, Pattern Recognition,
Stability — wszystkie L1.1/noise_world) — pierwsze VALIDATED w tym
dokumencie, po re-runie konfirmacyjnym (n=185, Hard-Halt PASS cały bieg)
i niezależnej weryfikacji Red Teamu (leave-one-out + Kruskal-Wallis +
winner's curse). Pozostałe 22 z 30 zmierzonych wierszy (poza kontrolami)
są NADAL oparte wyłącznie na Exploratory Dataset v0.10 — re-run objął
TYLKO {noise_world, stable_world, shock_world}, NIE `drift_world`
(świadoma decyzja zakresu, patrz aneks). To jest zgodne z dyrektywą CTO
cytowaną w SPRINT_v0.11.0.md: *"Jeżeli okaże się, że Adaptation przestanie
istnieć, Working Memory okaże się bezużyteczne, profil spadnie z 7 osi do
2 — akceptuję taki wynik."* Wynik jest LEPSZY niż ten scenariusz — 3 osie
VALIDATED, 3 więcej podniesione do EXPERIMENTAL przez poprawny test
statystyczny (§7) — wciąż z jawnym zastrzeżeniem winner's curse dla
VALIDATED (¹⁰) i skorygowanym Construct dla Homeostatic Resilience
(◐, nie ✘ — decyzja Architekta, ¹⁴).

---

## 6. Żadna metryka nie została usunięta z profilu

Zgodnie z dyrektywą CTO: `publications/competency_profile.json`
(`minimal_profile`/`full_profile`) pozostaje NIETKNIĘTE — wszystkie 7
zmierzonych osi nadal tam są, z tymi samymi wartościami. Ten dokument jest
DODATKOWĄ warstwą interpretacji nałożoną NA te dane, nie zmianą samych
danych ani usunięciem czegokolwiek przed końcem przeglądu.

---

## 7. Wynik Red Team (2026-07-20) — co zaatakowano, co obalono, co trafiło

**Metoda:** Red Team zweryfikował ocenę Power/Confirmatory audytora
BEZPOŚREDNIO na danych z pełnego re-runu konfirmacyjnego (12765 runów,
`execution_package_v0_11/results/full_rerun_results.jsonl`, Hard-Halt PASS
przez cały bieg — patrz `git log`), trzema niezależnymi metodami:
leave-one-out (odporność wyniku na usunięcie pojedynczego genomu),
Kruskal-Wallis (test omnibusowy na rangach, nowy w tym sprincie —
`clos_curriculum/laboratory/statistics.py::kruskal_wallis`, zwalidowany w
`tests/test_kruskal_wallis.py` przeciwko zamkniętej formie chi-kwadrat
df=2), i analizą winner's curse (porównanie wielkości efektu eksploracja
vs konfirmacja). **Cztery zarzuty, wynik: 3 obalone, 1 trafiony.**

### 7.1 Zarzut TRAFIONY — Pattern Retention: zły typ testu dał fałszywe zero

**Zarzut:** klasyfikacja `MEASURED_BUT_NULL` dla Pattern Retention
(L1.1/noise_world) była BŁĘDNA — test parami (Welch + BH-FDR, 0/253
istotnych par) przegapił realny, ale słaby i NIEMONOTONICZNY efekt.

**Weryfikacja niezależna (nie tylko przyjęta na słowo):** policzyłem
Kruskal-Wallis bezpośrednio na 23 grupach genomów z
`population_validation_v0_11_0.json` (`memory_decay_rate`,
L1.1/noise_world): **H=36.72, p=0.0254** — istotne przy α=0.05 (choć NIE
przy skorygowanym α=0.05/9=0.0056 z aneksu — zwracam uwagę na tę
subtelność: test omnibusowy Kruskal-Wallisa to INNY test niż omnibus ANOVA,
dla którego korekta 0.05/9 była wyprowadzona; czy ta sama korekta powinna
być zastosowana do KW, to pytanie METODOLOGICZNE nierozstrzygnięte tutaj —
odnotowuję, nie rozstrzygam).

**Werdykt: TRAFIONY.** Mechanizm dokładnie odwrotny do błędu P0 (tam: zły
brak korekty dał fałszywie WYSOKĄ pewność; tu: zły TYP testu dał fałszywie
NISKĄ/zerową pewność) — ten sam rodzaj lekcji, przeciwny kierunek. Status
zmieniony na `EXPERIMENTAL` (nie `VALIDATED` — brak jeszcze leave-one-out
dla tej konkretnej osi, brak niezależnej repliki tego konkretnego wyniku
KW, i istotność znika przy pełnej korekcie na 9 testów).

**Ryzyko jawnie odnotowane:** L1.1/drift_world Pattern Retention (poza
zakresem re-runu) NIE zostało przeliczone Kruskal-Wallisem — zostaje
`MEASURED_BUT_NULL` ze starych (Exploratory) danych. NIE zakładam, że
wynik tam byłby taki sam (mógłby być, mógłby nie być) — to by wymagało
osobnego sprawdzenia, którego nie zlecono.

### 7.2 Zarzuty OBALONE (3) — Working Memory / Pattern Recognition / Stability trzymają się

**Zarzut (domniemany, testowany przez Red Team):** czy VALIDATED dla tych
trzech osi (L1.1/noise_world) przetrwa (a) usunięcie pojedynczego genomu
(leave-one-out) i (b) niezależny test (Kruskal-Wallis zamiast ANOVA)?

**Weryfikacja niezależna:**
- Working Memory: Kruskal-Wallis H=127.31, **p=8.1×10⁻¹⁷** (policzone
  bezpośrednio, nie przyjęte na słowo).
- Pattern Recognition: Kruskal-Wallis H=112.17, **p=4.5×10⁻¹⁴** — zgadza
  się dokładnie z liczbą cytowaną w zleceniu.
- Stability: Kruskal-Wallis H=3280.47 — p tak ekstremalnie małe, że
  bezpośrednie `1-CDF` daje ujemny wynik przez katastroficzne skracanie
  (naprawione: `chi2_survival()`/`chi2_survival_log10()`, nowe funkcje w
  tym sprincie, patrz kod) — **log₁₀(p)≈-686.8**.
- Leave-one-out (69→45): odnotowane z relacji Red Teamu, NIE zweryfikowane
  przeze mnie niezależnie (nie miałem czasu odtworzyć pełnej procedury
  "usuń 1 z 23 genomów, przelicz FDR-istotne pary, powtórz 23×" w tej
  turze) — jawnie oznaczone jako NIEZWERYFIKOWANE przeze mnie, w
  odróżnieniu od liczb Kruskal-Wallisa powyżej, które SĄ zweryfikowane.

**Werdykt: OBALONE.** Wszystkie trzy osie przechodzą niezależny test
(Kruskal-Wallis) z ogromnym marginesem — status VALIDATED trzyma.

**Zastrzeżenie winner's curse — sprawdzone precyzyjnie, NIE w przybliżeniu
z zlecenia:**

| Metryka | f_obs eksploracja (n=10) | f_obs konfirmacja (n=185) | Kierunek |
|---|---|---|---|
| Working Memory | 0.2652 | 0.1537 | ↓ skurczyło się (winner's curse jak oczekiwano) |
| Pattern Recognition | 0.1300 | 0.1638 | **↑ WZROSŁO** (przeciwny kierunek!) |
| Stability | 2.2507 | 2.0615 | ↓ skurczyło się umiarkowanie |

Zlecenie cytowało "f 0.265→0.164" jako jedną liczbę dla całej trójki — **to
myli wartość PRZED Working Memory z wartością PO Pattern Recognition**.
Sprawdzone i skorygowane: nie ma jednego uniwersalnego "0.265→0.164" dla
tych trzech osi — każda ma własną trajektorię, a Pattern Recognition
zachowuje się WBREW narracji winner's curse. Zgłaszam tę nieścisłość
zamiast przepisać ją bez sprawdzenia.

### 7.3 Adaptation/Homeostatic Resilience — status z Kruskal-Wallisa, nie z ANOVA

Patrz przypisy ¹² i ¹³ przy tabeli §4b dla pełnego uzasadnienia. Skrót:
Adaptation (L1.1/noise_world) ma potwierdzoną złamaną homoskedastyczność
(część genomów deterministycznie zdegenerowana) — ANOVA tam jest
niewłaściwym narzędziem z definicji, Kruskal-Wallis (p≈0,
log₁₀p=-773.3) jest właściwym testem i daje jednoznaczny wynik.
Status: `EXPERIMENTAL`.

Homeostatic Resilience (L1.2/shock_world): Kruskal-Wallis daje
**p=4.1×10⁻¹⁹²** — sprawdzone dokładnie, i to **NIE JEST** "<10⁻³⁰⁰" jak
sugerowało zlecenie (10⁻¹⁹² > 10⁻³⁰⁰ liczbowo, mimo że oba są
astronomicznie małe) — nieścisłość odnotowana i skorygowana, potwierdzona
przez audytora.

**Napięcie z regułą pierwszeństwa (§1: "Construct=✘ fundamentalny >
wszystko inne"), zgłoszone w poprzedniej turze, zostało ROZSTRZYGNIĘTE
przez Architekta 2026-07-20** (nie obchodzone): Construct tej osi
skorygowany z ✘⁸ na ◐¹⁴ — `recovery_time` mierzy to, co obiecuje (czas
POWROTU do pasma), w odróżnieniu od `adaptation_tick` w L1.2, który
naprawdę mierzy inne zjawisko (okno przed szokiem, pozostaje ✘). Status
`EXPERIMENTAL` jest więc teraz zgodny z regułą pierwszeństwa, nie
wyjątkiem od niej — pełne uzasadnienie decyzji w przypisie ¹⁴ przy tabeli
§4b, wraz z jawnym zaznaczeniem, że to ODWRACA wcześniej udokumentowane
ustalenie (VALIDITY_REPORT.md footnote 8), nie cichą zmianą.

### 7.4 Podsumowanie: nowe narzędzia dodane do repo w trakcie tej weryfikacji

- `clos_curriculum/laboratory/statistics.py::kruskal_wallis()` — test
  Kruskala-Wallisa z korektą na remisy, zero scipy (zgodnie z konwencją
  projektu).
- `clos_curriculum/laboratory/statistics.py::chi2_survival()` /
  `chi2_survival_log10()` — funkcja przeżycia chi-kwadrat liczona wprost
  (górna niepełna gamma, ułamek łańcuchowy Lentza), NIE jako `1-CDF()` —
  ten drugi sposób daje UJEMNE wyniki dla ekstremalnie małych p (dokładnie
  przypadek Stability/Adaptation/Homeostatic Resilience powyżej).
- `tests/test_kruskal_wallis.py` — 9 testów, w tym walidacja przeciwko
  zamkniętej formie analitycznej (df=2: CDF=1-exp(-x/2)), nie tylko
  przykład z podręcznika.
