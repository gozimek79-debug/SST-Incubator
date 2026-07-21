# Validity Report — granice interpretacji 14 osi Competency Profile

> **⚠ STATUS DANYCH: Exploratory Dataset v0.10 (SPRINT_v0.11.0.md).** Analiza
> mocy statystycznej (v0.11.0 P0) wykazała, że populacja n=10/genom (v0.10.1
> P3), na której oparty jest cały ten dokument, ma bardzo niską moc wykrycia
> czegokolwiek poza ogromnymi efektami po korekcie na wielokrotne porównania
> (patrz `publications/preregistration_v0_11_0_power_reproduction.json`).
> **Ten dokument NIE jest poprawiany ani wycofywany** — pozostaje wiarygodnym
> zapisem tego, co dało się ustalić na etapie n=10, wraz z metodologią, która
> to ustaliła. Klasyfikacje ROBUST/FRAGILE i wnioski o dyskryminacji poniżej
> mają status **Measurement/Construct validity: aktualny**, ale
> **Power/Confirmatory validity: PENDING** do czasu re-run zatwierdzonego
> przez CTO (Wariant A/B/C — decyzja w toku). Nie cytować klasyfikacji z tego
> dokumentu jako ostatecznych bez sprawdzenia statusu re-run.

> **AKTUALIZACJA 2026-07-21 — re-run konfirmacyjny (n=185) zamknięty
> 2026-07-20, status Power/Confirmatory z bloku powyżej PRZESTAJE być
> PENDING dla Working Memory, Pattern Recognition, Pattern Retention.**
> Pełne dane: `reports/population/population_validation_v0_11_0.json`,
> `docs/METRIC_STATUS_TABLE.md` §4b + §7 (Red Team) + footnote¹⁵. Streszczenie
> — skorygowane 2026-07-21 po tym, jak audytor złapał błąd w PIERWSZEJ
> wersji tej adnotacji (patrz niżej "KOREKTA"):
>
> - **Working Memory (p=8.1e-17), Pattern Recognition (p=4.5e-14) →
>   VALIDATED** (footnote¹⁰): potwierdzone NIEZALEŻNIE dwoma testami —
>   Kruskal-Wallis (omnibusowy) ORAZ Welch-pary+BH-FDR (parowy). Liczba par
>   genomów przeżywających FDR na n=185: **Working Memory 69/253 (27%),
>   Pattern Recognition 77/253 (30%)** — zweryfikowane bezpośrednio na
>   `pairwise_comparisons.n_fdr_significant_q_0_05` w surowym pliku +
>   niezależny przelicz BH-FDR z `pairwise_comparisons.details`, oba zgodne.
>   Zastrzeżenie winner's curse obowiązkowe: wielkość efektu z eksploracji
>   (n=10) była zawyżona dla WM (f 0.2652→0.1537) i nietypowo WZROSŁA dla
>   Pattern Recognition (f 0.130→0.1638) — patrz footnote¹⁰.
> - **Pattern Retention (p=0.0254) → EXPERIMENTAL** (footnote¹¹): Red Team
>   wykrył, że pierwotna klasyfikacja MEASURED_BUT_NULL była BŁĘDNA — test
>   parowy dał fałszywe zero (**0/253, potwierdzone — to jest jedyna z
>   trzech osi, dla której 0/253 jest poprawne również na n=185**),
>   Kruskal-Wallis wykrył słaby, NIEMONOTONICZNY efekt, którego test parowy
>   strukturalnie nie widzi.
> - **KOREKTA 2026-07-21 (znaleziona przez audytora na surowym pliku,
>   PIERWSZA wersja tej adnotacji była błędna):** wcześniej napisałem tu, że
>   "0/253 pozostaje prawdziwe również na n=185" dla WSZYSTKICH trzech osi —
>   to jest fałszywe dla Working Memory i Pattern Recognition (prawdziwe
>   tylko dla Pattern Retention). Skopiowałem liczbę z etapu eksploracyjnego
>   (n=10) zamiast odczytać ją z `population_validation_v0_11_0.json`
>   (n=185). Poprawka: 69/253 i 77/253 — patrz wyżej. **Dla Working
>   Memory/Pattern Recognition NIE ma rozdźwięku "omnibus wykrywa, parowy
>   nie"** — oba testy się zgadzają, to silniejszy wynik niż wcześniej
>   zapisany, nie dwuznaczny. Zabronione pozostaje wyłącznie twierdzenie o
>   KONKRETNEJ, niewskazanej parze bez sprawdzenia, czy akurat ta para jest
>   jedną z tych 69 (WM) / 77 (Pattern Recognition) istotnych — sprawdź
>   `pairwise_comparisons.details` dla konkretnych genomów przed
>   twierdzeniem "genom X różni się od genomu Y".

**Status: SPRINT_v0.10.1.md P4 (Zadanie 3 CTO).** Ten dokument NIE poprawia
żadnej metryki — dyrektywa CTO: "poznaj granice", nie "napraw". Konsoliduje
ograniczenia znane z v0.9/v0.10 i rozszerza je o dane z walidacji populacyjnej
(v0.10.1 P3, `reports/population/population_validation_v0_10_1.json`, 23
genomy × do 3 środowisk × 10 seedów). Definicje poznawcze pojęć są w
[cognitive_ontology.md](../clos_academy/cognitive_ontology.md) — ten dokument
odpowiada na inne pytanie: **kiedy wolno ufać liczbie, którą ta oś zwraca**.

Legenda stanu (P3, `clos_academy/population_validation.py`): **GENOME-ROBUST**
= ≥80% z 23 genomów ma `ci95_valid=True` I `n_effective≥5` (mierzalna).
**GENOME-FRAGILE** = poniżej tego progu. **FDR-discriminating** = po korekcie
Benjamini-Hochberg (q=0.05) na wszystkich parach genomów co najmniej jedna
para pozostaje istotna — patrz §"Kluczowe odkrycie" poniżej, zanim przejdziesz
do sekcji per oś: **ROBUST i discriminating to dwa różne pytania.**

**Rozróżnienie prerejestrowane vs. post-hoc, stosowane konsekwentnie w tym
dokumencie:** klasyfikacja ROBUST/FRAGILE i wynik korekty FDR są
**prerejestrowanym** wyjściem analizy zaplanowanej w
`preregistration_v0_10_1_population.json` PRZED uruchomieniem populacji —
te liczby traktujemy jako wynik, nie hipotezę. Wszelkie DALSZE wyjaśnienia
mechanizmu (np. korelacja z konkretnym genem), zauważone dopiero PO
zobaczeniu tych wyników, na tych samych danych, są oznaczone wprost jako
**post-hoc/eksploracyjne — hipoteza do przyszłego, osobno prerejestrowanego
testu**, nie jako ustalenie. Te dwie kategorie nigdy nie są mieszane bez
etykiety.

---

## KLUCZOWE ODKRYCIE Z P3: "ROBUST" ≠ "wykrywa różnice między genomami"

**GENOME-ROBUST znaczy wyłącznie: da się to policzyć wiarygodnie (realna
wariancja międzyseedowa, CI95 ważne). NIE znaczy: różne genomy dają różne
wartości.** To dwa oddzielne pytania (patrz też
[preregistration_v0_10_1_population.json](../publications/preregistration_v0_10_1_population.json)
`metrology.robustness_definition.distinct_from_multiple_comparisons`).

**Working Memory jest 100% GENOME-ROBUST w obu środowiskach, gdzie ma
zastosowanie (`noise_world`, `drift_world`) — a mimo to ZERO z 253 par
genomów przeżywa korektę FDR w którymkolwiek z nich:**

| Środowisko | valid_rate | par ogółem | istotnych PRZED FDR (p<0.05) | istotnych PO FDR (q=0.05) |
|---|---|---|---|---|
| noise_world | 100% (23/23) | 253 | 3 | **0** |
| drift_world | 100% (23/23) | 253 | 0 | **0** |

3 "surowo istotne" pary w `noise_world` to dokładnie tyle, ile oczekuje się z
samego przypadku przy 253 porównaniach i α=0.05 (253×0.05≈12.65 — 3 to
*mniej* niż szum, nie więcej) — FDR poprawnie odrzucił wszystkie jako
niewystarczający dowód.

