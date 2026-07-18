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

| Lekcja | Środ. | Metryka | Definicja (skrót) | Interpretacja biologiczna | Measurement | Construct | Power | Confirm. | Rekomendacja |
|---|---|---|---|---|---|---|---|---|---|
| L1.1 | noise_world | Working Memory | `mean(mae@t≥stim+50)` | błąd predykcji utrzymany 50 ticków po ustaniu bodźca | ✔ | ◐¹ | PENDING | PENDING | **INSUFFICIENT_POWER** (moc PENDING do prospektywnego re-run; 0/253 par FDR-istotnych) |
| L1.1 | drift_world | Working Memory | jw. | jw. | ✔ | ◐¹ | PENDING | PENDING | **INSUFFICIENT_POWER** (moc PENDING do prospektywnego re-run; 0/253 par FDR-istotnych) |
| L1.1 | stable_world | Working Memory | jw. | jw. | ✘⁷ | ◐¹ | PENDING | PENDING | — (kontrola, nie klasyfikowana) |
| L1.1 | noise_world | Pattern Recognition | `mean(mae) w fazie bodźca` | błąd predykcji PODCZAS bodźca | ✔ | ◐⁴ | PENDING | PENDING | **INSUFFICIENT_POWER** (moc PENDING do prospektywnego re-run; 0/253 par FDR-istotnych) |
| L1.1 | drift_world | Pattern Recognition | jw. | jw. | ✔ | ◐⁴ | PENDING | PENDING | **INSUFFICIENT_POWER** (moc PENDING do prospektywnego re-run; 0/253 par FDR-istotnych) |
| L1.1 | stable_world | Pattern Recognition | jw. | jw. | ✘⁷ | ◐⁴ | PENDING | PENDING | — (kontrola) |
| L1.1 | noise_world | Pattern Retention | `(mae_silence-mae_stim)/silence_ticks` | tempo zaniku błędu po ustaniu bodźca | ✔ | ◐⁵ | PENDING | PENDING | **MEASURED_BUT_NULL** (wartości ∈[-0.000235, 0.000204], grand mean 1.3e-5) |
| L1.1 | drift_world | Pattern Retention | jw. | jw. | ✔ | ◐⁵ | PENDING | PENDING | **MEASURED_BUT_NULL** (wartości ∈[-0.000014, 0.000191], grand mean 9.0e-5) |
| L1.1 | stable_world | Pattern Retention | jw. | jw. | ✘⁷ | ◐⁵ | PENDING | PENDING | — (kontrola) |
| L1.1 | noise_world | Adaptation | tick stabilizacji entropii od startu | czas do ustania chaosu początkowego | ✘ | ◐ⁱ | PENDING | PENDING | **INSUFFICIENT_POWER** (35% valid_rate — fałszywie-pozytywne "tick=0", §3) |
| L1.1 | drift_world | Adaptation | jw. | jw. | ✘ | ◐ⁱ | PENDING | PENDING | **INSUFFICIENT_POWER** (43% valid_rate, jw.) |
| L1.1 | stable_world | Adaptation | jw. | jw. | ✘⁷ | ◐ⁱ | PENDING | PENDING | — (kontrola) |
| L1.1 | noise_world | Stability | `1/(std(entropy)+std(\|1-energy\|)+ε)` | stałość dynamiki wewnętrznej w czasie | ✔ | ◐³ | PENDING | PENDING | **EXPERIMENTAL** (208/253 par FDR-istotnych, 82%; moc prospektywna PENDING) |
| L1.1 | drift_world | Stability | jw. | jw. | ✔ | ◐³ | PENDING | PENDING | **EXPERIMENTAL** (168/253 par FDR-istotnych, 66%; moc prospektywna PENDING) |
| L1.1 | stable_world | Stability | jw. | jw. | ✘⁷ | ◐³ | PENDING | PENDING | — (kontrola) |
| L1.1 | noise_world | Final Energy Level | `energy` w ostatnim ticku | poziom rezerwy energetycznej na koniec | ✘ | ✘⁶ⁱⁱ | PENDING | PENDING | **INSUFFICIENT_POWER** (39% valid_rate; gdzie mierzalne: 31/36 par FDR-istotnych; moc prospektywna PENDING) |
| L1.1 | drift_world | Final Energy Level | jw. | jw. | ✘ | ✘⁶ⁱⁱ | PENDING | PENDING | **INSUFFICIENT_POWER** (78% valid_rate, graniczne; gdzie mierzalne: 110/153 par) |
| L1.1 | stable_world | Final Energy Level | jw. | jw. | ✘⁷ | ✘⁶ⁱⁱ | PENDING | PENDING | — (kontrola) |
| L1.2 | shock_world | Homeostatic Resilience | `t*-t_shock`, pierwsze trwałe okno w paśmie | czas do USTANOWIENIA homeostazy po perturbacji | ✘ | ✘⁸ | PENDING | PENDING | **INVALID_CONSTRUCT** (mierzy ustanowienie, nie powrót; 78% cenzurowane) |
| L1.2 | stable_world | Homeostatic Resilience | nie dotyczy | brak zdarzenia do powrotu | —⁹ | —⁹ | — | — | — (brak zastosowania konstruktu, nie porażka) |
| L1.2 | drift_world | Homeostatic Resilience | nie dotyczy | jw. | —⁹ | —⁹ | — | — | — (jw.) |
| L1.2 | shock_world | Adaptation | tick stabilizacji entropii w oknie PRZED szokiem | (deklarowane: adaptacja do szoku — FAKTYCZNIE: nic związanego z szokiem) | ✘ | **✘** | PENDING | PENDING | **INVALID_CONSTRUCT** (stała=10 dla 100% genomów/seedów, §3) |
| L1.2 | stable_world | Adaptation | jw. | jw. | ✘⁷ | ✘ | PENDING | PENDING | — (kontrola) |
| L1.2 | drift_world | Adaptation | tick stabilizacji entropii od startu | jak L1.1 — cold start, NIE pre-shock window (brak szoku w tym środ.) | ✘ | ◐ⁱ | PENDING | PENDING | **INSUFFICIENT_POWER** (43% valid_rate, §3 — inny konstrukt niż shock_world!) |
| L1.2 | shock_world | Stability | jw. jak L1.1 | jw. | ✔ | ◐³ | PENDING | PENDING | **EXPERIMENTAL** (22/253 par FDR-istotnych, 9% — słabsza dyskryminacja niż L1.1; moc prospektywna PENDING) |
| L1.2 | stable_world | Stability | jw. | jw. | ✘⁷ | ◐³ | PENDING | PENDING | — (kontrola) |
| L1.2 | drift_world | Stability | jw. | jw. | ✔ | ◐³ | PENDING | PENDING | **EXPERIMENTAL** (192/253 par FDR-istotnych, 76%; moc prospektywna PENDING) |
| L1.2 | shock_world | Final Energy Level | jw. jak L1.1 | jw. | ✔ | ✘⁶ⁱⁱ | PENDING | PENDING | **EXPERIMENTAL** (113/253 par FDR-istotnych, 45%; moc prospektywna PENDING) |
| L1.2 | stable_world | Final Energy Level | jw. | jw. | ✘⁷ | ✘⁶ⁱⁱ | PENDING | PENDING | — (kontrola) |
| L1.2 | drift_world | Final Energy Level | jw. | jw. | ✘ | ✘⁶ⁱⁱ | PENDING | PENDING | **INSUFFICIENT_POWER** (74% valid_rate, graniczne; gdzie mierzalne: 108/136 par, 79%) |

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

