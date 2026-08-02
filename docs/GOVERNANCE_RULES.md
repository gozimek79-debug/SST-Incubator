# Governance Rules — wiążące zasady procesowe

**Status: WIĄŻĄCE.** Nie deklaracja intencji — reguły stosowane retroaktywnie do
konkretnych decyzji tego projektu (patrz §5-§6 "Test historyczny").

**Lokalizacja:** to jest **pierwsza formalna definicja** O-001 w tym repo. Do
2026-07-28 O-001 był cytowany w kodzie/komentarzach (`clos_kernel/snapshot_engine.py`,
`execution_package_v0_11/validators/hard_halt.py`, `tests/test_observer_removability.py`
— zawsze jako "D-005 pkt 5, zasada O-001") bez jednego miejsca definiującego treść
zasady. Ten dokument jest tym miejscem — nie zmienia znaczenia O-001 (użycie
w cytowanych plikach jest już z nim zgodne), tylko nadaje mu jeden, cytowalny adres.

---

## O-001 (Observation First)

Jeśli eksperyment wymaga dodatkowych danych do analizy, **preferowana droga to
rozszerzenie Observation Layer, nie modyfikacja Core.**

**Precedens w tym repo:** `Snapshot.prediction_error`/`.prediction`/`.input` (PC KROK 2,
PC-001 B2) — dodane jako pola Observation Layer (`clos_kernel/snapshot_engine.py`),
czytające już istniejący stan `tissue` bez zmiany `clos_brain/`. Test usuwalności
(`tests/test_observer_removability.py`) dowodzi, że `observe=False` odtwarza dokładnie
poprzednią ścieżkę wykonania.

---

## G-001 (Klasyfikacja poprawek metodologicznych)

Każda poprawka metodologiczna zgłoszona w trakcie projektu to **Typ M** albo **Typ I**:

| Typ | Definicja | Traktowanie |
|---|---|---|
| **M — Measurement Failure** | eksperyment **NIE mierzy** hipotezy prerejestrowanej | może wejść do **bieżącego** protokołu |
| **I — Interpretation Improvement** | eksperyment **mierzy** hipotezę, ale da się **lepiej interpretować** | trafia do **następnego** eksperymentu, nie zatrzymuje bieżącego |

### Kryterium Typu M — OBA warunki JEDNOCZEŚNIE

1. **Primary Endpoint nie mierzy hipotezy prerejestrowanej** — nie "mierzy gorzej", nie
   "da się lepiej mierzyć". Chodzi o to, czy wynik testu byłby **taki sam niezależnie od
   prawdziwości hipotezy** (wtedy nie mierzy jej wcale), nie o precyzję pomiaru.
2. **Nie istnieje poprawna interpretacja uzyskanych wyników** — nawet z pełną
   świadomością ograniczenia, nie da się wyciągnąć z wyniku wniosku o hipotezie.

Jeśli **którykolwiek** warunek nie jest spełniony (endpoint mierzy hipotezę, choćby
niedoskonale ALBO istnieje poprawna, choć zawężona interpretacja) — to **Typ I**, nie M.

### Role

- **Audytor** przygotowuje analizę, dowody, ocenę wpływu i rekomendacje.
- **CTO** wydaje decyzję.
- Audytor **nie zatrzymuje** projektu (nie ma takiej władzy procesowej — może tylko
  rekomendować STOP, co i tak wymaga decyzji CTO, patrz precedens B4a).
- CTO **nie wykonuje** analizy (nie zastępuje audytora w dowodzeniu, czy warunki
  Typu M są spełnione).

---

## G-002 (Źródło decyzji)

Źródłem decyzji jest **wpływ na mierzalność hipotezy**, nie liczba znalezionych
ulepszeń.

**Konsekwencja praktyczna:** dziesięć drobnych poprawek Typu I nie sumuje się do
Typu M. Jedna poprawka, która unieważnia Primary Endpoint, jest Typem M, nawet jeśli
jest jedynym znaleziskiem w całym audycie. Liczba nie jest dowodem wagi.

---

## G-003 (Wymagania dla nowej kontroli naukowej)

Każda nowa kontrola naukowa musi dostarczyć **JEDNOCZEŚNIE** sześć rzeczy — brak
któregokolwiek dyskwalifikuje kontrolę do czasu uzupełnienia:

1. **Formalna definicja matematyczna** — wzór, nie opis słowny.
2. **Hipoteza falsyfikowalna** — jasne, co odróżnia wynik potwierdzający od
   obalającego.
3. **Plan analizy mocy** — jak, przed uruchomieniem, ustalić wymaganą liczbę
   przebiegów/seedów.
4. **Dowód, że analiza mocy NIE wymaga ujawnienia wyniku eksperymentu** —
   inaczej analiza mocy sama staje się formą mocy retrospektywnej (ten sam
   błąd co `power_n10`, tylko przesunięty o jeden krok).