**To samo dotyczy Pattern Recognition i Pattern Retention** — również 100%
ROBUST w obu środowiskach, również 0/253 par przeżywa FDR w każdym z nich
**na tym etapie (n=10, Exploratory Dataset — liczby w tym akapicie NIE są
poprawiane, zapis historyczny).** Trzy z siedmiu zmierzonych osi są więc
wiarygodnie mierzalne, ale w tej próbce 23 genomów na n=10 **nie różnicują
genomów w żaden sposób, który przetrwałby korektę na wielokrotne
porównania.** **Patrz AKTUALIZACJA 2026-07-21 powyżej: na n=185
konfirmacyjnym to się zmieniło ODMIENNIE dla każdej osi** — Working Memory
i Pattern Recognition dyskryminują teraz TAKŻE parowo (69/253 i 77/253),
Pattern Retention nadal 0/253 parowo, tylko omnibusowo (Kruskal-Wallis).

**Retroaktywna kontekstualizacja wyniku v0.9/v0.10:** `competency_profile.md`
raportuje Cohen's d=0.327 dla Working Memory między `default` i
`highly_plastic` (2 genomy, bez korekty — przy jednym porównaniu korekta na
wielokrotność jest bezprzedmiotowa). Ta pojedyncza para WYGLĄDA jak sygnał
(dodatni Cohen's d, w kierunku "highly_plastic gorszy"). Na 23 genomach,
**żadna para — w tym prawdopodobnie ta konkretna — nie utrzymuje się jako
istotna po FDR.** Nie znaczy to, że pomiar d=0.327 był błędny — znaczy, że
**przy tylko 2 punktach w przestrzeni genomów nie było możliwości odróżnić
"realnej różnicy między tymi dwoma konkretnymi genomami" od "szumu, który
akurat tak wypadł"**. Populacja 23 genomów dająca odpowiedź "brak
wystarczającego dowodu różnicy" jest bardziej wiarygodna niż pojedyncze
porównanie par — to jest dokładnie to, po co CTO zlecił ten sprint.

Kontrast: **Stability i Final Energy Level (gdy ROBUST) DYSKRYMINUJĄ silnie**
— np. Stability w `noise_world`: 208/253 par przeżywa FDR (82% wszystkich
par genomów różni się istotnie). Nie każda zmierzona oś ma ten sam charakter
— stąd potrzeba tej tabeli per metryka, nie jednego zbiorczego wniosku.

---

## Perception

**Formalna definicja (P1):** nie dotyczy — brak lekcji, brak endpointu do
sformalizowania. Mechanizm (`perceive()`) istnieje w Core, ale mechanizm
≠ zmierzony endpoint (zasada uczciwości, `cognitive_ontology.md`).

**Co mierzy:** nic — `not yet measured` (bez zmian od v0.8.4).
**Czego NIE mierzy:** brak lekcji izolującej percepcję jako endpoint.
**Kiedy zdegenerowana:** nie dotyczy (brak pomiaru).
**Kiedy myląca:** nie dotyczy.
**Kiedy wymaga innej interpretacji:** `insufficient_data` w Competency
Profile nie znaczy "słaba percepcja" — znaczy "nikt tego nie zmierzył".

---

## Attention

**Formalna definicja (P1):** nie dotyczy — `attention_threshold` jest
GENEM (wejsciem), nie zmierzonym wyjsciem; zaden endpoint go nie testuje
jako zmienna niezalezna.

**Co mierzy:** nic — `not yet measured`. `attention_threshold` istnieje i
wpływa pośrednio na L1.1 (dobór rekordów pamięci w `predict()`), ale nie
jest testowany jako zmienna niezależna, i (patrz P3) nigdy nie jest
próbkowany w populacji — trzymany na stałe 0.3 dla wszystkich 23 genomów.
**Czego NIE mierzy:** selektywności uwagi w żadnym ilościowym sensie.
**Kiedy zdegenerowana / myląca:** nie dotyczy.
**Kiedy wymaga innej interpretacji:** identycznie jak Perception.

---

## Pattern Recognition (`mae_stimulus_phase`, dawniej `mse_stimulus_phase`)

**NAPRAWIONE (SPRINT_v0.11.0.md P1, 2026-07-15):** pole przemianowane z
`mse_stimulus_phase` na `mae_stimulus_phase` w kodzie (`lesson_L1_1.py` i
wszystkich konsumentach) — wartości i formuła BEZ ZMIAN, to korekta nazwy,
nie pomiaru. Zamrożone `publications/preregistration_L1_1.json` i już
opublikowany bundle `publications/L1_1_pattern_echo/` NIE zostały dotknięte
(świadomie — patrz datowany aneks
`publications/preregistration_L1_1_ANEKS_2026-07-15_MSE_do_MAE.json` i
`docs/MSE_MAE_NAMING_DECISION.md` dla pełnego uzasadnienia Wariantu (c)).
Poniższy opis "NAZWA vs POMIAR" to zapis ODKRYCIA (historia), zachowany
celowo — nazwa `mse_stimulus_phase` istniała od v0.8.4 do tej naprawy.

**Formalna definicja (P1, SPRINT_v0.11.0.md):**
```
error(t)          = |tissue.last_prediction(t) - pattern_signal(t)|     (BLAD BEZWZGLEDNY, nie kwadrat)
telemetry_ticks    = {t : t < stimulus_ticks, t mod 5 = 0}              (PROBKOWANE co 5. tick, nie kazdy)
mae_stimulus_phase = mean_{t in telemetry_ticks} error(t)
```
Domena: `stimulus_ticks=100` (domyslnie L1.1). Warunek brzegowy: jesli
`telemetry_ticks` jest puste, wynik = 0 (nie NaN/wyjatek - patrz P2 dla
konsekwencji tego wyboru).

**NAZWA vs POMIAR (P1, ODKRYCIE): NIEZGODNOSC PODWOJNA, JEDNA POLOWA
NAPRAWIONA.** (1) Prefiks `mse_` sugerowal Mean SQUARED Error — kod liczy
`abs()`, nie `**2`. To jest **Mean Absolute Error** — dotyczylo WSZYSTKICH
pol z dawnym prefiksem `mse_` w L1.1 (`mse_stimulus_phase`→`mae_stimulus_phase`,
`mse_silence_phase`→`mae_silence_phase`, `mse_at_tick_50`/Working Memory) —
**NAPRAWIONE** (rename, wartosci bez zmian). (2) "Recognition" nadal sugeruje
dyskretny, binarny osad (rozpoznane/nie) — metryka jest ciagla (sredni
blad), nie ma progu decyzyjnego "rozpoznane" — **NIENAPRAWIONE**, poza
zakresem tej korekty (pytanie o ontologie pojecia, nie o nazwe pola).

**Co mierzy:** średni błąd predykcji PODCZAS prezentacji bodźca (tick<100,
L1.1) — jak dobrze Brain trafia bieżący sygnał, gdy wciąż go widzi.
**Czego NIE mierzy:** rozpoznawania NOWEGO wzorca — ten sam, powtarzalny
sygnał przez cały przebieg; brak testu transferu na inny wzorzec w ramach
jednego runu.

**Kiedy zdegenerowana (P3):** GENOME-ROBUST 100% w `noise_world` i
`drift_world` (23/23). Zdegenerowana (0%) w `stable_world` — oczekiwane,
środowisko deterministyczne, `n_effective=1` dla każdego genomu z definicji.

**Kiedy myląca (P3, na etapie n=10 — zapis historyczny):** mimo 100%
ROBUST, **0/253 par genomów przeżywało FDR w obu środowiskach na n=10.**
**AKTUALIZACJA 2026-07-21 (KOREKTA — pierwsza wersja tej adnotacji błędnie
twierdziła, że 0/253 utrzymuje się też na n=185; audytor zweryfikował
surowy plik i to nieprawda):** na n=185 konfirmacyjnym metryka
dyskryminuje TAKŻE parowo — **77/253 par (30%) przeżywa FDR**
(`pairwise_comparisons.n_fdr_significant_q_0_05` w
`population_validation_v0_11_0.json`, zweryfikowane niezależnym przeliczem
BH-FDR) — plus test omnibusowy (Kruskal-Wallis, p=4.5e-14). Oba testy się
zgadzają — status VALIDATED, `docs/METRIC_STATUS_TABLE.md` footnote¹⁰ i ¹⁵.

**Kiedy wymaga innej interpretacji:** wysoki `valid_rate` w raporcie
populacyjnym NIE jest dowodem, że genomy różnią się w Pattern Recognition —
sprawdź zawsze `pairwise_comparisons.n_fdr_significant_q_0_05`, nie tylko
`classification`.

---

## Pattern Retention (`memory_decay_rate`)

**Formalna definicja (P1):**
```
memory_decay_rate = (mae_silence_phase - mae_stimulus_phase) / silence_ticks
```
(SPRINT_v0.11.0.md P1: pola przemianowane z `mse_*` na `mae_*`, patrz
Pattern Recognition powyżej — formuła i wartości bez zmian) gdzie
`mae_silence_phase`/`mae_stimulus_phase` sa srednimi bledami
bezwzglednymi (patrz Pattern Recognition powyzej) po odpowiednio CALEJ
fazie ciszy i CALEJ fazie stymulacji (nie tylko od ticku 50, w
przeciwienstwie do Working Memory ponizej). Warunek brzegowy:
`silence_ticks=0` -> wynik 0 (dzielenie przez zero unikniete cichym
zerem, nie wyjatkiem - patrz P2).

**NAZWA vs POMIAR (P1): ZNAK MOZE BYC UJEMNY, WBREW NAZWIE "decay" (rozpad).**
Jesli `mae_silence_phase < mae_stimulus_phase` (siec radzi sobie LEPIEJ w
ciszy niz podczas stymulacji - mozliwe np. gdy szum stymulacji utrudnia
predykcje bardziej niz jego brak), `memory_decay_rate` wychodzi UJEMNE -
"ujemny rozpad" jest pojeciowo niespojne z nazwa (rozpad z definicji nie
powinien byc ujemny). Dodatkowo: to jest RÓŻNICA MIĘDZY DWOMA ŚREDNIMI
podzielona przez czas, nie dopasowana krzywa zaniku - zaklada IMPLICITE
model LINIOWY (stala szybkosc pogarszania), nie eksponencjalny/nasycajacy
się, ktory bylby biologicznie bardziej prawdopodobny.

**Co mierzy:** tempo pogarszania się trafności predykcji w fazie ciszy L1.1.
**Czego NIE mierzy:** retencji w sensie długoterminowym (poza jednym
przebiegiem 200 ticków); nie rozróżnia zapominania od braku uczenia się od
początku.

**Kiedy zdegenerowana (P3):** identycznie jak Pattern Recognition —
GENOME-ROBUST 100% w `noise_world`/`drift_world`, zdegenerowana w
`stable_world` (oczekiwane).

**Kiedy myląca (P3):** **0/253 par przeżywa FDR w obu środowiskach (na
teście PAROWYM — jedyna z trzech osi, dla której liczba ta POZOSTAJE
0/253 również na n=185 konfirmacyjny; potwierdzone niezależnie —
`pairwise_comparisons.n_fdr_significant_q_0_05`=0 w
`population_validation_v0_11_0.json` + przelicz BH-FDR, patrz AKTUALIZACJA
2026-07-21 na początku dokumentu).** W odróżnieniu od Pattern Recognition
(77/253) i Working Memory (69/253), które na n=185 zaczęły dyskryminować
TAKŻE parowo, Pattern Retention pozostaje 0/253 parowo — sygnał widoczny
wyłącznie w teście omnibusowym (Kruskal-Wallis, n=185, p=0.0254,
niemonotoniczny efekt, Red Team) — status EXPERIMENTAL,
`docs/METRIC_STATUS_TABLE.md` footnote¹¹, NIE VALIDATED (efekt słabszy i
wykrywalny tylko jednym z dwóch testów, w odróżnieniu od WM/Pattern
Recognition gdzie zgadzają się oba).

**Kiedy wymaga innej interpretacji:** jak wyżej — `GENOME-ROBUST` czytać
jako "infrastruktura działa", nie jako "genomy się różnią".

---

## Working Memory (`mae_vs_pattern_after_stimulus_removal`, dawniej `mse_vs_pattern_after_stimulus_removal`, primary endpoint L1.1)

**NAPRAWIONE (SPRINT_v0.11.0.md P1, 2026-07-15):** to jest FLAGOWY endpoint
projektu — patrz `docs/MSE_MAE_NAMING_DECISION.md` dla pełnego zasięgu
zmiany. Wartości (0.156712/0.173229) i formuła bez zmian.

**Formalna definicja (P1):**
```
silence_after_50 = {t : phase(t)="silence", t >= stimulus_ticks + 50}     (POMIJA pierwsze 50 tickow ciszy)
mae_at_tick_50    = mean_{t in silence_after_50, t mod 5 = 0} |prediction(t) - pattern_signal(t)|
PASS              <=> mae_at_tick_50 < 0.5
```
Warunek brzegowy: jesli `silence_after_50` puste (np. `silence_ticks<50`),
wynik = **1.0** (nie 0, nie wyjatek - domyslna wartosc "najgorsza mozliwa",
ukryta w kodzie, nie w prerejestracji explicite jako "co jesli za krotka
faza ciszy"). **To osobny, NIENAPRAWIONY problem** ("cisza gorsza niz blad",
zasada nadrzedna 1 tego sprintu) — poza zakresem tej korekty nazwy, patrz
tabela P3 (Working Memory, kolumna Construct, przypis ¹).

**NAZWA vs POMIAR: dlaczego "po tick 50", nie od razu po usunieciu bodzca
(tick 100)?** Offset 50 ticków PRZED rozpoczęciem pomiaru zakłada, że
efekty przejściowe usunięcia bodźca (np. chwilowy skok błędu przy pierwszej
próbie predykcji bez sygnału) ustępują w tym czasie — to jest ZAŁOŻENIE
PROJEKTOWE (uzasadnione w `preregistration_L1_1.json`), nie zmierzony fakt;
gdyby prawdziwy czas ustępowania przejścia był inny niż 50 ticków, endpoint
mierzyłby częściowo efekt przejściowy, nie ustabilizowaną pamięć. Metryka
używa też `abs()`, nie kwadratu — dawniej ukryte pod `mse_` w nazwie,
**NAPRAWIONE** (patrz Pattern Recognition powyżej — ten sam błąd
nazewnictwa, ta sama korekta).

**Co mierzy:** zdolność odtworzenia wzorca z pamięci PO usunięciu bodźca
(tick≥150, bufor sensoryczny zamrożony przez `silent_step()`).
**Czego NIE mierzy:** working memory w sensie wieloelementowym/pojemnościowym
— jeden, ciągły sygnał, nie zestaw dyskretnych elementów do przechowania.

**Kiedy zdegenerowana (P3):** GENOME-ROBUST 100% w `noise_world` i
`drift_world`; zdegenerowana (0%) w `stable_world` (oczekiwane, kontrola).

**Kiedy myląca — NAJWAŻNIEJSZY WYNIK P4 (patrz "Kluczowe odkrycie"
powyżej):** primary endpoint całej lekcji L1.1 jest wiarygodnie mierzalny
dla każdego zbadanego genomu, ale **ŻADNA z 253 par genomów w żadnym z 2
środowisk nie różni się istotnie po korekcie FDR.** `competency_profile.md`
(v0.9/v0.10, 2 genomy) raportuje Cohen's d=0.327 między `default` i
`highly_plastic` — liczba ta pozostaje poprawnie policzona, ale **na 23
genomach nie ma dowodu, że jakakolwiek para (w tym prawdopodobnie ta)
różni się od siebie bardziej niż losowy szum przy tylu porównaniach.**

**Kiedy wymaga innej interpretacji:** raportując Working Memory jako
"zróżnicowaną między genomami" na podstawie tylko 2 genomów (jak robił to
`competency_profile.md` przed tym sprintem) — nie robić tego bez zastrzeżenia
o wielkości próby. Sam pomiar primary endpoint pozostaje wiarygodny (to nie
jest błąd infrastruktury) — wiarygodne jest tylko TWIERDZENIE O RÓŻNICY
MIĘDZY GENOMAMI, które wymaga populacji, nie dwóch punktów.

---

## Long-term Memory

**Formalna definicja (P1):** nie dotyczy — brak mechanizmu do
sformalizowania (jedna, jednolita struktura pamięci w `BrainTissue`, zero
rozróżnienia czasowego).

**Co mierzy:** nic — `not yet measured`, brak mechanizmu odróżniającego
pamięć długoterminową od roboczej w `BrainTissue`.
**Czego NIE mierzy / kiedy zdegenerowana / myląca:** nie dotyczy.
**Kiedy wymaga innej interpretacji:** jak Perception/Attention.

---

## Prediction

**Formalna definicja (P1):** nie dotyczy jako osobny endpoint —
`last_prediction` jest SKLADNIKIEM formul innych metryk (Pattern
Recognition, Working Memory), nigdy testowanym samodzielnie jako
predykcja "w przod" (przyszlego, jeszcze niewystapionego bodzca).

**Co mierzy:** nic jako osobny endpoint — `last_prediction` jest składnikiem
KAŻDEJ metryki MSE w L1.1, ale predykcja "w przód" (bodziec jeszcze
niewystąpiony) nie jest testowana jako osobna hipoteza.
**Kiedy wymaga innej interpretacji:** nie mylić z Working Memory/Pattern
Recognition — te używają predykcji jako narzędzia, nie testują jej wprost.

---

## Adaptation (`adaptation_tick`)

**Formalna definicja (P1):**
```
adaptation_tick = min{ t : t>=10, std(entropy[t : t+10]) < 0.02 }             (pierwsze okno 10 tickow, rolling std<0.02)
                  ELSE (jesli zaden taki t) = pierwszy t>=len/4 gdzie entropy(t) < 0.8*max(entropy[:len/2])  (fallback)
                  ELSE (jesli len(snapshots) < 20) = 0                        (degeneracja strukturalna, patrz P3/robustness)
```
`entropy` = trajektoria snapshotow (Read-Only Observer, v0.10). Snapshoty
indeksowane od tick=0 W CALYM przebiegu (nie od jakiegokolwiek zdarzenia -
"start szukania" to poczatek CALEGO runu, nie poczatek "nowego rezimu" jak
sugerowalaby nazwa "Adaptation").

**Domena zastosowania - UKRYTE ZALOZENIE:** formula zaklada, ze entropia
jest NIESTABILNA na poczatku przebiegu i STABILIZUJE SIE w pewnym momencie.
Jesli entropia jest stabilna OD SAMEGO POCZATKU (np. genom z wysokim
`decay_rate`, gdzie rozpad pamieci dominuje nad szumem srodowiska - patrz
`RAPORT_v0.10.md`), formula wykrywa to jako "koniec chaosu" natychmiast
(najwczesniejszy mozliwy `t=10`) - NIE dlatego, ze system "szybko sie
zaadaptowal", tylko dlatego, ze NIGDY NIE BYL w stanie chaosu do adaptacji.
Formula nie odroznia tych dwoch sytuacji.

**Co mierzy:** tick, w którym `_find_chaos_end()` wykrywa koniec
POCZĄTKOWEJ niestabilności entropii (rolling std<0.02 w oknie 10 ticków) —
patrz poprawiony opis w `cognitive_ontology.md` (poprzednia wersja błędnie
wskazywała `_find_adaptation_end()`).

**Czego NIE mierzy — WAŻNE, dwie odrębne pułapki:**

1. **L1.2 (v0.10 P2/P4):** `adaptation_tick` w L1.2 mierzy stabilizację
   entropii w oknie **PRZED szokiem** (bo `t_shock≥20` zawsze, a detektor
   sprawdza pierwsze okno od `tick=10`), NIE adaptację DO szoku. To NIE jest
   ta sama wielkość co L1.2's nazwa sugeruje.
2. **L1.1, NOWE Z P3:** ten sam mechanizm degeneracji (przedwczesne
   wykrycie "końca chaosu") dotyka też L1.1, na **35-43% zbadanej
   populacji genomów** (nie tylko na 2 anchorach z v0.10, gdzie
   przypadkiem oba miały niski `decay_rate` i wyszły niezdegenerowane).

**Kiedy zdegenerowana — PREREJESTROWANY WYNIK (P3, klasyfikacja wg progu
z `preregistration_v0_10_1_population.json`, zaplanowana przed uruchomieniem):**

| Środowisko (L1.1) | valid_rate |
|---|---|
| noise_world | 34.78% (8/23) |
| drift_world | 43.48% (10/23) |
| stable_world | 0% (oczekiwane, kontrola) |

> **UWAGA METODOLOGICZNA — poniższy akapit to ODKRYCIE POST-HOC/EKSPLORACYJNE,
> NIE prerejestrowany wynik.** Prerejestracja P1 deklarowała populację, próg
> ważności (`n_effective≥5`), próg GENOME-ROBUST (80%) i korektę FDR — NIE
> deklarowała szukania progu `decay_rate`. Wzorzec opisany niżej został
> zauważony PO zobaczeniu wyników (ten sam zestaw danych, na którym go
> dostrzeżono), więc nie ma statusu potwierdzonego ustalenia — to **HIPOTEZA
> do przyszłego testu**, nie wynik.

Zdegenerowane genomy (mean≈10, `n_effective`≤4) mają w TEJ próbce
`decay_rate` > ~0.035 bez wyjątku; ważne genomy (real variance, mean 14-42)
mają w TEJ próbce `decay_rate` < ~0.029 bez wyjątku. `highly_plastic`
(decay_rate=0.05) wpada w grupę zdegenerowaną — w v0.10 (próg
`n_effective≥2`) wyglądał na "ważny" (`n_effective=3`), ale przy
ostrzejszym progu populacyjnym (`n_effective≥5`, ten sam co
`MIN_NON_CENSORED` z L1.2) już nie przechodzi (TO zdanie — przeklasyfikowanie
`highly_plastic` progiem `n_effective≥5` — jest odtwarzalne z już
zaraportowanych liczb, nie jest post-hoc w tym samym sensie).

**Próg `decay_rate≈0.035` jest przybliżony, wyprowadzony z 23 punktów, i
NIE został przetestowany na niezależnej próbce** — żeby stać się
ustaleniem (nie tylko obserwacją), wymagałby osobnej prerejestracji
deklarującej dokładny próg PRZED uruchomieniem nowych seedów/genomów po
obu jego stronach, i weryfikacji, że próg trzyma się na danych, których
nie użyto do jego wyprowadzenia. Bez tego kroku próg 0.035 pozostaje
**opisem tej konkretnej próbki 23 genomów, nie prawem ogólnym.**

**Hipoteza robocza (nie udowodniona przyczynowo, tylko korelacja
zaobserwowana post-hoc w tych danych):** wysoki `decay_rate` mógłby
powodować, że dynamika entropii jest zdominowana przez sam rozpad pamięci,
a nie przez seed-zależny sygnał świata — rolling std spadałby poniżej
progu 0.02 szybko i deterministycznie, niezależnie od konkretnego
przebiegu szumu. To wyjaśnienie mechanistyczne jest wiarygodne, ale
**nieprzetestowane niezależnie** — traktować jako kierunek do
prerejestrowanego badania, nie jako wyjaśnienie zamknięte.

W L1.2 (patrz `cognitive_ontology.md` §Adaptation(d)): **0% na wszystkich
23 genomach, we WSZYSTKICH środowiskach** — to nie jest kwestia progu
`decay_rate`, to strukturalny efekt okna detekcji zawsze wypadającego przed
szokiem, niezależnie od genomu.

**Kiedy myląca:** gdy `adaptation_tick` WYGLĄDA na zmierzony (liczba w
raporcie) dla genomu z wysokim `decay_rate` w L1.1 — ta liczba (`~10`) nie
niesie żadnej informacji o adaptacji, to artefakt progu detekcji.

**Kiedy wymaga innej interpretacji:** przy porównywaniu Adaptation między
genomami warto sprawdzić `decay_rate` tych konkretnych genomów najpierw —
w TEJ próbce `decay_rate>0.03` koreluje z degeneracją — ale to podpowiedź
z hipotezy post-hoc, nie zweryfikowana reguła; nie traktować jako
gwarancji bez niezależnego testu. Pary genomów, którym udaje się przejść
próg walidacji (mniejszość), WYKAZUJĄ silną, FDR-odporną różnicę (24/28 par
w noise_world, 37/45 w drift_world, wynik prerejestrowany) — gdy Adaptation
nie jest zdegenerowana, jest bardzo dyskryminująca, nie słabo.

---

## Exploration

**Formalna definicja (P1):** nie dotyczy — `act()` nie ma zadnego
mechanizmu wyboru (czysty `return brain.last_input`), zero zmiennej do
sformalizowania.

**Co mierzy:** nic — `not yet measured`, `act()` to czyste echo bodźca, brak
mechanizmu wyboru działania.
**Kiedy wymaga innej interpretacji:** jak Perception.

---

## Generalization

**Formalna definicja (P1):** nie dotyczy — zaden endpoint nie porownuje
wyniku treningu na scenariuszu A z testem na scenariuszu B w ramach
JEDNEGO przebiegu (co odroznialoby to od Adaptation/Stability, gdzie
rozne srodowiska sa PORÓWNYWANE MIĘDZY SOBĄ, ale kazde osobno, nie jako
transfer).

**Co mierzy:** nic — `not yet measured`, brak lekcji trenującej na jednym
scenariuszu i testującej na innym w ramach tego samego przebiegu.
**Uwaga metodologiczna z P2/P3:** populacja BYŁA uruchamiana na 3
środowiskach (`noise_world`/`shock_world`, `stable_world`, `drift_world`),
ale to NIE jest test generalizacji w sensie tego pojęcia — każdy przebieg
jest treningiem i testem na TYM SAMYM środowisku, nie transferem.

---

## Planning

**Formalna definicja (P1):** nie dotyczy — `act()` dziala na pojedynczym
ticku, brak jakiegokolwiek stanu reprezentujacego sekwencje/horyzont do
sformalizowania.

**Co mierzy:** nic — `not yet measured`, `act()` nie ma pojęcia sekwencji
ani horyzontu czasowego.
**Kiedy wymaga innej interpretacji:** jak Perception.

---

## Stability (`stability_score`)

**Formalna definicja (P1):**
```
error(t)        = |1 - energy(t)|                              (PROXY - snapshoty nie maja bezposredniego bledu predykcji)
stability_score = 1 / ( std(entropy[0:T]) + std(error[0:T]) + 1e-6 )     (T = caly przebieg, wszystkie snapshoty)
```

**UKRYTE ZALOZENIE - PROXY, NIE PRAWDZIWY BLAD:** `error(t)=|1-energy(t)|`
NIE jest bledem predykcji (ktorego snapshoty nie przechowuja) - to jest
ZASTEPCZA wielkosc, zakladajaca ze "energia daleko od 1.0" koreluje z
"bledem daleko od 0". Ta relacja NIE jest formalnie wyprowadzona z
`regulate()` (Core) - jest przyjeta jako rozsadne przyblizenie. Jesli
energia i faktyczny blad predykcji rozjezdzaja sie w jakims reżimie
genomu/srodowiska, `stability_score` mierzy stabilnosc ENERGII, nie
stabilnosc SYSTEMU POZNAWCZEGO w potocznym sensie tej nazwy.

**NIELINIOWOSC (odwrotnosc) - male zmiany std dają duze zmiany SI blisko
zera:** przy `std_total` idacym do 0, `SI` idzie do 1e6 (nie do
nieskonczonosci, dzieki stalej 1e-6 w mianowniku, ale i tak bardzo duze
liczby) - std=0.01 daje SI≈99, std=0.02 daje SI≈49 - **SI NIE jest skala
liniowa "ile razy stabilniejszy"**, tylko odwrotnoscia, co matematycznie
tlumaczy czesc duzych Cohen's d (patrz nizej).

**Co mierzy:** `1/(std(entropy)+std(error)+1e-6)` na snapshotach całego
przebiegu — odporność stanu wewnętrznego na fluktuacje.
**Czego NIE mierzy:** stabilności WZGLĘDEM zadania (dwa genomy mogą mieć
identyczny `stability_score` przy zupełnie różnej jakości predykcji).

**Kiedy zdegenerowana (P3):** TYLKO w `stable_world` (0%, oczekiwane -
kontrola deterministyczna). We WSZYSTKICH pozostałych kontekstach
(L1.1×noise_world, L1.1×drift_world, L1.2×shock_world, L1.2×drift_world):
**100% GENOME-ROBUST.** Najbardziej niezawodnie mierzalna z 7 zmierzonych
osi.

**Kiedy myląca — UWAGA na Cohen's d (v0.10 §6c, potwierdzone i wzmocnione
przez P3):** Stability ma bardzo małą wariancję wewnątrzgenomową (std rzędu
0.03-0.1 na wartości ~2-3) — stąd duże Cohen's d w `competency_profile.md`
(9.46) świadczy o **precyzji pomiaru, nie o wielkości efektu w sensie
praktycznym.** P3 potwierdza to na dużą skalę: Stability jest jednocześnie
NAJBARDZIEJ dyskryminującą osią (82-92% par genomów istotnie różnych po
FDR, we wszystkich zbadanych nie-kontrolnych środowiskach) I ma najmniejszą
wariancję resztową spośród 7 zmierzonych osi — te dwa fakty razem
(duża liczba istotnych par + mała wariancja) oznaczają, że wiele z tych
"istotnych" różnic to prawdopodobnie **realne, ale ilościowo drobne**
różnice, wykryte tylko dzięki wyjątkowej precyzji pomiaru, nie dlatego że
genomy dramatycznie się różnią.

