# ANALIZA METODOLOGICZNA — `floor_env` (stała) vs `floor(t)` (funkcja ticka)

**Od:** audytor niezależny · **Dla:** CTO
**Data:** 2026-07-28
**Status:** PROJEKT · **Hard Halt w mocy**
**Podstawa:** D-015 (zmieniona: wyprowadzenie numeryczne dopuszczalne) · **D-017** (walidacja modelu środowiska)

> **Zadanie:** CTO nie zatwierdził przejścia z `floor_env` na `floor(t)`, wskazując, że to zmiana
> **modelu pomiarowego**, nie sposobu obliczania. Wymagana analiza: konsekwencje statystyczne,
> dodatkowa wariancja, interpretowalność.

---

## 1. Korekta językowa

Poprzednie sformułowanie audytora: *„`E|N(0,σ²)| = σ√(2/π)` nie obowiązuje"*.

**Precyzyjniej:** wzór jest poprawny dla nieobciętego rozkładu normalnego. **Nie opisuje jednak
oczekiwanego błędu generatora używanego przez środowiska CLOS**, ponieważ
`clos_world/generators.py:20` obcina wyjście do `[0,1]`, więc rozkład wyjściowy jest
**normalnym uciętym**, nie normalnym.

To nie jest błąd wzoru. To błąd **zastosowania wzoru do niewłaściwego rozkładu** — dokładnie
klasa ukrytego założenia, którą D-017 ma odtąd wykrywać.

---

## 2. Na czym polega różnica

Obcięcie bije **tylko wtedy, gdy sygnał leży blisko krańca zakresu.** W środowisku
oscylacyjnym (`noise_world` = sinus + szum) sygnał wędruje, więc:

| Położenie sygnału | Efekt obcięcia | Lokalna podłoga |
|---|---|---|
| środek zakresu (≈0.5) | znikomy | ≈ `σ√(2/π)` (pełna) |
| blisko 0 lub 1 | silny | **istotnie niższa** |

**Wniosek:** `floor` jest funkcją położenia sygnału, a więc — w środowisku okresowym — **funkcją
okresową ticka.**

---

## 3. Kluczowa obserwacja: kiedy stała wystarcza

> **Dla środowiska stacjonarnego i okresowego średnia `floor(t)` po pełnym okresie jest stała.**

Jeśli okna pomiarowe `W_early` i `W_late` obejmują **całkowitą liczbę okresów sygnału**, to:

```
mean{ floor(t) : t ∈ W_early } = mean{ floor(t) : t ∈ W_late } = floor_okres
```

— i **stała wystarcza**, bo obciążenie jest identyczne w obu oknach.

Jeśli okna są **niedopasowane do okresu**, powstaje **różnica obciążeń** między oknami, która
wchodzi wprost do licznika `W_early_red − W_late_red` — czyli **udaje efekt albo go maskuje**.

**To przekształca decyzję z preferencji w warunek sprawdzalny.**

---

## 4. Trzy warianty

### V-A: `floor_env` = stała (średnia po okresie)

| | |
|---|---|
| **Warunek ważności** | środowisko stacjonarne **oraz** okna obejmujące całkowitą liczbę okresów |
| **Interpretowalność** | najwyższa — jedna liczba na środowisko, porównywalna, cytowalna |
| **Wariancja dodatkowa** | minimalna: jedna wartość, błąd MC ≈ `σ/√(N·T)` |
| **Walidacja** | prosta — jedna liczba do niezależnego przeliczenia |
| **Ryzyko** | **obciążenie różnicowe przy niedopasowaniu okien do okresu** |

### V-B: `floor(t)` = funkcja ticka

| | |
|---|---|
| **Warunek ważności** | zawsze poprawna |
| **Interpretowalność** | niższa — „redukcja błędu redukowalnego" nadal sensowna, ale podłoga przestaje być liczbą do zacytowania |
| **Wariancja dodatkowa** | błąd MC na tick ≈ `σ/√N`, **ale uśredniony po oknie 60 ticków maleje ≈ √60 ≈ 7,7×** → wpływ na `W_early_red`/`W_late_red` **niewielki** |
| **Walidacja** | trudniejsza — `T` wartości zamiast jednej; wymaga testu na profilu podłogi, nie na liczbie |
| **Ryzyko** | złożoność; więcej miejsc na błąd implementacji |

### V-C (rekomendowany): `floor_env` **z prerejestrowanym warunkiem ważności**

> Używamy **stałej** `floor_env` (średniej po okresie), **ale prerejestrujemy sprawdzenie**,
> że warunek z §3 jest spełniony. Jeśli nie jest — **automatyczne przejście na `floor(t)`.**

**Warunek prerejestrowany:**

```
|mean{floor(t) : t ∈ W_early} − mean{floor(t) : t ∈ W_late}| < FLOOR_BIAS_TOLERANCE
```

gdzie `FLOOR_BIAS_TOLERANCE` = **0.002** (10% wartości `MIN_DENOMINATOR = 0.02`).

Sprawdzenie wykonywane **na samym generatorze środowiska**, przed eksperymentem — bez żadnych
danych z mózgu.

