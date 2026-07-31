# NOTATKA B4 — projekt analizy mocy dla PC-001

**Od:** audytor niezależny
**Dla:** CTO
**Data:** 2026-07-28
**Status:** **ZATWIERDZONA** decyzją **CTO D-008** · uzupełnienia D-008 pkt 2–4 naniesione
**Podstawa:** PC-001 §11 pkt 4 (analiza mocy obowiązkowa) · D-005 pkt 3 · D-008

---

## 1. Problem: analiza mocy dla testów nieparametrycznych nie ma postaci zamkniętej

Istniejące `power_two_sample_t_test`, `power_anova`, `minimum_detectable_effect`
(`clos_curriculum/laboratory/statistics.py`) są **parametryczne**. Nie stosują się do Wilcoxona,
Kendalla tau ani Manna-Whitneya, które PC-001 wykorzystuje w 9-warunkowej regule decyzyjnej.

Standardowa droga to **symulacja Monte Carlo**, ale ona wymaga znajomości **rozkładu** wielkości
mierzonej — a rozkładu `prediction_error` w tej architekturze **nie znamy**.

Stąd potrzeba pilota.

---

## 2. KRYTYCZNA POPRAWKA do planu pilota — ryzyko mocy retrospektywnej

> **Plan w pierwotnej formie odtwarzałby błąd, który projekt wcześniej świadomie usunął.**

CLOS usunął moc retrospektywną (`power_n10`) z uzasadnień statusu, bo **moc liczona z
zaobserwowanego efektu jest funkcją tego efektu** — rozumowanie jest cyrkularne. Recenzja
zewnętrzna wskazała to jako jedną z najmocniejszych stron projektu.

**Jeśli weźmiemy wielkość efektu z pilota i policzymy z niej moc, popełnimy dokładnie ten sam błąd**
— tylko przesunięty o jeden krok wcześniej w czasie.

### Rozdzielenie, które to naprawia

| Parametr | Skąd pochodzi | Uzasadnienie |
|---|---|---|
| **Wielkość efektu do wykrycia** | **20% — z prerejestracji, NIE z pilota** | To jest **minimalny efekt istotny**, ustalony z góry (Aneks 1, Zmiana 4). Pytanie brzmi „ile przebiegów potrzeba, by wykryć efekt 20%", nie „jaki efekt widzimy" |
| **Rozkład i wariancja** (parametry uciążliwe) | **z pilota** | Nie da się ich założyć bez zgadywania; są **niezależne od hipotezy** |

**Pilot dostarcza wyłącznie parametrów uciążliwych. Nigdy wielkości efektu.**

### Wzmocnienie: pilot nie może zobaczyć efektu

Aby ryzyko skażenia było **mechaniczne, nie tylko deklaratywne**:

> **Z pilota odczytujemy WYŁĄCZNIE rozkład `W_early`** (średnia PE w pierwszych 20% ticków) —
> czyli zmienność **na starcie przebiegu**.
>
> **NIE odczytujemy:** `W_late`, trajektorii PE, nachylenia `β`, ani żadnej wielkości mówiącej,
> **czy** PE spada.

Efekt alternatywny w symulacji jest **syntetyczny**: bierzemy rozkład `W_early` z pilota
i stosujemy do niego **prerejestrowaną redukcję 20%**, generując `W_late` sztucznie.

**Skutek:** po pilocie nadal **nie wiemy**, czy PE w tym systemie spada. Wiemy tylko, jak bardzo
jest zmienne na starcie. To eliminuje skażenie niemal całkowicie — nie przez dyscyplinę, tylko
przez **konstrukcję**.

---

## 3. Projekt pilota

| Parametr | Wartość | Uzasadnienie |
|---|---|---|
| Genomy | 23 (pełny zestaw) | zmienność międzygenomowa jest głównym źródłem wariancji |
| Środowiska | `shock_world`, `pure_noise_world` | dwa środowiska inferencyjne; `stable_world` poza inferencją (D-005 pkt 4) |
| Seedy | **5 na genom — WARTOŚĆ POCZĄTKOWA, nie zamrożona** (D-008 pkt 2) | 115 przebiegów na środowisko. Jeśli rozkład okaże się niestabilny (duża wariancja oszacowania wariancji, nieregularny kształt), **liczba seedów musi zostać zwiększona przed B4b** — decyzja podejmowana po obejrzeniu rozkładu `W_early`, co jest dopuszczalne, bo `W_early` nie niesie informacji o efekcie |
| Lekcja | L1.2 (Primary) | L1.1 wspierająca, pilot jej nie obejmuje |
| **Odczytywane** | **wyłącznie `W_early` per przebieg** | patrz §2 |

