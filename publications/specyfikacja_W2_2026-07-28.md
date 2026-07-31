# SPECYFIKACJA W2 — Primary Endpoint znormalizowany podłogą nieredukowalną

**Od:** audytor niezależny · **Dla:** CTO
**Data:** 2026-07-28
**Status:** **ZATWIERDZONA** decyzją **D-018** · procedura V-C (Adaptive Validation) wbudowana
**Podstawa:** Aneks 3 · D-011 · **D-015 (zmieniona przez D-018: wyprowadzenie numeryczne)** · D-012 · **D-017** · **D-018**

> **D-011 wymaga trzech rzeczy przed wejściem do baseline:** (1) formalna specyfikacja
> matematyczna, (2) niezależna weryfikacja implementacji, (3) jawna procedura dla małego
> mianownika. Ten dokument dostarcza (1) i (3); (2) jest zadaniem wykonawczym po zatwierdzeniu.

---

## 1. Ustalenie blokujące (D-011 pkt 3) — rozstrzygnięte

**Pytanie CTO:** *czy L1.2 opisuje scenariusz eksperymentalny, czy konkretną dynamikę świata?*

**Odpowiedź (zweryfikowana w kodzie, `clos_academy/lesson_L1_2.py`):** L1.2 opisuje **protokół**.
Docstring modułu stwierdza wprost, że `t_shock`/`pre_shock_in_band` są liczone dla **właściwości
scenariusza, nie dla nazwy** `shock_world`, oraz że w `stable_world` liczona jest bazowa
stabilność, **a nie** `recovery_time`. Lekcja obsługuje też `weak_shock_world`
i `long_stable_shock_world`.

**Wniosek: nowa lekcja nie jest potrzebna.** L1.2 uruchomiona w środowisku stacjonarnym jest
architektonicznie wspierana i degraduje się poprawnie (pomija metryki wstrząsowe).

**Zalecenie zgodne z D-012:** konfigurację PC-001 nazwać odrębnie — *protokół L1.2 · środowisko
`noise_world` · hipoteza PC · endpoint W2* — żeby wynik nie był czytany jako „shock recovery".

---

## 2. Definicja formalna W2

### 2.1 Podłoga nieredukowalna — procedura V-C (Adaptive Validation, D-018)

**Podłoga NIE jest wyprowadzana analitycznie.** Generator obcina wyjście do `[0,1]`
(`clos_world/generators.py:20`), więc rozkład wyjściowy jest **normalnym uciętym** — wzór
`σ√(2/π)` opisywałby rozkład, którego środowisko nie produkuje (D-017 krok 3).

**Podłoga jest wyprowadzana NUMERYCZNIE z faktycznego generatora** (D-015 zmieniona przez D-018):

```
Dla ticka t, N realizacji szumu z rzeczywistego generatora:
  s_i(t) = env(t, seed_i)                    i = 1..N
  m(t)   = mean{ s_i(t) }                    ← predykcja optymalna
  floor(t) = mean{ |s_i(t) − m(t)| }         ← oczekiwany błąd predyktora optymalnego
```

**`N = 100 000`** — wyprowadzone z kryterium precyzji `SE(floor) < 0.001` (= 5% `MIN_DENOMINATOR`),
nie wybrane arbitralnie. Patrz `ANALIZA_FLOOR_ENV_vs_FLOOR_T.md` §6.

### 2.1a Test ważności V-C — MECHANICZNY, nie decyzja użytkownika (D-018 pkt 6)

Przed eksperymentem, **na samym generatorze środowiska** (bez mózgu, bez danych eksperymentalnych):

```
floor_env      = mean{ floor(t) : t ∈ całe mierzalne okno }
bias_early     = mean{ floor(t) : t ∈ W_early } − floor_env
bias_late      = mean{ floor(t) : t ∈ W_late  } − floor_env
bias_roznicowy = | bias_early − bias_late |
```

**Reguła decyzyjna — wykonywana automatycznie, bez udziału operatora:**

| Warunek | Decyzja mechaniczna | Zapis w artefaktach |
|---|---|---|
| `bias_roznicowy < FLOOR_BIAS_TOLERANCE` | użyj **stałej `floor_env`** | `"floor_model": "constant"`, wartość `floor_env`, wartość `bias_roznicowy` |
| `bias_roznicowy ≥ FLOOR_BIAS_TOLERANCE` | **automatycznie użyj `floor(t)`** + **OSTRZEŻENIE** | `"floor_model": "per_tick"`, `"warning": "bias exceeds tolerance"`, profil `floor(t)` |

**`FLOOR_BIAS_TOLERANCE = 0.002`** — **parametr prerejestrowany PC-001, NIE globalna stała CLOS**
(D-018 pkt 3). W przyszłych eksperymentach może być inny; wymaga wtedy własnej prerejestracji.

