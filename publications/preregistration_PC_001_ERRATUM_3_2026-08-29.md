# ERRATUM 3 do ANEKS 1 i PC-001 §5 (K1, K4, K5)

**Data:** 2026-08-29
**Status:** **ZATWIERDZONY** decyzją **CTO**, B4C-2 (15) - domknięcie Negative-Control Inference
Review (B4C-2 (06) pkt 8), z korektą definicji `E_beta` wniesioną przez CTO.
**Podstawa:** Negative-Control Inference Review - BH-FDR kontroluje odsetek fałszywych ODRZUCEŃ,
nie fałszywych BRAKÓW odrzucenia; dla sześciu komórek, gdzie wsparcie hipotezy oznaczało dotąd
`kierunek_wsparcia="BRAK_ODRZUCENIA_H0"`, moc wykrycia naruszenia nie była nigdy policzona.
**Autor:** CTO (rozstrzygnięcie, korekta `E_beta`), wykonawca (szkic techniczny)
**Rodzaj dokumentu:** **ERRATUM do reguły decyzyjnej** - nie doprecyzowanie. ANEKS 1 i PC-001 §5
pozostają **NIETKNIĘTE** w pierwotnym brzmieniu; to erratum nadpisuje je **NORMATYWNIE**.

---

## Powód erratum

`ANEKS 1 → "Zaktualizowana reguła decyzyjna"` (warunki 4, 7, 8) i `PC-001 §5` (K1, K4, K5) mówią,
że te sześć komórek wspiera hipotezę PC, gdy efekt **nie występuje** w danych kontrolnych
(przetasowanych, czystego szumu, po ablacji) - operacyjnie: `p > próg BH` ⇒ wsparcie.

**To jest błąd metodologiczny.** `p > próg` nie znaczy „efekt zniknął" - może znaczyć: brak
efektu, za mała próba, za duża wariancja albo za mała moc testu. Analogia: przy `p=0.30` dla leku
nie wolno powiedzieć „udowodniono, że lek nie działa", tylko „nie wykazano działania". BH-FDR
kontroluje odsetek fałszywych ODRZUCEŃ wśród odrzuceń - dla komórek, gdzie **brak** odrzucenia
jest gałęzią wsparcia, nie kontroluje niczego: żadna moc wykrycia naruszenia nie została policzona.

**Cytaty doskonałe, spornych brzmień:**

> ANEKS 1 → „Zaktualizowana reguła decyzyjna", warunek 4: „K1 — efekt nie występuje w danych
> przetasowanych"

> ANEKS 1 → „Zaktualizowana reguła decyzyjna", warunek 7: „K4 — brak efektu w czystym szumie
> ORAZ istotna separacja od środowiska realnego"

> ANEKS 1 → „Zaktualizowana reguła decyzyjna", warunek 8: „K5 — efekt znika po ablacji
> surogatowej"

> PC-001 §5 → „K1": „Kryterium PC: w danych przetasowanych nie wolno uzyskać spełnienia A ani B."

> PC-001 §5 → „K4": „Kryterium PC: nie wolno uzyskać spełnienia A ani B."

> PC-001 §5 → „K5": „Kryterium PC: spełnienie A i B musi zniknąć."

---

## Poprawka: przejście na wnioskowanie o równoważności

**Sześć komórek (K1-A, K1-B, K4-A, K4-B, K5-A, K5-B) przechodzi z kryterium „brak odrzucenia H0"
na formalne wnioskowanie o RÓWNOWAŻNOŚCI PRAKTYCZNEJ** (TOST - Two One-Sided Tests), zamiast
interpretować `p > próg` jako dowód braku efektu.

### Margines równoważności `c = 0.10`

**ZAMROŻONY, z powodów MERYTORYCZNYCH, nie obliczeniowych.** `c` jest **połową** progu Warunku B
(`CONFIG::CONDITION_B_REDUCTION_THRESHOLD = 0.20`) - tworzy to jawną **strefę rozdzielającą**:

| Zakres `|efekt|` | Interpretacja |
|---|---|
| `≤ 0.10` | praktycznie brak efektu (równoważność wsparta) |
| `0.10 < \|efekt\| < 0.20` | strefa niejednoznaczna (ani równoważność, ani Warunek B) |
| `≥ 0.20` | efekt Warunku B (redukcja praktycznie istotna) |