### Rozdzielność seedów — warunek mechaniczny

> **Seedy pilota MUSZĄ być rozłączne z seedami eksperymentu konfirmacyjnego.**
> Pilot używa seedów `1–5`; eksperyment konfirmacyjny **zaczyna od seeda 1001**.
>
> Bez tego te same przebiegi weszłyby do obu zbiorów — pilot skaziłby konfirmację **dosłownie**,
> nie tylko interpretacyjnie.

### Zapis i oznaczenie

- Plik: `reports/pilot/pilot_PE_distribution_W_early.json`
- Pole obowiązkowe: `"purpose": "power_analysis_only"`
- Pole obowiązkowe: `"NEVER_FOR_INFERENCE": true`
- Pole obowiązkowe: `"seeds_used": [1,2,3,4,5]` — do weryfikacji rozłączności
- **Zapisujemy wyłącznie `W_early`** — nie pełne trajektorie. Czego nie ma w pliku,
  tego nie da się później podejrzeć.

---

## 4. Procedura Monte Carlo (B4)

1. **Rozkład bazowy:** empiryczny rozkład `W_early` z pilota (per genom, per środowisko).
2. **Hipoteza zerowa:** `W_late` losowane z tego samego rozkładu (brak redukcji).
3. **Hipoteza alternatywna:** `W_late = W_early × 0.80` (prerejestrowana redukcja 20%) plus szum
   o wariancji z pilota.
4. **Dla każdego kandydata `n` seedów:** wygeneruj `N_sim = 10 000` zestawów, uruchom **rzeczywisty
   kod testu** z `statistics.py` (nie przybliżenie), policz odsetek odrzuceń.
5. **Moc = odsetek odrzuceń pod alternatywą.** Szukamy najmniejszego `n`, dla którego
   **moc ≥ 0.80** przy `α = 0.05` po korekcie BH-FDR.
6. **Powtórz dla każdego testu z reguły decyzyjnej**, nie tylko dla warunku B:
   - warunek A (trend `β`), warunek B (Wilcoxon),
   - **K3b-1** (Kendall tau na `recovery_i` — uwaga: ≈7 punktów na przebieg, moc będzie niska),
   - **K4** (Mann-Whitney, separacja),
   - **K6** (Spearman).
7. **Liczba seedów = maksimum z wymagań wszystkich testów.** Nie średnia, nie mediana —
   najsłabszy test wyznacza `n`.

**Kod symulacji wchodzi do `CRITICAL_FILES_PC_001`** (lista rośnie z 30), baseline liczony po B4.

### 4a. Walidacja samego symulatora — OBOWIĄZKOWA (D-008 pkt 3)

> **Można mieć poprawny eksperyment i błędny symulator.** Symulator mocy musi przejść własną
> walidację, zanim jego wyniki zostaną użyte do doboru `n`.

To jest ten sam wzorzec, który w tym projekcie zadziałał już pięciokrotnie: walidator bez testu
negatywnego jest dekoracją. **Symulator, który zawsze zwraca wysoką moc, wygląda tak samo jak
symulator poprawny — dopóki nie sprawdzi się go na znanych przypadkach.**

**Wymagane testy symulatora:**

| # | Warunek | Oczekiwany wynik | Co wykrywa |
|---|---|---|---|
| 1 | **Hipoteza zerowa** — `W_late` z tego samego rozkładu co `W_early`, zero efektu | **moc ≈ α = 0.05** (tolerancja: przedział ufności dla `N_sim`) | symulator zawyżający moc; błąd w kierunku testu |
| 2 | **Efekt bardzo duży** — redukcja 80% | **moc → blisko 1.0** | symulator zaniżający moc; błąd w podawaniu danych do testu |
| 3 | **Monotoniczność** — moc rośnie wraz z `n` przy stałym efekcie | rosnąca | błąd w agregacji lub w pętli symulacji |
| 4 | **Monotoniczność** — moc rośnie wraz z wielkością efektu przy stałym `n` | rosnąca | błąd w generowaniu alternatywy |

**Test 1 jest kluczowy:** symulator, który pod hipotezą zerową daje moc istotnie wyższą niż `α`,
**zawyża moc systematycznie** — a to prowadziłoby do wybrania za małego `n`, czyli do powtórzenia
P0 mimo formalnie wykonanej analizy mocy.

Testy symulatora **wchodzą do pakietu testów** i muszą przechodzić przed uruchomieniem B4b.

---

## 5. Kryteria akceptacji pilota — i co, jeśli nie przejdzie

