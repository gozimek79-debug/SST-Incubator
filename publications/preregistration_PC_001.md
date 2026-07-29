# PREREJESTRACJA — eksperyment Predictive Coding (PC-001), rewizja 2

**Status:** **ZAMROŻONA** decyzją **CTO D-006** (2026-07-28) · korekta językowa §6/§7 naniesiona
**Podstawa:** D-004 (kontrole K1–K5, zasada O-001) · D-005 (poprawki redakcyjne) · D-006 (zamrożenie) · AIA v4 (próg 20%)
**Autor:** audytor niezależny
**Data:** 2026-07-28 · gałąź `v0.7.2-scientific-integrity` @ `4ad629c`

> **Relacja do rewizji 1:** rev1 zachowana jako ślad. Rewizja 2 wprowadza: Primary Endpoint oparty
> wyłącznie na L1.2 (D-005 pkt 2), `stable_world` jako środowisko **referencyjne poza inferencją
> statystyczną** (pkt 4), sekcję **Threats to Interpretation** (pkt 6) oraz — **poza numerowanymi
> punktami D-005, na podstawie argumentu CTO z dyskusji** — dwuwarunkowy Primary Endpoint
> (nachylenie regresji + próg 20%) zamiast samych okien brzegowych. Ta ostatnia zmiana podlega
> wetu CTO przed zamrożeniem.

> **ZOBOWIĄZANIE:** po zamrożeniu żadne kryterium nie może zostać zmienione w reakcji na obejrzany
> wynik. Zmiana wyłącznie przez datowany aneks, **przed** obejrzeniem danych, których dotyczy.

---

## 1. Co ten eksperyment testuje — i czego NIE testuje

**Testuje:** czy w obrębie pojedynczego przebiegu lekcji błąd predykcji maleje **w sposób
trendowy**, i czy ten spadek pochodzi z mechanizmu predykcyjnego, a nie z alternatywnych wyjaśnień.

**NIE testuje:** uczenia między lekcjami (Wariant 2 — BLOCKED wg D-002), generalizacji na nowe
środowiska (§10), ani powstania inteligencji czy ontogenezy. Nawet wynik pozytywny oznacza
**potwierdzenie konkretnego mechanizmu w architekturze CLOS** — nic więcej.

---

## 2. Primary Endpoint

**Podstawą głównego wniosku konfirmacyjnego jest wyłącznie lekcja L1.2** (D-005 pkt 2).
L1.1 ma charakter **wspierający** (§4) — jest za krótka (100 mierzalnych ticków, okna po 20)
i nie powstała do badania PC.

### 2.1 Dwa warunki, oba wymagane

Jednostką analizy jest **pojedynczy przebieg** = `(środowisko, genom, seed)`.

**Warunek A — trend malejący.** Regresja liniowa `prediction_error(t)` po całym mierzalnym oknie
przebiegu (L1.2: ticki 0–299). Wymagane **β < 0**, istotne statystycznie.

**Warunek B — wielkość redukcji ≥ 20%** (próg z AIA v4, użyty jako **próg interpretacyjny**):

| Symbol | Definicja |
|---|---|
| `W_early` | średnia `prediction_error`, ticki **0–59** (pierwsze 20% okna) |
| `W_late` | średnia `prediction_error`, ticki **240–299** (ostatnie 20% okna) |
| `redukcja` | `(W_early − W_late) / W_early` |

**Uzasadnienie dwuwarunkowości:** same okna brzegowe nie odróżniają monotonicznego spadku
od oscylacji. Szereg `40 30 20 10 5 15 5 15 5 15 5` daje podobne okna brzegowe co szereg
malejący, mimo zupełnie innej trajektorii. Warunek A eliminuje tę klasę fałszywych pozytywów.

Ticki z `prediction_error = None` są **wykluczone**, nie zastępowane zerem. Przebieg z < 5
wartościami nie-`None` w którymkolwiek oknie → `INSUFFICIENT_DATA`, wyłączony z komórki
i **raportowany**, nie ukrywany.

### 2.2 Test statystyczny

- **Warunek A:** rozkład współczynników `β` ze wszystkich przebiegów w komórce; test znaków
  / Wilcoxona przeciw `β = 0`.
- **Warunek B:** **test Wilcoxona dla par** na `(W_early, W_late)` w komórce.
- **Korekta:** Benjamini-Hochberg **FDR q = 0.05**, na liczbie **realnie testowalnych** komórek
  (precedens `fdr_correction_omnibus` z v0.11), nie nominalnych.