| | |
|---|---|
| **Interpretowalność** | jak V-A (jedna liczba), dopóki warunek spełniony |
| **Poprawność** | jak V-B (spadek na `floor(t)`, gdy warunek zawiedzie) |
| **Model pomiarowy** | **nie zmienia się** — endpoint pozostaje „redukcja błędu redukowalnego"; zmienia się tylko dokładność wyznaczenia podłogi |
| **Decyzja** | **oparta na dowodzie, nie na preferencji** |

---

## 5. Odpowiedzi na trzy pytania CTO

**Konsekwencje statystyczne.** Przy V-C żadne — dopóki warunek spełniony, model jest identyczny
z V-A. Przy przejściu na `floor(t)` model pozostaje ten sam; zmienia się jedynie precyzja
odjemnika.

**Dodatkowa wariancja.** Przy `floor(t)` błąd MC na tick propaguje do `PE_red(t)`, ale **uśrednienie
po oknie 60 ticków redukuje go ≈ 7,7-krotnie**. Przy `N` dobranym wg §6 wpływ jest o rząd wielkości
poniżej `MIN_DENOMINATOR`. **Nie jest to źródło istotnej wariancji.**

**Interpretowalność.** Zachowana w V-C. Raportujemy `floor_env` jako liczbę **plus** wynik
sprawdzenia warunku ważności. Jeśli warunek zawiedzie, raportujemy to jawnie wraz z profilem
`floor(t)` — czytelnik widzi, dlaczego użyto wersji złożonej.

---

## 6. Liczba realizacji `N` — wyprowadzona z kryterium, nie wybrana (D-015 pkt 3)

**Kryterium:** błąd Monte Carlo wyznaczenia podłogi ma być **poniżej 5% `MIN_DENOMINATOR`**:

```
SE(floor) < 0.05 · 0.02 = 0.001
```

Dla estymatora średniej z `N` realizacji: `SE ≈ σ_eff / √N`, gdzie `σ_eff ≤ σ` (obcięcie zmniejsza
rozrzut, więc `σ` jest oszacowaniem konserwatywnym).

| Środowisko | `σ` (górne oszacowanie) | **wymagane `N`** |
|---|---|---|
| `noise_world` | 0.224 | ≈ **50 000** |
| `pure_noise_world` | 0.316 | ≈ **100 000** |
| `shock_world` (po) | 0.141 | ≈ **20 000** |

> **`N = 100 000` na tick** pokrywa najostrzejszy przypadek z zapasem.
> Wartość **wynika z kryterium precyzji**, nie z wyboru „na oko" — zgodnie z uwagą CTO.

Kryterium `SE < 0.001` i współczynnik 5% są **konwencjami przyjętymi z góry**, jak próg 20%
i `MIN_DENOMINATOR` — ich wartością jest niezmienność.

> **KOREKTA 2026-07-28 (D-017/D-018), dla jasności:** `σ` w tabeli powyżej jest
> używane WYŁĄCZNIE jako konserwatywne górne oszacowanie do wzoru na `N` — nie
> jako wartość podłogi (to jest właśnie teza całego tego dokumentu: podłoga
> wymaga wyznaczenia numerycznego, nie analitycznego). Wykonanie dla `noise_world`
> potwierdziło poprawność tego użycia: `N=100 000` dało `floor_env=0.09589` ze
> stabilnym, powtarzalnym wynikiem (procedura V-C wybrała model `constant`,
> `bias_roznicowy` ~83× poniżej tolerancji) — sam `σ=0.224` NIGDY nie wszedł do
> obliczenia wartości podłogi, tylko do doboru `N`.

---

## 7. Wykonanie D-017 dla podłogi

| Krok D-017 | Realizacja |
|---|---|
| 1. Weryfikacja matematyczna modelu | wzór dla normalnego uciętego **nie jest wyprowadzany analitycznie** — model to „oczekiwany błąd bezwzględny optymalnego predyktora", wyznaczany numerycznie |
| 2. Weryfikacja implementacji generatora | **wykonana:** `rng.gauss(mean, √variance)` → parametr `variance` **jest** wariancją; `max(0, min(1, raw))` → **obcięcie potwierdzone** |
| 3. Potwierdzenie, że implementacja zachowuje założenia wyprowadzenia | **to jest krok, który zawiódł.** Odtąd: wyprowadzenie **korzysta z faktycznego generatora**, nie z jego idealizacji — więc krok 3 jest spełniony **konstrukcyjnie** |

**Wniosek:** wyprowadzanie podłogi przez **próbkowanie rzeczywistego generatora** eliminuje całą
klasę błędu z D-017 — nie ma idealizacji, która mogłaby się rozjechać z implementacją.

---

## 8. Do rozstrzygnięcia przez CTO

1. **Czy przyjmujesz V-C** (stała + prerejestrowany warunek ważności + automatyczne przejście
   na `floor(t)`, gdy warunek zawiedzie)?
2. **`FLOOR_BIAS_TOLERANCE = 0.002`** (10% `MIN_DENOMINATOR`) — akceptujesz?
3. **`N = 100 000`** wyprowadzone z `SE < 0.001` — akceptujesz kryterium i wartość?
4. Czy analiza spełnia wymóg „osobnego dokumentu metodologicznego" przed zdjęciem blokady
   z `floor(t)`?

---

*Wartości `σ` odczytane z `clos_world/scenarios.py`; obcięcie potwierdzone
w `clos_world/generators.py:20`. Warunek ważności z §3 wymaga sprawdzenia okresu sygnału
`noise_world` względem długości okien — do wykonania przy implementacji.*