**Kiedy wymaga innej interpretacji:** L1.1 i L1.2 liczą Stability tą samą
funkcją, ale NIE są łączone w jedną pulę CI95 (`cognitive_ontology.md`
§Stability(d)) — różne konteksty zadaniowe, decyzja świadomie odłożona.

---

## Final Energy Level (`final_energy`, dawniej "Energy Efficiency")

> **NAPRAWIONE (SPRINT_v0.11.0.md P1, decyzja CTO 2026-07-17, Opcja 1):**
> pojęcie przemianowane z "Energy Efficiency" na "Final Energy Level" —
> `final_energy` i wartości (0.460800 default / 0.413800 highly_plastic) bez
> zmian. To był błąd KATEGORII (efektywność=stosunek, `final_energy`=poziom
> punktowy), nie błąd nazwy w kategorii operacji matematycznej jak MSE/MAE —
> nie da się go naprawić samym rename bez ryzyka nowego błędu, patrz niżej
> "dlaczego nie 'Metabolic Cost'". **Ta oś jest teraz jawnie oznaczona jako
> ZMIENNA STANU FIZJOLOGICZNEGO, NIE zdolność poznawcza** — patrz
> "Podsumowanie" na końcu dokumentu i
> `clos_scientist/capability_analyzer.py:CONCEPT_KIND`. Pełne uzasadnienie
> trzech rozważanych opcji: `docs/ENERGY_EFFICIENCY_ONTOLOGY_DECISION.md`.