Granica `0.20` sama dawałaby zerową strefę rozdzielającą - `19.9%` liczyłoby się jako „brak
efektu", a `20.1%` jako „efekt", mimo że różnica między nimi jest szumem pomiarowym, nie
sygnałem. Konwencja przyjęta z góry - **zmiana `c` po obejrzeniu danych jest niedopuszczalna**
(ta sama zasada co przy progu 20% Warunku B, ANEKS 1 → „Zmiana 4").

**ZAKAZ wprost:** granica równoważności NIE jest wyprowadzona z mediany Pilota Final ani z żadnej
innej wartości historycznej (`reports/pilot/pilot_final.json` jest oznaczony
`NEVER_FOR_INFERENCE`) - wcześniejsza propozycja wykonawcy (`Δ_beta = c · W_early_red_mediana /
300`) została **odrzucona przez CTO z dwóch powodów**: (1) granica metodologiczna zależałaby od
jednej historycznej liczby z artefaktu oznaczonego jako nigdy-do-wnioskowania - rozróżnienie
„używam jej wyłącznie jako skali" jest subtelne i dlatego kruche; za pół roku zostałaby po nim
zamrożona w definicji endpointu liczba `0.15718`. (2) błąd arytmetyczny - przy tickach `0..299`
odstęp między pierwszym a ostatnim punktem wynosi **299**, nie 300. Normalizacja PER BLOK
(poniżej) usuwa oba problemy naraz.

### Definicje efektu, obie bezwymiarowe

**Grupa B (K1-B, K4-B, K5-B) - `E_red`:**

```
E_red = redukcja_W2   (już bezwymiarowe - iloraz (W_early_red − W_late_red) / W_early_red)
```

Grupa B testuje: `|redukcja_W2| < c`.

**Grupa A (K1-A, K4-A, K5-A) - `E_beta`:**

```
E_beta = beta * (t_last − t_first) / W_early_red     — POLICZONE PER PRZEBIEG
```

gdzie `beta` = `linear_slope(ticks, PE_red(t))` na pełnej siatce tego przebiegu, `t_last`/
`t_first` = ostatni/pierwszy tick TEJ SAMEJ siatki (`tick_span = t_last − t_first`, **wyprowadzony
z faktycznej siatki, nie wpisany jako literał** - patrz sekcja „Kolejność operacji"), `W_early_red`
= wielkość mianownika TEGO SAMEGO przebiegu (ta sama, którą liczy `compute_w2_reduction`).

`E_beta` jest miarą „ile PE_red zmieniło się na przestrzeni całego okna, względem tego, ile było
na starcie" - bezwymiarowe z tego samego powodu co `redukcja_W2` (dzielenie przez `W_early_red`).

Grupa A testuje: `|E_beta| < c`.

### Kolejność operacji: PER PRZEBIEG, potem `block_means`

**Wymóg wiążący, zweryfikowany zgodnością z już istniejącym kodem:** `E_beta` i `E_red` liczone są
**PER PRZEBIEG** (jeden genom, jeden seed), **DOPIERO POTEM** uśredniane przez `STATS::block_means`
po 23 genomach do jednej wartości na blok seedowy. Średniej ilorazów nie wolno mylić z ilorazem
średnich.

Zgodność z istniejącym kodem: `clos_scientist.w2_endpoint.compute_w2_reduction` liczy
`redukcja_W2` PER PRZEBIEG (mianownik `W_early_red` z okna TEGO przebiegu), dopiero `STATS::
block_means` uśrednia po genomach. `clos_scientist.pc_001_evaluator.k4_separation_cell` (B4C-2
(09)) stosuje dokładnie ten sam porządek: `_reduction_by_seed` liczy redukcję per przebieg, potem
`block_means`. `E_beta` **musi** iść tym samym porządkiem - inaczej Warunek A, K1-A, K4-A, K5-A
liczyłyby nachylenie inaczej niż komórki równoważności, co złamałoby porównywalność, którą chroni
wspólna implementacja `linear_slope`.

`tick_span` jest polem raportu (dziś `299`), ale w kodzie **wyprowadzany z faktycznej siatki**
(`tick_span = max(ticks) − min(ticks)`), z asercją, że równa się `299` przy dzisiejszym
protokole - wpisany literał przestałby być prawdziwy przy zmianie długości przebiegu i nikt by
tego nie zauważył; asercja padnie głośno.

### Test statystyczny: TOST

**Jedna komórka = jeden `p_equivalence = max(p_lower, p_upper)`** (TOST, dwie jednostronne wersje
Wilcoxona signed-rank na dziewięciu wartościach blokowych, `STATS::tost_wilcoxon`):

- `p_lower`: `H1: mediana(efekt) > −c` (odrzuca H0 „prawdziwy efekt ≤ −c")
- `p_upper`: `H1: mediana(efekt) < +c` (odrzuca H0 „prawdziwy efekt ≥ +c")
- `p_equivalence = max(p_lower, p_upper)` - **wprost**, nie średnia, nie minimum. Równoważność
  wymaga odrzucenia OBU jednostronnych H0 jednocześnie, więc `p` łączne jest zdeterminowane przez
  słabszy z dwóch dowodów.

Granice (`−c`, `+c`) pochodzą z **jednej** wartości `equivalence_margin_c` zapisanej w artefakcie
rodziny (`publications/pc_001_bh_family.json`) per komórka - **nie ze stałej wpisanej w kodzie
evaluatora**.

**Warstwa opisowa (obserwowany efekt, jego wielkość względem `c`) jest CZĘŚCIĄ wyniku TOST, nie
osobnym mechanizmem** - nie definiuje się żadnej dodatkowej miary wielkości efektu poza tym, co
TOST już produkuje (`observed_effect`, granice, `p_lower`/`p_upper`/`p_equivalence`).

### Warunki twarde dla `E_beta` (per obserwacja blokowa)

Wymagane jednocześnie: `beta` skończone, siatka kompletna, `W_early_red` skończone, `W_early_red
> 0`. Brak któregokolwiek ⇒ komórka **NONCOMPUTABLE** ⇒ cały PC-001 **INCONCLUSIVE** (scenariusz A,
B4C-2 (01) v2) - **NIGDY** epsilon, mediana populacji, wartość z pilota, pominięcie bloku ani
zmniejszenie `n`.

**Asymetria zastana (nie wprowadzona tym erratum):** przebieg `FLOOR_LIMITED` ma `W_early_red`
**dodatnie**, tylko poniżej `MIN_DENOMINATOR` - `E_beta` jest więc dla niego **definiowalne**, mimo
że `redukcja_W2` (potrzebne dla `E_red`, Grupa B) jest wtedy `None` z mocy istniejącego kontraktu
W2 (`compute_w2_reduction`, gałąź `classification != "VALID"`). Ta asymetria między Grupą A i
Grupą B jest **zastana właściwość istniejącego kontraktu W2** (Warunek A od zawsze liczony także
dla `FLOOR_LIMITED`, W2-SPEC §3.4) - odnotowana tu wprost, żeby nikt jej nie „naprawił" jako
przeoczenia.

---

## Co pozostaje bez zmian

`m = 11` **BEZ ZMIAN** - to erratum nie zmienia liczby komórek, koryguje wyłącznie **kryterium
wsparcia** sześciu z nich. `N_operational_current = 9` (ERRATUM 2) **BEZ ZMIAN w tym erratum** -
`N_operational_final` pozostaje **pending equivalence power check** (krok następny, osobne
zlecenie: moc każdej z sześciu komórek, minimum z sześciu, `P(cała szóstka przechodzi)` przy
prawdziwej równoważności, zachowanie po korekcie BH przy `m=11`; próg akceptacji 80% dla każdej
komórki, próg dla `P(all 6)` jeszcze nie ustanowiony). **Niska moc zmienia `N`, NIGDY `c`.**

K3a-warunek1, A, B, K4-separacja, K6 (pięć komórek `ODRZUCENIE_H0`) **BEZ ZMIAN** - to erratum
dotyczy wyłącznie sześciu komórek `RÓWNOWAŻNOŚĆ`.

---

## Zamrożenie

Po zatwierdzeniu erratum zostaje zamrożone jako
`publications/preregistration_PC_001_ERRATUM_3_2026-08-29.json`, z hashem w rejestrze
(`CRITICAL_FILES_PC_001`, razem z tym dokumentem `.md`). Korekta wykonana **przed pierwszym
przebiegiem konfirmacyjnym PC-001** i **przed policzeniem `PC_001_BASELINE`** (B5, dodatkowo
wstrzymane do zamknięcia power check dla równoważności - decyzja CTO pkt 12).
