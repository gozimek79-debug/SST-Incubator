# W2 COMPLETION REPORT — zamknięcie cyklu przeprojektowania Primary Endpoint

**Od:** audytor niezależny · **Dla:** CTO
**Data:** 2026-07-28 · gałąź `v0.7.2-scientific-integrity` @ `15d304e`
**Podstawa:** **D-019** (W2 zatwierdzony, Hard Halt W2 zdjęty, globalny pozostaje)

> **Status blokad po D-019:**
> **Hard Halt W2 — ZDJĘTY** (implementacja i walidacja V-C zakończone).
> **Hard Halt eksperymentu — POZOSTAJE.** Kolejne bramki obowiązkowe:
> pilot pod W2 → Monte Carlo → baseline → bramka wejścia → start.

---

## 1. Problem

**Pilot B4a (230 przebiegów) trafił w dwa z trzech prerejestrowanych warunków zatrzymania:**

- `W_early = 0.0` **dokładnie** dla wszystkich 23 genomów przy `seed=2` w `shock_world`
  (20% przebiegów tego środowiska),
- rozkład `W_early` grupował się w **5 klastrów odpowiadających seedom**, nie w 23 wartości
  genomowe — **seed dominował nad genomem** niemal całkowicie.

Wykonawca zatrzymał proces zgodnie z instrukcją, zamiast przejść do B4b.

---

## 2. Analiza

Przyczyną nie był artefakt pilota, tylko **struktura środowiska**:

```
shock_world:
  tick <  shock_tick :  0.2                                (STAŁA — trywialnie przewidywalna)
  tick == shock_tick :  shock_magnitude                     (skok)
  tick >  shock_tick :  shock_magnitude·0.8 + N(0, 0.02)    (szum — podłoga nieredukowalna)

shock_tick ~ Uniform[20, 80],  okno W_early = [0, 60)
  ⇒ P(shock_tick > 60) ≈ 33% — całe okno przedwstrząsowe, PE ≈ 0
```

**Wniosek:** w `shock_world` błąd predykcji **strukturalnie rośnie** przez przebieg
(`W_early → 0`, `W_late ≥ podłoga szumu`). Primary Endpoint wymagał **spadku o ≥20%** —
niemożliwego dla klasy predyktorów zaimplementowanych w `prediction.py`.

**Diagnoza właściwa (trafność konstrukcyjna):** hipoteza mówiła *„system uczy się przewidywać
strukturę świata"*, a operacjonalizacja mierzyła *„jak bardzo świat stał się trudniejszy"*.
To ta sama klasa błędu co `adaptation_tick` w v0.11 — **nazwa i mechanizm rozjechały się.**

---

## 3. Błędne hipotezy — dwie, obie ukryte

### H1: „redukcja surowego PE mierzy uczenie w każdym środowisku"

**Fałszywa.** PE ma dwie składowe: **redukowalną** (struktura świata) i **nieredukowalną** (szum).
PC może zmniejszyć tylko pierwszą. Jeden próg „≥20% surowego PE" znaczy co innego przy podłodze 0,
a co innego przy 0.25 — **kryterium niespójne między środowiskami.**

### H2: „generator szumu jest nieobciętym rozkładem normalnym"

**Fałszywa — i to jest cenniejsze znalezisko.** `clos_world/generators.py:20` obcina wyjście
do `[0,1]`, więc rozkład jest **normalnym uciętym**. Wzór `E|N(0,σ²)| = σ√(2/π)` jest poprawny,
ale **opisuje rozkład, którego środowisko nie produkuje.**

**Skala błędu, zmierzona:**

| | `noise_world` |
|---|---|
| podłoga analityczna (H2 fałszywa) | **0.1784** |
| podłoga z rzeczywistego generatora | **0.09589** |
| **różnica** | **~86% zawyżenia** |

Przyczyna: sinus `noise_world` sam zakresuje sygnał do `[0.2, 0.8]`, a szum `σ ≈ 0.224`
**regularnie** wypycha sumę poza `[0,1]`. **Obcięcie jest systematyczne, nie brzegowe.**

Gdyby wartość analityczna została zamrożona, **cały endpoint byłby przesunięty o ~86%** —
przy liczbach wyglądających na tyle sensownie, że nikt by tego nie zauważył.

---

## 4. Nowa specyfikacja

### W2 — redukcja składowej redukowalnej

```
PE_red(t)   = max(0, PE(t) − floor)
redukcja_W2 = (W_early_red − W_late_red) / W_early_red
```

Mierzy: **ile z tego, co dało się nauczyć, zostało nauczone.** Szum jest z definicji poza
licznikiem, więc miara jest **porównywalna między środowiskami** — 20% znaczy to samo wszędzie.

### V-C (Adaptive Validation) — decyzja mechaniczna, nie operatorska

Spór „stała czy funkcja" był **źle postawiony**. Właściwe pytanie: *czy stała jest wystarczającym
przybliżeniem dla tego eksperymentu* — a to jest **sprawdzalne**:

```
bias_roznicowy = | mean(floor(t) w W_early) − mean(floor(t) w W_late) |
  < FLOOR_BIAS_TOLERANCE  → model "constant"
  ≥ FLOOR_BIAS_TOLERANCE  → model "per_tick" AUTOMATYCZNIE + ostrzeżenie + zapis decyzji
```

**Uzasadnienie:** dla środowiska stacjonarnego i okresowego średnia `floor(t)` po pełnym okresie
jest stała. Przy oknach obejmujących całkowitą liczbę okresów obciążenie jest w obu identyczne.
Przy niedopasowaniu — różnica obciążeń wchodzi wprost do licznika i **udaje efekt albo go maskuje**.