**Dlaczego "Final Energy Level", nie "Metabolic Cost":** audytor zgłosił
zastrzeżenie zapisane tu wprost, żeby nikt za rok nie "poprawił" nazwy z
powrotem. `final_energy` mierzy ile energii ZOSTAŁO, nie ile wydano —
`default=0.4608` (więcej zostało) vs `highly_plastic=0.4138` (mniej
zostało) oznacza, że `default` miał NIŻSZY koszt metaboliczny mimo WYŻSZEJ
wartości pola. Metryka nazwana "Metabolic Cost" byłaby odwrotnie
skorelowana z rzeczywistym kosztem — dokładnie ten sam rodzaj błędu, który
naprawiliśmy dzisiaj w MSE/MAE. Poprawny "Metabolic Cost" wymagałby
`initial_energy - final_energy`, co ZMIENIA WARTOŚĆ liczbową i łamie
zasadę "korekta nazwy, nie pomiaru" — nie zostało zrobione.

**Formalna definicja (P1):**
```
final_energy = tissue.energy @ tick = ostatni_tick_przebiegu     (JEDEN PUNKT W CZASIE, nie srednia/calka)
```
Zero uśredniania, zero okna czasowego - to jest **pojedyncza wartość
punktowa** odczytana na końcu (tick=199 dla L1.1, tick=299 dla L1.2).