- **Wybór nieparametryczny jest celowy:** v0.11 wykazało złamaną homoskedastyczność w części osi,
  przez co ANOVA była nieważna, a rozstrzygał Kruskal-Wallis.
- **Wielkość efektu:** mediana `redukcja` w komórce.

**Primary Endpoint spełniony**, gdy: `β < 0` istotne (A) **ORAZ** mediana `redukcja ≥ 20%`
przy p < 0.05 po FDR (B).

### 2.3 Zakres wykonania

- **Lekcja główna:** L1.2 (300 ticków, `PERCEIVE` nigdy pomijany → pełne okno mierzalne).
- **Genomy:** 23 (`default`, `highly_plastic`, `minimal`, `pop_000`–`pop_019`) — zestaw z v0.11.
- **Środowiska inferencyjne:** `shock_world`, `pure_noise_world` (K4).
- **Środowisko referencyjne (poza inferencją):** `stable_world` — patrz K2.
- **Liczba seedów:** **wynika z analizy mocy**, wykonanej i zatwierdzonej **przed** uruchomieniem
  (D-005 pkt 3). Prerejestracja celowo nie podaje jej z góry.

---

## 3. Threats to Interpretation (D-005 pkt 6)

**Spadek błędu predykcji nie jest sam w sobie dowodem działania mechanizmu predykcyjnego.**
Poniższe mechanizmy trywialne dają ten sam spadek i muszą być odróżnione:

| # | Mechanizm trywialny | Dlaczego daje spadek PE | Która kontrola go odróżnia |
|---|---|---|---|
| T1 | **System przestaje reagować na świat** | predykcja zamiera w stałej wartości; jeśli input też jest blisko niej, `PE` maleje **mimo zerowej adaptacji** | K5 (ablacja — stała predykcja daje ten sam spadek) |
| T2 | **Predykcja zbiega do średniej sygnału** | statystycznie optymalne bez żadnego modelu świata | K4 (w czystym szumie średnia też minimalizuje błąd) |
| T3 | **Amplituda sygnału maleje** | `\|predykcja − input\|` kurczy się bez poprawy predykcji | K2 (świat referencyjny o stałej amplitudzie) |
| T4 | **Efekt podłogi (floor effect)** | `PE` osiąga minimum metryki i nie może spaść dalej — pozorna „stabilizacja" | Warunek A (β) + inspekcja trajektorii |
| T5 | **Uczenie sekwencji, nie przewidywanie** | zapamiętanie konkretnego przebiegu bez modelu generatywnego | K3 (zmiana reguł musi wywołać wzrost PE) |

**Problem otwarty, świadomie niemierzalny w PC-001** (uwaga CTO): redukcja PE może współwystępować
z **utratą jakości zachowania** — organizm „wygrywa" z metryką, ignorując świat. PC-001 **nie mierzy
jakości zachowania**. Zapisujemy to jako znane ograniczenie: nawet pełne spełnienie reguły
decyzyjnej §5 **nie wyklucza**, że redukcja PE zachodzi kosztem funkcji. Weryfikacja tego wymaga
osobnego eksperymentu (§10) i **nie jest warunkiem pierwszego potwierdzenia mechanizmu**.

---

## 4. L1.1 — wynik wspierający (nie konfirmacyjny)

L1.1 wnosi wyłącznie **fazę bodźca (ticki 0–99)** — w fazie ciszy `prediction_error` nie powstaje
(`CURRENT_SCIENTIFIC_LIMITS` §8). Okna: `W_early` = 0–19, `W_late` = 80–99.

Analiza L1.1 jest wykonywana identyczną procedurą i **raportowana**, ale:
- **nie wchodzi do reguły decyzyjnej §5**,
- zgodność jej kierunku z L1.2 jest **wsparciem interpretacyjnym**, nie dowodem,
- rozbieżność między L1.1 a L1.2 jest **faktem do zaraportowania**, nie powodem do odrzucenia L1.2.

---

## 5. Confirmatory Controls (K1–K5)

### K1 — Baseline (surogat z przetasowaniem)

**Charakter:** kontrola **analityczna surogatowa**, post-hoc. **Nie jest ingerencją w system.**

**Procedura:** przetasować `prediction` między tickami w obrębie przebiegu (zachowując rozkład,
niszcząc związek czasowy), przeliczyć `PE_shuffled = |prediction_shuffled − input|`, przepuścić
przez **identyczny** pipeline analityczny (warunki A i B).