**Uzasadnienie warunku** (`ANALIZA_FLOOR_ENV_vs_FLOOR_T.md` §3): dla środowiska stacjonarnego
i okresowego średnia `floor(t)` po pełnym okresie jest stała. Jeśli okna obejmują całkowitą liczbę
okresów, obciążenie jest w obu identyczne i stała wystarcza. **Jeśli nie — różnica obciążeń wchodzi
wprost do licznika `W_early_red − W_late_red` i udaje efekt albo go maskuje.**

**Decyzja MUSI być mechaniczna** (D-018 pkt 6). Operator nie wybiera modelu podłogi — wybiera go
test. Wybór jest zapisywany w artefaktach eksperymentu wraz z wartością `bias_roznicowy`,
żeby recenzent widział, na jakiej podstawie zapadł.

**Model pomiarowy nie zmienia się** przy przejściu na `floor(t)` — endpoint pozostaje „redukcja
błędu redukowalnego"; zmienia się wyłącznie precyzja wyznaczenia odjemnika.

### 2.2 Błąd redukowalny

```
PE_red(t) = max(0, PE(t) − floor_env)
```

Obcięcie do zera jest konieczne: pojedyncza realizacja szumu może dać `PE(t) < floor_env`,
co nie oznacza „lepiej niż optymalnie", tylko fluktuację.

### 2.3 Endpoint

```
W_early_red = mean{ PE_red(t) : t ∈ okno wczesne }
W_late_red  = mean{ PE_red(t) : t ∈ okno późne  }

redukcja_W2 = (W_early_red − W_late_red) / W_early_red
```

**Warunek A** (kierunek): regresja `PE_red(t)` po całym mierzalnym oknie, `β < 0`, istotne.
**Warunek B** (wielkość): `redukcja_W2 ≥ 0.20`.

**Interpretacja:** *jaką część tego, co **dało się** nauczyć, system faktycznie nauczył.*
Szum jest z definicji poza licznikiem, więc miara jest **porównywalna między środowiskami** —
20% znaczy to samo przy podłodze 0 i przy 0.25.

---

## 3. Procedura dla małego mianownika (D-011 pkt 1, warunek 3)

`redukcja_W2` jest niestabilna, gdy `W_early_red → 0` — czyli gdy system **od początku**
przewiduje na poziomie bliskim optymalnemu i nie ma czego redukować.

### 3.1 Próg minimalnego mianownika

```
MIN_DENOMINATOR = 0.02
```

**Uzasadnienie wartości:** to ≈ 11% najmniejszej niezerowej podłogi w zestawie
(`shock_world` po wstrząsie, 0.1128) i ≈ 8% podłogi `pure_noise_world`. Poniżej tego poziomu
`W_early_red` jest tego samego rzędu co fluktuacja próbkowania w oknie 60 ticków.
**Wartość jest konwencją przyjętą z góry**, jak próg 20% — jej wartością jest niezmienność,
nie optymalność.

### 3.2 Obsługa

| Warunek | Klasyfikacja przebiegu | Traktowanie |
|---|---|---|
| `W_early_red ≥ MIN_DENOMINATOR` | **VALID** | wchodzi do analizy |
| `W_early_red < MIN_DENOMINATOR` | **FLOOR_LIMITED** | **wykluczony z testu Warunku B**, ale **raportowany** |

**FLOOR_LIMITED nie jest brakiem danych — jest wynikiem.** Oznacza: *system od początku
przewidywał na poziomie bliskim optymalnemu; nie było czego redukować.*

### 3.3 Bezpiecznik przeciw skażeniu doborem próby

> Jeśli **> 30% przebiegów** w komórce jest `FLOOR_LIMITED`, komórka jest klasyfikowana jako
> **INCONCLUSIVE** — niezależnie od wyniku pozostałych przebiegów.

**Powód:** przy dużym odsetku wykluczeń test działałby na **podzbiorze wybranym ze względu
na wysoki błąd początkowy**, czyli na próbie z regresją do średniej wbudowaną w kryterium doboru.
To dałoby fałszywy pozytyw.

Próg 30% — konwencja przyjęta z góry.

### 3.4 Warunek A a FLOOR_LIMITED

Warunek A (`β < 0`) **jest liczony także dla przebiegów FLOOR_LIMITED** — nachylenie nie ma
mianownika, więc nie jest niestabilne. Raportowane osobno dla obu grup.

---

## 4. Wymagania weryfikacyjne (D-011 pkt 1, warunek 2)

Implementacja **nie może wejść do baseline** przed spełnieniem wszystkich:

| # | Test | Co wykrywa |
|---|---|---|
| 1 | `floor_env` policzona **niezależnie** przez audytora z definicji scenariusza, zgodna do 1e-6 | błąd w wyprowadzeniu podłogi |
| 2 | **Test negatywny:** podłoga celowo zawyżona → wszystkie przebiegi `FLOOR_LIMITED` | czy próg działa |
| 3 | **Test negatywny:** podłoga celowo wyzerowana → W2 redukuje się do W1 (surowe PE) | czy normalizacja jest realnie stosowana |
| 4 | **Symulacja:** predyktor idealny (zwraca warunkową średnią) → `PE_red ≈ 0`, `redukcja` nieokreślona → `FLOOR_LIMITED` | czy podłoga jest poprawna |
| 5 | **Symulacja:** predyktor stały (0.5) → brak redukcji | czy miara nie generuje efektu z niczego |
| 6 | Przypadki brzegowe: `W_early_red = 0` dokładnie, wszystkie `PE(t) < floor_env` | dzielenie przez zero, obcięcie |
| **W2-T7** | **Test mechanizmu V-C (D-018 pkt 6):** dla środowiska referencyjnego policz `floor_env` i `floor(t)`, wykonaj test ważności. Sprawdź: (a) przy `bias < tolerancja` → wybrana stała; (b) przy sztucznie zawyżonym `bias` → **automatyczne** przejście na `floor(t)` + ostrzeżenie + zapis decyzji w artefaktach; (c) decyzja **nie jest** konfigurowalna przez operatora | czy V-C jest mechaniczne, a nie deklaratywne |

**Test 3 jest kluczowy:** implementacja, która pobiera `floor_env`, ale jej nie odejmuje,
przechodziłaby wszystkie testy „pozytywne" i dawała wyniki W1 pod nazwą W2. To ten sam wzorzec,
co alias `comparison` w P0 — kod wyglądający na działający, niechroniący niczego.

**W2-T7 punkt (c) jest równie ważny:** jeśli model podłogi da się ustawić parametrem, to V-C jest
sugestią, nie mechanizmem — i pierwszy niewygodny wynik zostanie „naprawiony" przełącznikiem.
Test musi wykazać, że **nie istnieje ścieżka, w której operator wybiera model podłogi.**

---

## 5. Wpływ na kontrole K1–K7

Wszystkie kontrole operują teraz na `PE_red`, nie na surowym `PE`:

| Kontrola | Zmiana |
|---|---|
| **K1** (przetasowanie) | bez zmian koncepcyjnych; liczona na `PE_red` |
| **K3a/K3b** (wstrząs) | **bez zmian** — `shock_world` pozostaje środowiskiem K3, gdzie mierzy się adaptację, nie uczenie struktury |
| **K4** (czysty szum) | **wzmocniona**: w `pure_noise_world` `PE_red ≈ 0` z definicji (brak struktury) → wszystkie przebiegi `FLOOR_LIMITED` → **brak efektu jest strukturalnie gwarantowany**, nie tylko empirycznie |
| **K5** (ablacja) | bez zmian koncepcyjnych; liczona na `PE_red` |
| **K6** (korelacja) | **bez zmian** — operuje na `prediction`/`input`, nie na PE |
| **K7** (gałąź awaryjna) | bez zmian |

> **Uwaga do K4:** przy W2 kontrola staje się częściowo tautologiczna — w środowisku bez struktury
> nie ma czego redukować **z definicji**. To **wzmacnia** kontrolę (gwarancja strukturalna zamiast
> empirycznej), ale musi być tak opisane w raporcie, żeby nie prezentować tautologii jako wyniku.

---

## 6. Czego ta specyfikacja NIE rozstrzyga

- **Okien pomiarowych** — wynikają z wyboru środowiska Primary, nie odwrotnie.
- **Progu 20%** — pozostaje konwencją (Aneks 1, Zmiana 4), stosowaną teraz do `redukcja_W2`.
- **Liczby seedów** — wynika z ponownej analizy mocy po zatwierdzeniu W2.
- **Ponownego pilota** — konieczny, bo poprzedni mierzył `W_early` surowe, nie `W_early_red`.

---

## 7. Do rozstrzygnięcia przez CTO

1. **`MIN_DENOMINATOR = 0.02`** — akceptujesz wartość i uzasadnienie, czy chcesz inną?
2. **Próg 30% FLOOR_LIMITED → INCONCLUSIVE** — akceptujesz?
3. **Środowisko Primary:** `noise_world` (istniejące, `floor = 0.1784`) — potwierdzasz?
4. **Nazwa konfiguracji** zgodna z D-012 — czy wprowadzamy jawną warstwę „konfiguracja
   eksperymentu" (lekcja × środowisko × hipoteza × endpoint) jako osobny artefakt w repo?

---

*Podłogi wyprowadzone z `E|N(0,σ²)| = σ√(2/π)`, wartości `σ²` odczytane z `clos_world/scenarios.py`.
Wymagają niezależnego przeliczenia przed zamrożeniem (wymaganie weryfikacyjne nr 1).*

*KOREKTA 2026-07-28 (D-017/D-018): wymaganie weryfikacyjne nr 1 wykonane — wartości
powyżej są oszacowaniem analitycznym przy założeniu nieobciętego rozkładu normalnego;
założenie fałszywe (obcięcie do `[0,1]`, `generators.py:20`). Wyznaczenie numeryczne
(procedura V-C) dało dla `noise_world` `floor_env = 0.09589`, ~53% wartości
analitycznej 0.178. Obowiązują wyłącznie wartości z `clos_world/floor_model.py`.*