**NAZWA vs POMIAR (ODKRYCIE, NAPRAWIONE): BYŁA NAJWIEKSZĄ NIEZGODNOŚCIĄ ze
wszystkich 7 zmierzonych osi.** "Efficiency" (wydajnosc/efektywnosc) z
definicji jest STOSUNKIEM (output/koszt, korzysc/naklad) - metryka nie jest
stosunkiem, jest surowym POZIOMEM energii w jednym punkcie czasu. Genom,
ktory zuzywa duzo energii, ale osiaga swietne wyniki poznawcze, i genom,
ktory zuzywa malo energii, ale nie robi nic uzytecznego, MOGA miec
identyczny `final_energy` - "Efficiency" w nazwie obiecywał rozroznienie,
ktorego metryka NIE dostarczała. **Naprawione:** nazwa "Final Energy Level"
opisuje dosłownie to, co jest mierzone, zero interpretacji kierunku.

**Co mierzy:** poziom energii `BrainTissue.energy` na koniec przebiegu.
**Czego NIE mierzy:** efektywności koszt/korzyść względem zadania — nie ma
znormalizowanego wskaźnika (np. energia na jednostkę poprawnie odtworzonego
wzorca); mierzymy ZUŻYCIE, nie WYDAJNOŚĆ.

**Kiedy zdegenerowana — PREREJESTROWANY WYNIK (klasyfikacja wg progu z
prerejestracji, zaplanowana przed uruchomieniem):**