### Parametry — wszystkie wyprowadzone, żaden wybrany „na oko"

| Parametr | Wartość | Skąd |
|---|---|---|
| `N` (realizacje na tick) | 100 000 | z kryterium `SE(floor) < 0.001` = 5% `MIN_DENOMINATOR` |
| `MIN_DENOMINATOR` | 0.02 | konwencja projektu (Engineering Constant v1), jawnie deklarowana |
| `FLOOR_BIAS_TOLERANCE` | 0.002 | **parametr prerejestrowany PC-001**, nie globalna stała CLOS |
| próg FLOOR_LIMITED → INCONCLUSIVE | 30% | bezpiecznik przeciw selekcji przebiegów |

---

## 5. Implementacja

| Moduł | Rola |
|---|---|
| `clos_world/floor_model.py` | wyznaczenie podłogi **z rzeczywistego generatora** (nie ze wzoru) |
| `clos_scientist/w2_endpoint.py` | endpoint W2 + kontrola odtwarzalności (`FrozenFloorMismatchError`) |
| `clos_scientist/pc_001_experiment_config.py` | konfiguracja eksperymentu (D-012) + **zamrożona `floor_env`** |

**Wynik dla `noise_world`** (produkcyjne `N = 100 000`, pełne okno 300 ticków):

```
floor_model:     "constant"
floor_env:        0.09589
bias_roznicowy:   0.000024      (83× poniżej tolerancji 0.002)
seed_range:       500000-599999  (rozłączny z pilotem 1-5 i konfirmacją 1001+)
```

**Wszystkie trzy moduły w `CRITICAL_FILES_PC_001`** (37 → 40) — są definicją Primary Endpoint
w kodzie, więc endpoint nie może się zmienić bez złamania hasha.

---

## 6. Walidacja

| # | Test | Rola |
|---|---|---|
| 1 | podłoga przeliczona niezależnie, zgodność 1e-6 | poprawność wyprowadzenia |
| 2 | NEG: podłoga zawyżona → wszystkie `FLOOR_LIMITED` | działanie progu |
| **3** | **NEG: `floor=0` → W2 ≡ W1 **oraz** `floor>0` → `PE_red < PE`** | **kluczowy** |
| 4 | SYM: predyktor idealny → `PE_red ≈ 0` → `FLOOR_LIMITED` | poprawność podłogi |
| 5 | SYM: predyktor stały → brak redukcji | miara nie generuje efektu z niczego |
| 6 | brzegowe: `W_early_red = 0`, wszystkie `PE < floor` | dzielenie przez zero |
| **W2-T7** | **mechanizm V-C: (a) stała przy małym biasie, (b) automatyczne `floor(t)` przy dużym, (c) DOWÓD braku ścieżki operatorskiej** | **V-C jest mechanizmem, nie sugestią** |
| — | NEG: zmieniona zamrożona `floor_env` → `FrozenFloorMismatchError` z „HALT" | odtwarzalność |

**Test 3 wzmocniony przez wykonawcę:** sama część `floor=0 → W2≡W1` **nie złapałaby** implementacji
pobierającej `floor_env` bez odejmowania, bo `max(0, PE−0) == PE` niezależnie od tego, czy
odejmowanie zachodzi. Dodanie drugiej części domyka lukę.

**627/627 testów PASS.** Core (`clos_brain/`, `clos_kernel/genome`, `birth/`) nietknięty.
`requirements.txt` bez scipy.

---

## 7. Zamknięcie

**W2 zatwierdzony (D-019). Hard Halt W2 zdjęty. Hard Halt eksperymentu pozostaje.**

**Pozostałe bramki, wszystkie obowiązkowe:**

```
[✅ W2/V-C]  →  pilot pod W2  →  Monte Carlo (B4b)  →  baseline (B5)  →  bramka (B6)  →  START
```

**Ponowny pilot jest konieczny** — poprzedni mierzył `W_early` **surowe**, a W2 wymaga
`W_early_red`. Poprzedni pilot nie jest stratą: **230 przebiegów wykryło błąd projektu, który
uniemożliwiłby cały eksperyment.** Jego artefakty pozostają w repo jako udokumentowany negatywny
wynik walidacyjny (Aneks 3 §8, D-010 pkt 2).

---

## 8. Lekcja metodologiczna

W ciągu tej fazy wykryto sześć błędów, z których **żaden nie został znaleziony po publikacji**:

`MSE→MAE` · `Energy Efficiency` · bramka ROADMAP · `shock_world` · podłoga analityczna · obcięty gaussian

**Wszystkie mają jedną przyczynę: model uproszczony nie był tym samym, co implementacja.**

Odpowiedź, przyjęta jako zasada (D-017/D-018):

> **Źródłem prawdy jest implementacja, nie jej model matematyczny.**

To rozszerzenie zasady, która obowiązywała już dla danych („liczby z surowego pliku, nie
z przepisania") — teraz także dla **wielkości wyprowadzanych**: liczyć z kodu środowiska, nie
ze wzoru opisującego, co ten kod „powinien" robić.

Wyprowadzanie podłogi przez próbkowanie rzeczywistego generatora **eliminuje tę klasę błędu
konstrukcyjnie** — nie ma idealizacji, która mogłaby się rozjechać z implementacją, bo
wyprowadzenie *używa* implementacji.

---

*Wszystkie liczby zweryfikowane niezależnie na świeżym klonie `15d304e`.
Podłoga `0.09589` porównana z wartością analityczną `0.1784` — różnica potwierdzona jako
systematyczna, nie brzegowa.*