5. **Gwarancja mechaniczna chroniąca ślepotę** — konstrukcyjna, nie
   deklaratywna (ten sam standard co pilot B4a/B4a-2: to, czego nie ma w
   pliku, nie da się później podejrzeć).
6. **Klasyfikacja typu danych wymaganych przez analizę mocy** — jedna z
   czterech, wybrana MECHANICZNIE, nie przez ocenę:
   - **dane środowiska** — dostępne zawsze (np. `floor_env` z generatora,
     nie zależy od żadnego przebiegu eksperymentalnego).
   - **dane pilota** — dostępne przed konfirmacją (parametry uciążliwe:
     rozkład, wariancja — nigdy wielkość efektu, patrz D-008 pkt 1).
   - **dane eksperymentalne** — **NIEDOSTĘPNE** przed konfirmacją (są
     wynikiem samego testu, który kontrola ma wykonać).
   - **dane niedopuszczalne przed konfirmacją** — kategoria wprost
     wykluczająca użycie.

**Reguła:** jeśli pkt 6 klasyfikuje wymagane dane jako "dane eksperymentalne",
pkt 4 jest **automatycznie niespełniony** — nie da się zaplanować mocy testu
bez zobaczenia jego własnego wyniku. Punkt 6 istnieje właśnie po to, żeby to
było widoczne z samej klasyfikacji, bez potrzeby osobnej analizy.

---

## G-004 (Ochrona tożsamości badanego systemu)

> Jeżeli wykryta właściwość wynika z implementacji Core i nie jest skutkiem
> błędu pomiarowego ani metodologicznego, **NIE WOLNO** modyfikować Core w
> ramach trwającego eksperymentu wyłącznie w celu uzyskania oczekiwanego
> zachowania. Taka modyfikacja tworzy **NOWĄ WERSJĘ** badanego systemu i
> wymaga nowego programu badawczego (PC-002 lub CLOS v0.12).

**Precedens, który uzasadnił tę zasadę:** K3b/W-01 (Aneks 4) — regulator
homeostatyczny CLOS v0.11 nie wyprowadza systemu z nasycenia entropii w oknie
`recurring_shock_world` (88.4% cenzurowania, zweryfikowane bezpośrednio w
trajektorii, nie założone). Poprawną reakcją NIE było poprawienie
`regulate()`, żeby K3b "zadziałała" — to byłoby dokładnie modyfikacją Core w
celu uzyskania oczekiwanego zachowania. Poprawną reakcją było zawieszenie
K3b (status ARCHITECTURE-LIMITED) do CLOS v0.12.

---

## D-017 (zasada wyprowadzona: źródło prawdy)

Źródłem prawdy jest **implementacja**, nie jej model matematyczny.

Wielkości wyprowadzane z definicji środowiska (podłogi szumu, rozkłady, momenty)
liczy się **z kodu środowiska**, wykonując go (próbkowanie/symulacja), **nie ze wzoru**
opisującego idealizację tego kodu — chyba że wzór jest **zweryfikowany krok po kroku**
przeciwko implementacji (patrz `analiza_floor_model_2026-07-28.md` §7, trzy kroki
weryfikacji D-017: (1) poprawność matematyczna modelu, (2) poprawność implementacji
generatora, (3) **czy implementacja zachowuje założenia wyprowadzenia** — krok, który
w tym repo faktycznie zawiódł raz, patrz §5 poniżej).

**Precedens, który ustanowił tę zasadę:** `E|N(0,σ²)|=σ√(2/π)` jest poprawnym wzorem
dla **nieobciętego** rozkładu normalnego — ale `clos_world/generators.py:20` obcina
wyjście do `[0,1]`, więc rozkład produkowany przez generator jest normalnym **uciętym**,
nie normalnym. Krok 3 D-017 (czy implementacja zachowuje założenia wzoru) zawiódł
cicho, dopóki nie sprawdzono go wprost.

---

## §5 Test historyczny

Reguła G-001 stosowana retroaktywnie do trzech rzeczywistych decyzji tego projektu —
żeby nie była martwą literą, tylko sprawdzalnym kryterium.

### shock_world (Primary Endpoint w W1) → **Typ M**

- **Warunek 1 spełniony:** Aneks 3 §1.1 dowodzi formalnie, że redukcja W1 w
  `shock_world` jest **systematycznie nieosiągalna** (`W_late≥0.113`, `W_early→0` gdy
  okno przedwstrząsowe) — wynik testu jest **taki sam niezależnie od tego, czy
  mechanizm PC istnieje**. Endpoint nie mierzy hipotezy, mierzy zmianę trudności
  świata (Aneks 3 §2).
- **Warunek 2 spełniony:** skoro wynik jest strukturalnie zdeterminowany niezależnie
  od hipotezy, nie ma **żadnej** poprawnej interpretacji wyniku względem PC.