| Kontekst | valid_rate |
|---|---|
| L1.1×noise_world | 39.13% (9/23) |
| L1.1×drift_world | 78.26% (18/23) |
| L1.2×shock_world | 100% (23/23) — ROBUST |
| L1.2×drift_world | 73.91% (17/23) |
| oba×stable_world | 0% (oczekiwane) |

> **UWAGA METODOLOGICZNA — poniższe wyjaśnienie mechanizmu to ODKRYCIE
> POST-HOC/EKSPLORACYJNE, NIE prerejestrowany wynik**, z dokładnie tego
> samego powodu co przy Adaptation powyżej: korelacja z `decay_rate` została
> zauważona po zobaczeniu wyników FRAGILE, na tych samych 23 genomach, nie
> była częścią planu z P1. To **HIPOTEZA**, nie ustalenie.

Zaobserwowany (nie potwierdzony niezależnie) wzorzec: genomy z wyższym
`decay_rate` (w tej próbce: >~0.04-0.05 w L1.1) klastrują się przy
`n_effective` 3-4 (poniżej progu 5), genomy z niższym `decay_rate` przy
`n_effective` 5-9 — ten sam kierunek co przy Adaptation, sugerujący wspólny
mechanizm, ale osobno nieprzetestowany. Możliwa interpretacja: wysoki
rozpad pamięci mógłby prowadzić system do podobnego, mało-zróżnicowanego
seedowo stanu energetycznego na końcu przebiegu — **wymaga tego samego
kroku weryfikacji na niezależnej próbce co próg Adaptation, żeby przejść
od obserwacji do ustalenia.**

**Kontrast L1.2×shock_world (100% ROBUST) vs L1.1 (FRAGILE) na tych samych
genomach jest sam w sobie PREREJESTROWANYM wynikiem** (obie klasyfikacje
wynikają wprost z zaplanowanego progu 80%, żadna nie wymagała szukania
progu post-hoc) — ale WYJAŚNIENIE tego kontrastu (szok wprowadza dodatkowe
źródło międzyseedowej wariancji energii przez `random.Random(seed)`, które
maskuje efekt wygładzający wysokiego `decay_rate` widoczny w L1.1) jest
**również hipotezą post-hoc**, nieprzetestowaną niezależnie od tych samych
23 genomów.

**Kiedy myląca:** identycznie jak Adaptation — niska `n_effective` przy
wysokim `decay_rate` nie jest błędem infrastruktury, jest realną
konsekwencją dynamiki, ale sprawia, że liczba w raporcie nie niesie
informacji różnicującej genomy w tym reżimie.

**Kiedy wymaga innej interpretacji:** Final Energy Level jest kontekstowo
zmienna (ROBUST w szoku, FRAGILE bez szoku) bardziej niż jakakolwiek inna
zmierzona oś — nie zakładać stałej wiarygodności między środowiskami. Poza
tym: to zmienna stanu fizjologicznego, nie zdolność poznawcza (patrz wyżej)
— "kontekstowo zmienna wiarygodność pomiaru" NIE implikuje "kontekstowo
zmienna kompetencja poznawcza".

---

## Homeostatic Resilience (`recovery_time` / `time_to_sustained_band`)

**Formalna definicja (P1) — JUZ ISTNIEJE w pelnej formie w
`publications/preregistration_L1_2.json` (`recovery_time_definition`), NIE
duplikowana tutaj w calosci - skrot:**
```
B          = [0.5*homeostasis_target, homeostasis_target]                (pasmo homeostazy)
t*         = min{ tau >= t_shock : entropy(s) in B, dla wszystkich s w [tau, tau+N-1] }   (N=10)
recovery_time (a.k.a. time_to_sustained_band) = t* - t_shock, szukane w tau w [t_shock, t_shock+W-N]  (W=150)
censored   = TRUE, jesli zaden takie t* nie istnieje w oknie -> recovery_time=None
```
Nazwa `recovery_time` w kodzie POZOSTAJE, mimo ze §(c) nizej (i
`cognitive_ontology.md`) stwierdza, ze faktyczny znaczony fenomen to
USTANOWIENIE, nie POWROT (rozstrzygniete z danych, `pre_shock_in_band_fraction`
< progu 0.8) — jawny przyklad "nazwa nie zostala zmieniona po tym, jak dane
pokazaly, ze mierzy inne zjawisko niz zalozono", zachowany celowo dla
ciaglosci artefaktow (patrz `preregistration_L1_2.json` dla pelnego
uzasadnienia rewizji).

**Co mierzy:** liczbę ticków od `t_shock` do pierwszego okna N=10 ticków w
paśmie homeostazy — patrz `cognitive_ontology.md` dla pełnej definicji
dwuznaczności recovery/establishment.

**Czego NIE mierzy (v0.9, historia — bez zmian, ale teraz z populacyjnym
potwierdzeniem):** NIE mierzy "powrotu" (recovery) w tej lekcji —
`pre_shock_in_band_fraction=0.0` dla obu oryginalnych genomów oznacza, że
mierzony jest przypadek **ustanowienia** (`time_to_sustained_band`), nie
odzyskania. Nazwa `recovery_time` w kodzie jest METODOLOGICZNIE MYLĄCA z
tego właśnie powodu — świadomie zachowana (zmiana złamałaby ciągłość
artefaktów), ale interpretacja musi używać `time_to_sustained_band`.

**Kiedy zdegenerowana (P3, NOWE - populacja potwierdza, że to NIE wyjątek):**
valid_rate = **21.74% (5/23)** w `shock_world` — reszta populacji jest w
różnym stopniu ucenzurowana (`recovery_time=None`, brak powrotu w oknie
W=150). W v0.10 (2 genomy) `highly_plastic` 100% ucenzurowany wyglądał jak
pojedynczy, dobrze wytłumaczony wyjątek (wysoki `decay_rate` → 5× silniejszy
przyrost entropii). **P3 pokazuje, że to nie wyjątek — to WIĘKSZOŚĆ
przestrzeni parametrów** (18/23 genomów nie osiąga wystarczającej liczby
nieucenzurowanych obserwacji).

**Historia — DWA UKRYTE OGRANICZENIA DZIEDZINY, ODKRYTE w P2/P3, NAPRAWIONE
w SPRINT_v0.11.0.md P2 (kod zmieniony, populacja v0.10.1 poniżej NIE
przeliczona — patrz zastrzeżenie na końcu):**

1. **Name-gate (NAPRAWIONE).** Do SPRINT_v0.11.0.md P2, `run_shock_recovery()`
   liczył `t_shock`/`primary_endpoint`/`pre_shock_in_band` WYŁĄCZNIE gdy
   `scenario == "shock_world"` dosłownie — NIE gdy scenariusz był semantycznie
   "szokowy". P3 (v0.10.1) potwierdził to empirycznie: Homeostatic Resilience
   był **`not_applicable`** nawet w scenariuszach z realną, pojedynczą
   perturbacją (`weak_shock_world`, `long_stable_shock_world`), tylko dlatego,
   że nazwa się nie zgadzała. **Teraz:** `lesson_L1_2.py` używa
   `clos_world.scenarios.has_single_perturbation(scenario)` — WŁAŚCIWOŚCI
   scenariusza (rejestr `SINGLE_PERTURBATION_SCENARIOS`), nie jego nazwy.
   `weak_shock_world`/`long_stable_shock_world` liczą teraz endpoint;
   `recurring_shock_world` nadal go nie dostaje, ale świadomie — ma
   WIELOKROTNE perturbacje, nie pasuje do modelu "jeden `t_shock`" (prawdziwy
   brak zastosowania konstruktu, nie name-gate). Regresja: `shock_world`
   (0.156712/0.173229/15.4) bez zmian — `tests/test_genome_params_regression.py`
   zielony.