---

## 5. Podsumowanie liczbowe

| Rekomendacja | Liczba wierszy (z 37) |
|---|---|
| VALIDATED | **0** — żaden wiersz nie spełnia (wymaga potwierdzonej mocy I repliki, oba PENDING) |
| EXPERIMENTAL | 6 (Stability ×4 środowiska eksperymentalne, Final Energy Level L1.2 shock_world) |
| MEASURED_BUT_NULL | 2 (Pattern Retention, oba środowiska eksperymentalne L1.1) |
| INSUFFICIENT_POWER | 12 (Working Memory ×2, Pattern Recognition ×2, Adaptation ×3 [L1.1×2 + L1.2/drift], Final Energy Level ×3 [L1.1×2 + L1.2/drift]) |
| INVALID_CONSTRUCT | 2 (Homeostatic Resilience shock_world, Adaptation L1.2/shock_world) |
| NOT_MEASURED | 7 (Perception, Attention, Long-term Memory, Prediction, Exploration, Generalization, Planning) |
| — (kontrola/nie dotyczy) | 8 (6× `stable_world` L1.1 + 2× L1.2 `stable_world`/`drift_world` Homeostatic Resilience) |

**0+6+2+12+2+7+8 = 37.** Zgadza się z 14 osi × (do 3 środowisk, gdzie
dotyczy) + 7 wierszy bez kontekstu.

**Najważniejszy pojedynczy wniosek:** **0/37 wierszy jest VALIDATED.**
Najlepszy obecny status to EXPERIMENTAL (6 wierszy, wszystkie albo
Stability, albo Final Energy Level w L1.2/shock_world) — realny,
dyskryminujący sygnał, ale bez niezależnego potwierdzenia. To jest zgodne
z dyrektywą CTO cytowaną w SPRINT_v0.11.0.md: *"Jeżeli okaże się, że
Adaptation przestanie istnieć, Working Memory okaże się bezużyteczne,
profil spadnie z 7 osi do 2 — akceptuję taki wynik."* Ta tabela pokazuje
dokładnie, które 2 (a właściwie: 1 metryka × 4 konteksty) obecnie
najlepiej się trzymają.

---

## 6. Żadna metryka nie została usunięta z profilu

Zgodnie z dyrektywą CTO: `publications/competency_profile.json`
(`minimal_profile`/`full_profile`) pozostaje NIETKNIĘTE — wszystkie 7
zmierzonych osi nadal tam są, z tymi samymi wartościami. Ten dokument jest
DODATKOWĄ warstwą interpretacji nałożoną NA te dane, nie zmianą samych
danych ani usunięciem czegokolwiek przed końcem przeglądu.
