# Governance Rules — wiążące zasady procesowe

**Status: WIĄŻĄCE.** Nie deklaracja intencji — reguły stosowane retroaktywnie do
konkretnych decyzji tego projektu (patrz §5 "Test historyczny").

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