2. **Granica t_shock (SKORYGOWANA I EGZEKWOWANA).** `compute_recovery_time()`
   czyta `entropy_by_tick` aż do indeksu `t_shock+W-1` (nie tylko do
   `deadline=t_shock+W-N`, jak poprzednia wersja tego dokumentu błędnie
   zakładała) — poprawny warunek to `t_shock ≤ ticks_total-W` = **150**, nie
   159 jak poprzednio udokumentowano (pomyłka o `N-1=9`, sama nigdy nie
   ujawniona bo żaden zarejestrowany scenariusz jej nie przekraczał).
   Naruszenie tego warunku (lub `t_shock<N` dla `pre_shock_in_band`) podnosi
   teraz jawnie `RecoveryWindowOutOfDomainError` (metryka/scenariusz/warunek/
   powód) zamiast cichego pominięcia lub niejasnego `KeyError` — zasada
   nadrzędna 1 tego sprintu. `long_stable_shock_world` (`t_shock∈[100,150]`)
   zostaje dokładnie na tej granicy, nigdy jej nie przekracza.

**Zastrzeżenie o danych poniżej:** naprawa dotyczy WYŁĄCZNIE mechanizmu
pomiaru w kodzie. Artefakt `reports/population/population_validation_v0_10_1.json`
(P3, poniższe liczby) nadal obejmuje TYLKO `shock_world`/`stable_world`/
`drift_world` (`LESSON_ENVIRONMENTS["L1.2"]` w `population_validation.py` nie
zmienione) — `weak_shock_world`/`long_stable_shock_world` NIE mają populacyjnej
walidacji Homeostatic Resilience, ta naprawa umożliwia ją dopiero w
przyszłości. Liczby poniżej (`valid_rate=21.74%` itd.) są więc dokładnie te
same, sprzed i po tej naprawie.

**Kiedy wymaga innej interpretacji:** interpretując Homeostatic Resilience
dla NOWEGO genomu/środowiska, sprawdzić: (a) czy
`clos_world.scenarios.has_single_perturbation(scenario)` (nie: czy nazwa to
dosłownie `"shock_world"`), (b) jaki jest `decay_rate` tego genomu (silny
predyktor cenzurowania, patrz P3), (c) czy `t_shock` mógłby przekroczyć 150
dla `ticks_total=300` (teraz: jeśli tak, dostaniesz jawny wyjątek, nie cichy
błąd).

---

## Podsumowanie: 6 osi poznawczych + 1 zmienna stanu fizjologicznego

> **SPRINT_v0.11.0.md P1 (decyzja CTO 2026-07-17):** z 7 wierszy poniżej,
> **6 to osie poznawcze** (zmierzone zdolności lub kandydaci na nie —
> Pattern Recognition, Pattern Retention, Working Memory, Stability,
> Adaptation, Homeostatic Resilience) i **1 to zmienna stanu
> fizjologicznego** (Final Energy Level, dawniej "Energy Efficiency") — NIE
> zdolność poznawcza, mierzy stan systemu, nie jego kompetencję. Ta sama
> tabela je grupuje, bo obie kategorie przechodzą przez ten sam pipeline
> pomiaru (Measurement/Construct/Power/Confirmatory) — rozróżnienie
> kategorii jest dodatkowe, nie zastępuje tabeli. Pełne uzasadnienie:
> `docs/ENERGY_EFFICIENCY_ONTOLOGY_DECISION.md`;
> `publications/competency_profile.json` niesie to samo rozróżnienie jawnie
> w polu `minimal_profile.cognitive_axes` vs
> `minimal_profile.physiological_state_variables`.

| Oś | Kategoria | ROBUST wszędzie poza kontrolą? | Dyskryminuje po FDR (test parowy, n=10)? | Główny mechanizm ograniczenia |
|---|---|---|---|---|
| Pattern Recognition | poznawcza | Tak (2/2 środ.) | **Nie, na n=10** (0/253 w obu)¹ | — (na n=10; na n=185 dyskryminuje, patrz¹) |
| Pattern Retention | poznawcza | Tak (2/2 środ.) | **Nie** (0/253 w obu)¹ | — (0/253 parowo pozostaje prawdziwe też na n=185, patrz¹) |
| Working Memory | poznawcza | Tak (2/2 środ.) | **Nie, na n=10** (0/253 w obu)¹ | — (na n=10; na n=185 dyskryminuje, patrz "Kluczowe odkrycie" i¹) |
| Stability | poznawcza | Tak (4/4 środ. nie-kontrolnych) | **Tak, silnie** (82-92%) | mała wariancja resztowa → duże Cohen's d, ostrożna interpretacja |
| Adaptation | poznawcza | **Nie** (35-43% w L1.1, 0% w L1.2) | Tak, gdy mierzalna | *hipoteza post-hoc, niepotwierdzona:* wysoki `decay_rate` → przedwczesna detekcja końca chaosu |
| Final Energy Level | **stan fizjologiczny** | **Częściowo** (39-100% zależnie od kontekstu) | Tak, gdy mierzalna | *hipoteza post-hoc, niepotwierdzona:* wysoki `decay_rate` → spłaszczenie energii między seedami |
| Homeostatic Resilience | poznawcza | **Nie** (22% w shock_world, n/a gdzie indziej) | Tak, w małej próbce | cenzurowanie (większość populacji); name-gate NAPRAWIONY i granica t_shock skorygowana/egzekwowana (SPRINT_v0.11.0.md P2), populacja P3 nieprzeliczona |

¹ **Kolumna powyżej opisuje etap n=10 (Exploratory Dataset), niezmieniona
z wersji sprzed re-runu.** Na n=185 konfirmacyjnym (re-run zamknięty
2026-07-20, `population_validation_v0_11_0.json`,
`pairwise_comparisons.n_fdr_significant_q_0_05`, zweryfikowane niezależnym
przeliczem BH-FDR) **wynik jest RÓŻNY dla każdej z trzech osi — nie
jednolity, jak błędnie zapisano we wcześniejszej wersji tej adnotacji
(korekta 2026-07-21, znaleziona przez audytora):**
- **Working Memory: 69/253 (27%)** — teraz dyskryminuje TAKŻE parowo.
- **Pattern Recognition: 77/253 (30%)** — teraz dyskryminuje TAKŻE parowo.
- **Pattern Retention: 0/253** — NIE zmieniło się, jedyna z trzech, gdzie
  parowy test nadal nic nie wykrywa.

Test OMNIBUSOWY (Kruskal-Wallis, niezależny od testu parowego) wykrył
istotny efekt dla wszystkich trzech osi niezależnie od powyższego: Working
Memory p=8.1e-17 → **VALIDATED**, Pattern Recognition p=4.5e-14 →
**VALIDATED**, Pattern Retention p=0.0254 → **EXPERIMENTAL** (Red Team,
sygnał widoczny tylko omnibusowo — mechanizm opisany przy tej osi
powyżej). Patrz AKTUALIZACJA 2026-07-21 na początku dokumentu i
`docs/METRIC_STATUS_TABLE.md` §4b/§7/footnote¹⁵.

---

## Cztery statusy walidacji per metryka × kontekst (SPRINT_v0.11.0.md P3)

**Zadanie CTO:** jeden label ("ROBUST"/"FRAGILE") miesza ze sobą pytania,
które są NIEZALEŻNE. Tabela niżej rozdziela je na cztery kolumny, osobno dla
KAŻDEJ z 30 kombinacji (lekcja, środowisko, metryka) obecnych w
`reports/population/population_validation_v0_10_1.json`:

1. **Measurement validity** — czy metryka w tym kontekście daje wiarygodny
   (CI95-ważny, `n_effective≥5`) wynik dla ≥80% populacji? Źródło: pole
   `classification`/`valid_rate` w artefakcie P3, bez zmian.
2. **Construct validity** — czy metryka mierzy to, co sugeruje jej nazwa?
   Źródło: formalne definicje (P1, sekcje wyżej w tym dokumencie) i sekcje
   "Czego NIE mierzy" — NIE duplikowane tutaj w całości, tylko przywołane
   przypisem.
3. **Power validity** — czy próbka (n=10/genom) ma moc statystyczną
   wystarczającą do wykrycia efektu takiej wielkości, jaki faktycznie
   zaobserwowano? **PENDING dla wszystkich 30 wierszy** — wymaga re-runu wg
   `publications/preregistration_v0_11_0_power_reproduction.json`, decyzja
   CTO (Wariant A/B/C) w toku, re-run WSTRZYMANY.
4. **Confirmatory validity** — czy wynik replikuje się w NIEZALEŻNEJ,
   prerejestrowanej próbie (nie tej, na której został po raz pierwszy
   zaobserwowany)? **PENDING dla wszystkich 30 wierszy** — z definicji nie
   może być odpowiedziane przed re-runem; obecny zbiór jest w całości
   eksploracyjny (Exploratory Dataset v0.10).