| Sytuacja | Działanie |
|---|---|
| Rozkład `W_early` jednomodalny, bez ekstremalnych outlierów | → B4 normalnie |
| Rozkład **multimodalny** (np. genomy dzielą się na grupy) | → **decyzja CTO**: czy stratyfikować symulację per grupa, czy przyjąć rozkład mieszany |
| **Ekstremalne outliery** (część genomów z PE rzędu wielokrotności mediany) | → **decyzja CTO**: czy testy rangowe są odporne (prawdopodobnie tak — to ich zaleta), czy wykluczyć genomy z uzasadnieniem **przed** konfirmacją |
| `W_early ≈ 0` dla części genomów | → **problem podłogi (T4)** ujawniony wcześnie; redukcja procentowa niezdefiniowana. **Decyzja CTO** przed konfirmacją |

**Ostatni wiersz jest istotny:** jeśli `W_early` jest bliskie zeru, to `(W_early − W_late)/W_early`
jest numerycznie niestabilne albo niezdefiniowane. Lepiej wykryć to na 115 przebiegach niż na
pełnym eksperymencie.

---

## 6. Co, jeśli analiza mocy wymaga niewykonalnej liczby przebiegów

Realne ryzyko: **K3b-1 (Kendall tau na ≈7 punktach `recovery_i`)** ma z natury niską moc.
Może się okazać, że wykrycie trendu wymaga liczby seedów przekraczającej możliwości obliczeniowe.

**To NIE jest powód do obniżenia progu ani usunięcia K3b.**

**DECYZJA CTO (D-008 pkt 4): priorytetem jest PRZEPROJEKTOWANIE eksperymentu, opcja 1.**
CTO nie akceptuje świadomego uruchomienia eksperymentu z kontrolą, o której z góry wiadomo,
że nie będzie rozstrzygalna.

Kolejność wiążąca:

1. **Zwiększyć liczbę wstrząsów na przebieg** — dłuższy przebieg albo krótszy `interval`.
   To zmiana **projektu eksperymentu**, nie kryteriów — wymaga aneksu **przed** uruchomieniem.
   **← wybór CTO, stosowany jako pierwszy**
2. Zaakceptować niższą moc dla K3b z jawnym zapisem, że wynik negatywny K3b będzie
   **nieinterpretowalny** (a nie „PC odrzucone"). **← dopiero gdy 1 nie wystarczy**
3. Uznać PC-001 za niewykonalny w obecnym projekcie i przeprojektować w PC-002.
   **← ostateczność**

**Niedopuszczalne:** obniżenie progu 20%, usunięcie kontroli, uruchomienie mimo niedostatecznej
mocy z nadzieją, że wyjdzie. To byłoby powtórzenie P0.

---

## 7. Kolejność wykonania

| Krok | Zawartość | Bramka |
|---|---|---|
| **B4a** | Pilot: 230 przebiegów (23 genomy × 5 seedów × 2 środowiska), zapis **wyłącznie `W_early`** | audyt: czy zapisano tylko `W_early`, czy seedy rozłączne |
| **B4b** | Monte Carlo → `publications/power_analysis_PC_001.json` | audyt: czy efekt 20% pochodzi z prerejestracji, nie z pilota |
| **B5** | `PC_001_BASELINE` — cały pipeline istnieje | niezależne przeliczenie przez audytora |
| **B6** | Bramka wejścia | wszystkie wymagania §11 + Aneksy |
| **Start** | Eksperyment konfirmacyjny, seedy **od 1001** | — |

---

## 8. Pytania do rozstrzygnięcia przez CTO

1. **Czy akceptujesz ograniczenie pilota do `W_early`?** To główna poprawka tej notatki —
   kosztuje trochę precyzji symulacji (nie znamy wariancji `W_late`), ale eliminuje skażenie
   konstrukcyjnie, nie deklaratywnie.
2. **Czy 5 seedów na genom wystarczy** do oszacowania wariancji, czy chcesz więcej?
   (Więcej = lepsze oszacowanie, ale też większy fragment przestrzeni seedów zużyty.)
3. **Seedy pilota 1–5, konfirmacja od 1001** — akceptujesz rozdzielność?
4. **Co, jeśli K3b okaże się niewykonalny mocowo** — która z trzech reakcji z §6?

---

*Notatka opiera się na zweryfikowanym stanie kodu: `statistics.py` zawiera testy parametryczne
mocy (`power_two_sample_t_test`, `power_anova`, `minimum_detectable_effect`) niestosujące się
do testów rangowych; `recurring_shock_world` ma `interval = 40`, co przy 300 tickach daje ≈7
wstrząsów na przebieg.*