- **Traktowanie:** weszło do bieżącego protokołu — Primary Endpoint przeniesiony do
  `noise_world` (W2, Aneks 3 §5), `shock_world` zredukowany do roli kontroli K3.

### Podłoga analityczna (`σ√(2/π)` jako `floor_env`) → **Typ M**

- **Warunek 1 spełniony:** użycie błędnej (o ~2× zawyżonej dla `noise_world`) podłogi
  jako odjemnika w `PE_red(t)=max(0,PE(t)-floor_env)` systematycznie zniekształca
  `redukcja_W2` dla **każdego** przebiegu, niezależnie od prawdziwości hipotezy PC —
  to nie pogorszenie precyzji, to zły przedmiot pomiaru (D-017).
- **Warunek 2 spełniony:** `PE_red`/`redukcja_W2` liczone na błędnej podłodze są
  przesunięte o nieznaną, systematyczną wielkość — nie da się ich poprawnie
  zinterpretować bez przeliczenia.
- **Traktowanie:** weszło do bieżącego protokołu — wyprowadzenie zmienione z
  analitycznego na numeryczne (`clos_world/floor_model.py`) **przed** uruchomieniem
  jakiegokolwiek pilota czy eksperymentu (złapane w fazie projektowania).

### K7 / T7 (gałąź awaryjna `predict()`) → **Typ I**

- **Warunek 1 NIE spełniony:** T7/K7 nie unieważniają Primary Endpointu ani reguły
  decyzyjnej — Aneks 2 stwierdza wprost "reguła pozostaje 9-warunkowa... K7 NIE
  WCHODZI do niej". Główny test nadal mierzy hipotezę.
- **Warunek 2 NIE spełniony:** istnieje poprawna interpretacja — K7 jest jawnie
  oznaczone jako "oszacowanie dolne, heurystyka" z progami interpretacyjnymi
  (20%/50%, Aneks 2 Zmiana 7) pozwalającymi poprawnie zinterpretować K6 w jego
  świetle.
- **Traktowanie:** **ani** warunek 1, **ani** 2 nie jest spełniony (G-001 wymaga
  OBU jednocześnie dla Typu M) → Typ I. Dopisane jako pomiar raportowany w
  dokumentacji PC-001 (Aneks 2), nie jako dziewiąty/dziesiąty warunek decyzyjny.
  **Uwaga proceduralna:** Typ I "trafia do następnego eksperymentu, nie zatrzymuje
  bieżącego" — tu bieżący eksperyment jeszcze nie wystartował (Hard Halt aktywny,
  zero danych), więc "dopisanie do bieżącego protokołu" nie jest wyjątkiem od reguły:
  nic nie zostało przerwane, bo nic jeszcze nie trwało.

## §6 Test historyczny — G-003 (obowiązkowy przykład, jak przy G-001)

### K3b (Kendall tau na `recovery_i`), zaprojektowana w Aneksie 1

Zastosowanie sześciu punktów G-003 retroaktywnie do kontroli, która **już przeszła
przez cały proces projektowy** zanim luka została zauważona:

| Punkt | Ocena |
|---|---|
| 1. Formalna definicja matematyczna | **spełniony** |
| 2. Hipoteza falsyfikowalna | **spełniony** |
| 3. Plan analizy mocy | **spełniony** |
| 5. Gwarancja mechaniczna chroniąca ślepotę | **spełniony** |
| 6. Klasyfikacja typu danych | `recovery_i` = **DANE EKSPERYMENTALNE** (jest wynikiem samej kontroli K3b, nie parametrem uciążliwym z pilota ani ze środowiska) |
| 4. Dowód, że analiza mocy nie wymaga ujawnienia wyniku | **NIESPEŁNIONY** — konsekwencja wprost z pkt 6: skoro `recovery_i` jest danymi eksperymentalnymi, zaplanowanie mocy testu na `recovery_i` wymagałoby najpierw go zmierzyć |

**Kiedy problem faktycznie wykryto:** dopiero przy projektowaniu pilota B4b —
**sześć tur** po zaprojektowaniu kontroli w Aneksie 1 (przez Aneks 1 → B2 → B3 →
B4a → Aneks 3/W2 → B4a-2 → próba B4b), mimo że punkty 1/2/3/5 były przez cały
ten czas poprawnie spełnione i nic w nich tego nie sygnalizowało.

**Dlaczego punkt 6 to zmienia:** z punktem 6 w miejscu problem byłby widoczny
**natychmiast** przy projektowaniu kontroli — klasyfikacja "`recovery_i` = dane
eksperymentalne" jest **mechaniczna** (sama definicja tego, co się mierzy, mówi,
skąd te dane pochodzą), nie wymaga przeprowadzenia analizy mocy, żeby zauważyć
sprzeczność z punktem 4. To jest różnica między regułą wymagającą doświadczenia/
osądu, żeby zauważyć problem po fakcie, a regułą wymagającą wyłącznie
mechanicznej klasyfikacji, żeby zauważyć go z góry.
