# Validity Report — granice interpretacji 14 osi Competency Profile

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
ROBUST w obu środowiskach, również 0/253 par przeżywa FDR w każdym z nich.
Trzy z siedmiu zmierzonych osi są więc wiarygodnie mierzalne, ale w tej
próbce 23 genomów **nie różnicują genomów w żaden sposób, który przetrwałby
korektę na wielokrotne porównania.**

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

Kontrast: **Stability i Energy Efficiency (gdy ROBUST) DYSKRYMINUJĄ silnie**
— np. Stability w `noise_world`: 208/253 par przeżywa FDR (82% wszystkich
par genomów różni się istotnie). Nie każda zmierzona oś ma ten sam charakter
— stąd potrzeba tej tabeli per metryka, nie jednego zbiorczego wniosku.

---

## Perception

**Co mierzy:** nic — `not yet measured` (bez zmian od v0.8.4).
**Czego NIE mierzy:** brak lekcji izolującej percepcję jako endpoint.
**Kiedy zdegenerowana:** nie dotyczy (brak pomiaru).
**Kiedy myląca:** nie dotyczy.
**Kiedy wymaga innej interpretacji:** `insufficient_data` w Competency
Profile nie znaczy "słaba percepcja" — znaczy "nikt tego nie zmierzył".

---

## Attention

**Co mierzy:** nic — `not yet measured`. `attention_threshold` istnieje i
wpływa pośrednio na L1.1 (dobór rekordów pamięci w `predict()`), ale nie
jest testowany jako zmienna niezależna, i (patrz P3) nigdy nie jest
próbkowany w populacji — trzymany na stałe 0.3 dla wszystkich 23 genomów.
**Czego NIE mierzy:** selektywności uwagi w żadnym ilościowym sensie.
**Kiedy zdegenerowana / myląca:** nie dotyczy.
**Kiedy wymaga innej interpretacji:** identycznie jak Perception.

---

## Pattern Recognition (`mse_stimulus_phase`)

**Co mierzy:** średni błąd predykcji PODCZAS prezentacji bodźca (tick<100,
L1.1) — jak dobrze Brain trafia bieżący sygnał, gdy wciąż go widzi.
**Czego NIE mierzy:** rozpoznawania NOWEGO wzorca — ten sam, powtarzalny
sygnał przez cały przebieg; brak testu transferu na inny wzorzec w ramach
jednego runu.

**Kiedy zdegenerowana (P3):** GENOME-ROBUST 100% w `noise_world` i
`drift_world` (23/23). Zdegenerowana (0%) w `stable_world` — oczekiwane,
środowisko deterministyczne, `n_effective=1` dla każdego genomu z definicji.

**Kiedy myląca (P3, patrz "Kluczowe odkrycie"):** mimo 100% ROBUST, **0/253
par genomów przeżywa FDR w obu stosowanych środowiskach.** Metryka jest
wiarygodnie mierzalna, ale w tej próbce populacji nie różnicuje genomów.

**Kiedy wymaga innej interpretacji:** wysoki `valid_rate` w raporcie
populacyjnym NIE jest dowodem, że genomy różnią się w Pattern Recognition —
sprawdź zawsze `pairwise_comparisons.n_fdr_significant_q_0_05`, nie tylko
`classification`.

---

## Pattern Retention (`memory_decay_rate`)

**Co mierzy:** `(mse_silence_phase - mse_stimulus_phase) / silence_ticks` —
tempo pogarszania się trafności predykcji w fazie ciszy L1.1.
**Czego NIE mierzy:** retencji w sensie długoterminowym (poza jednym
przebiegiem 200 ticków); nie rozróżnia zapominania od braku uczenia się od
początku.

**Kiedy zdegenerowana (P3):** identycznie jak Pattern Recognition —
GENOME-ROBUST 100% w `noise_world`/`drift_world`, zdegenerowana w
`stable_world` (oczekiwane).

**Kiedy myląca (P3):** **0/253 par przeżywa FDR w obu środowiskach** —
trzecia oś z tym samym profilem "mierzalna, ale niedyskryminująca" co
Pattern Recognition i Working Memory.

**Kiedy wymaga innej interpretacji:** jak wyżej — `GENOME-ROBUST` czytać
jako "infrastruktura działa", nie jako "genomy się różnią".

---

## Working Memory (`mse_vs_pattern_after_stimulus_removal`, primary endpoint L1.1)

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

**Co mierzy:** nic — `not yet measured`, brak mechanizmu odróżniającego
pamięć długoterminową od roboczej w `BrainTissue`.
**Czego NIE mierzy / kiedy zdegenerowana / myląca:** nie dotyczy.
**Kiedy wymaga innej interpretacji:** jak Perception/Attention.

---

## Prediction

**Co mierzy:** nic jako osobny endpoint — `last_prediction` jest składnikiem
KAŻDEJ metryki MSE w L1.1, ale predykcja "w przód" (bodziec jeszcze
niewystąpiony) nie jest testowana jako osobna hipoteza.
**Kiedy wymaga innej interpretacji:** nie mylić z Working Memory/Pattern
Recognition — te używają predykcji jako narzędzia, nie testują jej wprost.