**Kryterium PC:** w danych przetasowanych **nie wolno** uzyskać spełnienia A ani B.
**Falsyfikacja:** spełnienie → spadek jest artefaktem procedury. **PC odrzucone.**

### K2 — Static World (środowisko referencyjne, POZA inferencją statystyczną)

**Status formalny (D-005 pkt 4):** `stable_world` **nie jest częścią inferencji statystycznej.**
Jest środowiskiem **referencyjnym, opisowym**. Wyniki z niego **nie mogą** stanowić samodzielnego
dowodu statystycznego — jest deterministycznie zdegenerowane (ignoruje seed, `n_effective = 1`).

**Zastosowanie:** porównanie **opisowe**. Jeśli trajektoria PE w `stable_world` jest nieodróżnialna
od `shock_world`, jest to **przesłanka interpretacyjna** przeciw PC — nie test.

### K3 — World Shift

**Środowisko:** `shock_world` (stała 0.2 → wstrząs w ticku 20–80 → nowy reżim; `shock_tick`
deterministyczny z seeda, więc znany dla każdego przebiegu).

**Kryterium PC — oba warunki:**
1. **Wzrost:** średnia PE w `[shock_tick, shock_tick+20]` **>** średnia w `[shock_tick−20, shock_tick−1]`.
2. **Ponowna adaptacja:** średnia PE w `[shock_tick+40, shock_tick+60]` **<** średnia
   w `[shock_tick, shock_tick+20]`.

**Falsyfikacja:** brak wzrostu po zmianie reguł → system nie reaguje na niespodziankę, tylko
odtwarza wyuczoną sekwencję (T5). **PC odrzucone.**

### K4 — Noise Control

**Środowisko:** `pure_noise_world` — nowy scenariusz (D-004 pkt 2): sam szum gaussowski, zero
sygnału, brak struktury do nauczenia. Dodawany do `clos_world/scenarios.py` (poza Core).

**Kryterium PC:** **nie wolno** uzyskać spełnienia A ani B.
**Falsyfikacja:** spełnienie → system uczy się artefaktu metryki (T2), nie struktury świata.
**PC odrzucone.**

### K5 — Ablation (surogatowa kontrola analityczna)

**Charakter:** kontrola **analityczna kontrfaktyczna**, post-hoc. **NIE jest ingerencją w działanie
systemu** — Core nietknięty (D-004 pkt 1). Odpowiada na pytanie *„czy ten spadek mógłby powstać
bez mechanizmu"*, **nie** *„co się stanie, gdy mechanizm wyłączymy"*. To rozróżnienie musi być
zachowane w każdym raporcie i publikacji.

**Procedura:** zastąpić `prediction` **stałą 0.5** (wartość neutralnej predykcji Core,
`clos_brain/runtime/prediction.py:20`), przeliczyć `PE_ablated = |0.5 − input|`, przepuścić
przez identyczny pipeline analityczny.

**Kryterium PC:** spełnienie A i B **musi zniknąć**.
**Falsyfikacja:** utrzymanie się przy martwej predykcji → spadek nie pochodzi z predykcji (T1).
**PC odrzucone.**

---

## 6. Reguła decyzyjna

**Hipotezę o obecności mechanizmu zgodnego z Predictive Coding uznaje się za wspartą** wyłącznie
gdy **wszystkie** warunki zachodzą **dla lekcji L1.2**:

| # | Warunek |
|---|---|
| 1 | **Warunek A** — `β < 0` istotne (trend malejący) |
| 2 | **Warunek B** — mediana redukcji **≥ 20%** |
| 3 | **p < 0.05** po korekcie FDR |
| 4 | **K1** — efekt **nie występuje** w danych przetasowanych |
| 5 | **K3** — PE **rośnie** po zmianie reguł i **ponownie maleje** po adaptacji |
| 6 | **K4** — efekt **nie występuje** w `pure_noise_world` |
| 7 | **K5** — efekt **znika** po ablacji surogatowej |

**K2** wchodzi jako **przesłanka opisowa**, nie warunek formalny (D-005 pkt 4).

**Niespełnienie któregokolwiek warunku 1–7 oznacza, że hipoteza NIE została wsparta.**
Wynik częściowy raportuje się jako częściowy — nie przeformułowuje kryteriów, by go objąć.

**Język raportowania (D-006 pkt 5):** dopuszczalne jest wyłącznie sformułowanie *„dane zgodne
z hipotezą Predictive Coding"*. Sformułowanie *„CLOS posiada mechanizm Predictive Coding"* jest
**niedopuszczalne** w raportach i publikacjach — także przy wyniku w pełni pozytywnym.