Legenda: ✔ = spełnione · ✘ = niespełnione/problematyczne · ◐ = częściowe,
z zastrzeżeniami · — = nie dotyczy (konstrukt/pomiar nie istnieje w tym
kontekście, NIE porażka).

| Lekcja | Środowisko | Metryka | Measurement | Construct | Power | Confirmatory |
|---|---|---|---|---|---|---|
| L1.1 | noise_world | Working Memory | ✔ | ◐¹ | PENDING | PENDING |
| L1.1 | noise_world | Adaptation | ✘ | ✘² | PENDING | PENDING |
| L1.1 | noise_world | Stability | ✔ | ◐³ | PENDING | PENDING |
| L1.1 | noise_world | Pattern Recognition | ✔ | ◐⁴ | PENDING | PENDING |
| L1.1 | noise_world | Pattern Retention | ✔ | ◐⁵ | PENDING | PENDING |
| L1.1 | noise_world | Final Energy Level | ✘ | ✘⁶ | PENDING | PENDING |
| L1.1 | stable_world | Working Memory | ✘⁷ | ◐¹ | PENDING | PENDING |
| L1.1 | stable_world | Adaptation | ✘⁷ | ✘² | PENDING | PENDING |
| L1.1 | stable_world | Stability | ✘⁷ | ◐³ | PENDING | PENDING |
| L1.1 | stable_world | Pattern Recognition | ✘⁷ | ◐⁴ | PENDING | PENDING |
| L1.1 | stable_world | Pattern Retention | ✘⁷ | ◐⁵ | PENDING | PENDING |
| L1.1 | stable_world | Final Energy Level | ✘⁷ | ✘⁶ | PENDING | PENDING |
| L1.1 | drift_world | Working Memory | ✔ | ◐¹ | PENDING | PENDING |
| L1.1 | drift_world | Adaptation | ✘ | ✘² | PENDING | PENDING |
| L1.1 | drift_world | Stability | ✔ | ◐³ | PENDING | PENDING |
| L1.1 | drift_world | Pattern Recognition | ✔ | ◐⁴ | PENDING | PENDING |
| L1.1 | drift_world | Pattern Retention | ✔ | ◐⁵ | PENDING | PENDING |
| L1.1 | drift_world | Final Energy Level | ✘ | ✘⁶ | PENDING | PENDING |
| L1.2 | shock_world | Homeostatic Resilience | ✘ | ✘⁸ | PENDING | PENDING |
| L1.2 | shock_world | Adaptation | ✘ | ✘² | PENDING | PENDING |
| L1.2 | shock_world | Stability | ✔ | ◐³ | PENDING | PENDING |
| L1.2 | shock_world | Final Energy Level | ✔ | ✘⁶ | PENDING | PENDING |
| L1.2 | stable_world | Homeostatic Resilience | —⁹ | —⁹ | PENDING | PENDING |
| L1.2 | stable_world | Adaptation | ✘⁷ | ✘² | PENDING | PENDING |
| L1.2 | stable_world | Stability | ✘⁷ | ◐³ | PENDING | PENDING |
| L1.2 | stable_world | Final Energy Level | ✘⁷ | ✘⁶ | PENDING | PENDING |
| L1.2 | drift_world | Homeostatic Resilience | —⁹ | —⁹ | PENDING | PENDING |
| L1.2 | drift_world | Adaptation | ✘ | ✘² | PENDING | PENDING |
| L1.2 | drift_world | Stability | ✔ | ◐³ | PENDING | PENDING |
| L1.2 | drift_world | Final Energy Level | ✘ | ✘⁶ | PENDING | PENDING |

**Podsumowanie Measurement validity (30 wierszy, zgodne z klasyfikacją P3):**
✔ 11 · ✘ (środowiska eksperymentalne) 8 · ✘⁷ (kontrola, oczekiwane) 9 · — 2.

¹ **Working Memory:** `silence_after_50` puste → domyślnie **1.0 CICHO**
(nie wyjątkiem) — narusza zasadę nadrzędną 1 tego sprintu.
**NIENAPRAWIONE w tym sprincie** (P2 objął wyłącznie name-gate L1.2, nie ten
silny-domyślny w L1.1) — kandydat do osobnego priorytetu.
² **Adaptation:** `_find_chaos_end()` daje false-positive "natychmiastowa
adaptacja" (`adaptation_tick=0`) dla genomów o wysokim `decay_rate` —
hipoteza post-hoc `decay_rate≈0.035`, nieprzetestowana niezależnie (sekcja
Adaptation wyżej, `docs/CURRENT_SCIENTIFIC_LIMITS.md` §5). **Doprecyzowanie
(SPRINT_v0.11.0.md, 2026-07-18):** to "✘" tutaj jest jednolite dla L1.1 i
L1.2, ale rzeczywisty konstrukt RÓŻNI SIĘ per (lekcja, środowisko) —
`docs/METRIC_STATUS_TABLE.md` §3 rozdziela to na ◐ (cold-start, L1.1 i
L1.2/drift_world) vs ✘ (pre-shock window bez związku z tematem lekcji,
wyłącznie L1.2/shock_world, gdzie wartość jest stała=10 dla 100% populacji).
Ten dokument NIE jest tu edytowany wstecznie — METRIC_STATUS_TABLE.md jest
teraz dokładniejszym źródłem dla Adaptation.
³ **Stability:** `error(t)=|1-energy(t)|` to PROXY energii (nie realny błąd
predykcji); `SI=1/(std+std+ε)` to skala odwrotna nieliniowa — utrudnia
interpretację wartości bezwzględnej (nie tylko porównawczej).
⁴ **Pattern Recognition:** dawna nazwa pola `mse_stimulus_phase` sugerowała
błąd kwadratowy, formuła zawsze była błędem bezwzględnym (MAE) — **pole
przemianowane na `mae_stimulus_phase` (SPRINT_v0.11.0.md P1, Wariant c,
2026-07-15)**, wartości bez zmian. Construct nadal ◐, nie ✔, bo "Recognition"
w nazwie pojęcia (nie pola) nadal sugeruje osąd binarny, którego metryka nie
daje — sam konstrukt (błąd predykcji podczas bodźca) pozostaje sensowny.
⁵ **Pattern Retention:** `memory_decay_rate` może być UJEMNY (przyrost, nie
spadek błędu) i zakłada liniowy zanik — nazwa "decay" zakłada kierunek,
którego dane nie gwarantują.
⁶ **Final Energy Level (dawniej "Energy Efficiency"):** pojedyncza wartość
energii w OSTATNIM ticku, NIE stosunek/wydajność — był to największy
mismatch nazwa/pomiar spośród 7 zmierzonych osi, **naprawiony rename na
"Final Energy Level"** (SPRINT_v0.11.0.md P1, sekcja wyżej) — Construct
nadal ✘ tutaj oznacza cos innego niz w pozostalych osiach: to nie mismatch
nazwa/formula (naprawiony), tylko fakt, ze ta os to zmienna stanu
fizjologicznego, nie zdolnosc poznawcza (patrz "Podsumowanie" ponizej).
⁷ `stable_world` to KONTROLA deterministyczna — `n_effective=1` dla każdej
metryki każdego genomu jest OCZEKIWANYM dowodem działania mechanizmu
CI95/pseudoreplikacji (`RESEARCH_READINESS_REPORT.md` §1.2), NIE usterką
pomiaru. "✘" tutaj ma inne znaczenie niż w środowiskach eksperymentalnych —
nie interpretować jako porażkę metryki.
⁸ **Homeostatic Resilience:** nazwa `recovery_time` metodologicznie myląca —
mierzy USTANOWIENIE (`time_to_sustained_band`), nie POWRÓT;
`pre_shock_in_band_fraction` < progu 0.8 potwierdza to empirycznie (sekcja
Homeostatic Resilience wyżej).
⁹ `stable_world`/`drift_world` w L1.2: Homeostatic Resilience nie ma tu
ZASTOSOWANIA (brak zdarzenia perturbacyjnego do zmierzenia) — to NIE jest
name-gate (naprawiony w SPRINT_v0.11.0.md P2, sekcja Homeostatic Resilience
wyżej), to prawdziwy brak konstruktu w tych środowiskach. Measurement i
Construct oznaczone "—" (nie dotyczy), nie "✘".