---

## Adaptation (`adaptation_tick`)

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

**Co mierzy:** nic — `not yet measured`, `act()` to czyste echo bodźca, brak
mechanizmu wyboru działania.
**Kiedy wymaga innej interpretacji:** jak Perception.

---

## Generalization

**Co mierzy:** nic — `not yet measured`, brak lekcji trenującej na jednym
scenariuszu i testującej na innym w ramach tego samego przebiegu.
**Uwaga metodologiczna z P2/P3:** populacja BYŁA uruchamiana na 3
środowiskach (`noise_world`/`shock_world`, `stable_world`, `drift_world`),
ale to NIE jest test generalizacji w sensie tego pojęcia — każdy przebieg
jest treningiem i testem na TYM SAMYM środowisku, nie transferem.

---

## Planning

**Co mierzy:** nic — `not yet measured`, `act()` nie ma pojęcia sekwencji
ani horyzontu czasowego.
**Kiedy wymaga innej interpretacji:** jak Perception.

---

## Stability (`stability_score`)

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

## Energy Efficiency (`final_energy`)

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

**Kiedy wymaga innej interpretacji:** Energy Efficiency jest kontekstowo
zmienna (ROBUST w szoku, FRAGILE bez szoku) bardziej niż jakakolwiek inna
zmierzona oś — nie zakładać stałej wiarygodności między środowiskami.

---

## Homeostatic Resilience (`recovery_time` / `time_to_sustained_band`)

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

**Kiedy myląca — DWA UKRYTE OGRANICZENIA DZIEDZINY (P2, potwierdzone
empirycznie w P3):**

1. **Name-gate:** `run_shock_recovery()` liczy `t_shock`/`primary_endpoint`/
   `pre_shock_in_band` WYŁĄCZNIE gdy `scenario == "shock_world"` dosłownie
   (`lesson_L1_2.py:139`) — NIE gdy scenariusz jest semantycznie "szokowy".
   P3 potwierdza to empirycznie: Homeostatic Resilience jest
   **`not_applicable`** (nie "zdegenerowana", dosłownie brak pola) w
   `stable_world` i `drift_world` — nawet `drift_world`, który ma realną,
   ciągłą zmienność, nie aktywuje tego endpointu, bo nie nazywa się
   dosłownie `"shock_world"`.
2. **Granica t_shock≤150:** `compute_recovery_time()` zakłada
   `t_shock + W - N ≤ ticks_total-1` (299) — dla `t_shock>159` funkcja
   dostałaby `KeyError` z `entropy_by_tick` (dziura poza zarejestrowanym
   zakresem). Populacja NIE natrafiła na ten przypadek (używa
   `shock_world` z oryginalnym `t_shock∈[20,80]`), ale `long_stable_shock_world`
   (P2) był świadomie zaprojektowany, by trzymać się PONIŻEJ tej granicy
   (`t_shock∈[100,150]`) — sama granica pozostaje nietestowana boleśnie,
   tylko udokumentowana jako znana krawędź domeny.

**Kiedy wymaga innej interpretacji:** interpretując Homeostatic Resilience
dla NOWEGO genomu/środowiska, zawsze sprawdzić najpierw: (a) czy scenariusz
nazywa się dosłownie `"shock_world"` (inaczej pole nie istnieje wcale), (b)
jaki jest `decay_rate` tego genomu (silny predyktor cenzurowania, patrz P3),
(c) czy `t_shock` mógłby przekroczyć 159 dla `ticks_total=300`.

---

## Podsumowanie: 7 zmierzonych osi wg profilu degeneracji

| Oś | ROBUST wszędzie poza kontrolą? | Dyskryminuje po FDR? | Główny mechanizm ograniczenia |
|---|---|---|---|
| Pattern Recognition | Tak (2/2 środ.) | **Nie** (0/253 w obu) | — (metryka czysta, ale bez sygnału w tej populacji) |
| Pattern Retention | Tak (2/2 środ.) | **Nie** (0/253 w obu) | — |
| Working Memory | Tak (2/2 środ.) | **Nie** (0/253 w obu) | — (patrz "Kluczowe odkrycie") |
| Stability | Tak (4/4 środ. nie-kontrolnych) | **Tak, silnie** (82-92%) | mała wariancja resztowa → duże Cohen's d, ostrożna interpretacja |
| Adaptation | **Nie** (35-43% w L1.1, 0% w L1.2) | Tak, gdy mierzalna | *hipoteza post-hoc, niepotwierdzona:* wysoki `decay_rate` → przedwczesna detekcja końca chaosu |
| Energy Efficiency | **Częściowo** (39-100% zależnie od kontekstu) | Tak, gdy mierzalna | *hipoteza post-hoc, niepotwierdzona:* wysoki `decay_rate` → spłaszczenie energii między seedami |
| Homeostatic Resilience | **Nie** (22% w shock_world, n/a gdzie indziej) | Tak, w małej próbce | cenzurowanie (większość populacji) + name-gate + granica t_shock |