---

## 7. Co uznajemy za wynik negatywny

Niespełnienie reguły decyzyjnej **nie oznacza**, że mechanizmu nie ma — oznacza, że **hipoteza nie
została wsparta w tym układzie**. Rozróżnienie jest wiążące, wprost z lekcji P0: przy 2,8% mocy
ogłoszono „Working Memory nie dyskryminuje", co okazało się fałszywym negatywem przetrwałym
kilka sprintów.

**Wynik negatywny musi być raportowany łącznie z osiągniętą mocą statystyczną.** Bez tej liczby
jest nieinterpretowalny i **nie wolno go zapisać jako `MEASURED_BUT_NULL`.**

---

## 8. Znane ograniczenia (zapisane PRZED wykonaniem)

1. **Faza ciszy L1.1 niemierzalna** — `PERCEIVE` pomijany → `last_input = None` → `compute_error()`
   early-return. Granica pojęciowa, nie brak danych (`CURRENT_SCIENTIFIC_LIMITS` §8).
2. **`stable_world` zdegenerowane** — poza inferencją statystyczną (D-005 pkt 4).
3. **K1 i K5 to surogaty analityczne**, nie ingerencje w system (§5).
4. **Jakość zachowania nie jest mierzona** — patrz Threats to Interpretation §3, problem otwarty.
5. **Brak testu generalizacji** — §10.

---

## 9. Analizy post-hoc

Każda hipoteza niewynikająca wprost z tego dokumentu, sformułowana po obejrzeniu danych, jest
**eksploracyjna** i musi być tak oznaczona. Nie może wchodzić do reguły decyzyjnej §6 ani być
prezentowana jako potwierdzenie mechanizmu.

---

## 10. Roadmapa badań (poza zakresem PC-001)

- **PC-002: kształt trajektorii** — warunek `β < 0` przepuszcza przebieg typu „gwałtowny spadek →
  plateau" (`100 90 80 70 60 5 5 5 5 5`), który spełnia oba warunki Primary, nie wyglądając jak
  uczenie. To znane ograniczenie pierwszego eksperymentu, zapisane jako **T4**. PC-002 ma badać
  **kształt** trajektorii, nie tylko kierunek i wielkość (D-006).
- **Test generalizacji** — czy wzorzec występuje w środowiskach wcześniej niewidzianych
  (`drift_world`, `high_noise_world`, `recurring_shock_world`). Mocny argument w publikacji,
  **nieobowiązkowy do pierwszego potwierdzenia** (D-004). Wymaga własnej prerejestracji.
- **Redukcja PE vs jakość zachowania** — czy spadek PE współwystępuje z utrzymaniem funkcji,
  czy zachodzi jej kosztem (§3, problem otwarty T1).

---

## 11. Wymagania techniczne przed uruchomieniem

| # | Wymaganie | Podstawa |
|---|---|---|
| 1 | `Snapshot` rozszerzony o `prediction` i `input` — **wyłącznie surowe dane obserwacyjne**; żadnych danych pochodnych, interpretacyjnych ani wewnętrznych stanów modelu | D-005 pkt 5, O-001 |
| 2 | Rozszerzenie przechodzi **test usuwalności** (`observe=False` → zero wpływu na Execution Pipeline) | AIA v4 |
| 3 | `pure_noise_world` dodany do `clos_world/scenarios.py` | D-004 pkt 2 |
| 4 | **Analiza mocy** wykonana i zatwierdzona w aneksie — eksperyment **nie może** ruszyć bez niej | D-005 pkt 3 |
| 5 | Hard-Halt / baseline hash dla przebiegu PC, jak w v0.11 | precedens v0.11 |

---

## 12. Zamrożenie

Po zatwierdzeniu przez CTO dokument zostaje zamrożony i zacommitowany jako
`publications/preregistration_PC_001.json` (+ hash w rejestrze). Zmiany wyłącznie przez datowany
aneks, **przed** obejrzeniem danych, których dotyczą.

---

*Fakty techniczne zweryfikowane w kodzie na klonie `4ad629c`: liczby ticków (L1.2 = 300, L1.1 = 200
z fazą bodźca 0–99), dostępność środowisk, mechanizm `PERCEIVE`/`compute_error`, wartość neutralnej
predykcji 0.5, status `_CERTIFIED_SKIPPABLE = {PERCEIVE}`.*
