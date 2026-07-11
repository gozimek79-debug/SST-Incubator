# IDIO-MORPH — hipoteza badawcza (v0.9)

**Status: OFICJALNA HIPOTEZA BADAWCZA. Zero kodu produkcyjnego w tym
sprincie i żadnym dotychczasowym.** Ten dokument nie jest specyfikacją do
implementacji (jak `docs/spec_partial_step.md`) — jest zbiorem czterech
pytań badawczych, które CLOS mógłby kiedyś testować, gdyby ktoś podjął
decyzję o rozpoczęciu tej pracy. Nie projektujemy pod IDIO-MORPH
spekulacyjnie — patrz §2.

Nazwa robocza: **IDIO**syncratic **MORPH**ic representation — cztery
kierunki łączy pytanie, czy reprezentacja wewnętrzna Brain musi być
jednolita i statyczna (jak jest dziś), czy może być zmienna w czasie i
swoista dla danej instancji.

---

## 1. Cztery kierunki (pytania badawcze, nie zadania)

Każdy kierunek jest sformułowany jako pytanie i zakotwiczony w
KONKRETNYM, obecnym ograniczeniu architektonicznym — nie w abstrakcji.

### 1.1 Dynamiczne kodowanie reprezentacji

**Obecny stan:** `_hash_stimulus()`
([clos_brain/runtime/prediction.py:61](../clos_brain/runtime/prediction.py))
dyskretyzuje ciągły bodziec `[0,1]` na **stałą** liczbę 100 kubełków,
identyczną dla każdego Brain, każdego genomu, przez cały czas życia.

**Pytanie badawcze:** Czy granularność/schemat kodowania bodźca mógłby
zmieniać się w czasie (np. zagęszczać się wokół często obserwowanych
wartości, rozrzedzać wokół rzadkich) zamiast być jednym, sztywnym
podziałem na 100 równych przedziałów przez całe życie Brain?

### 1.2 Morficzna kompresja informacji

**Obecny stan:** `BrainTissue.memory`
([clos_brain/tissue.py](../clos_brain/tissue.py)) to płaska lista
`MemoryRecord`, ograniczona `memory_capacity`; przy przepełnieniu
`update_memory()`
([clos_brain/runtime/plasticity.py:57](../clos_brain/runtime/plasticity.py))
usuwa rekord o najstarszym `timestamp_tick` — wiek, nie treść, decyduje o
przetrwaniu śladu.

**Pytanie badawcze:** Czy podobne/nadmiarowe ślady pamięciowe mogłyby się
łączyć/kompresować semantycznie (np. uśredniać zamiast konkurować o miejsce
1:1) zamiast konkurować wyłącznie wiekiem o stałą liczbę slotów?

### 1.3 Idiosynkratyczne reprezentacje semantyczne

**Obecny stan:** `_hash_stimulus()` jest funkcją **uniwersalną** — dwa
różne Brainy (różne genomy, różna historia) reprezentują TEN SAM bodziec
identycznym kubełkiem. Reprezentacja wewnętrzna nie zależy od tożsamości
ani historii instancji.

**Pytanie badawcze:** Czy każda instancja Brain mogłaby wykształcić własne,
rozbieżne odwzorowanie bodziec→reprezentacja, kształtowane przez jej
unikalną historię/genom, zamiast dzielić jedno, uniwersalne kodowanie z
każdym innym Brainem?

### 1.4 Metaboliczna optymalizacja pamięci

**Obecny stan:** `regulate()`
([clos_brain/runtime/homeostasis.py:20](../clos_brain/runtime/homeostasis.py))
odejmuje **stały** koszt energetyczny (`energy_decay = 0.001`/tick),
niezależny od `len(brain.memory)` czy złożoności utrzymywanych
reprezentacji. Utrzymanie 1 śladu pamięciowego kosztuje tyle samo, co
utrzymanie `memory_capacity` śladów.

**Pytanie badawcze:** Czy koszt energetyczny mógłby skalować się z
rozmiarem/złożonością pamięci (prawdziwy koszt metaboliczny utrzymania
reprezentacji), tworząc presję w stronę zwięzłych/skompresowanych
reprezentacji, zamiast płaskiego podatku niezależnego od obciążenia
poznawczego?

---

## 2. Nota o zgodności architektonicznej (NEGATYWNA — nie zadanie)

**Wymóg z SPRINT_v0.9.md: architektura v0.9 nie może zamykać drogi do
powyższych czterech kierunków. Nie oznacza to projektowania pod nie z
wyprzedzeniem — tylko sprawdzenie, że nic dodanego w tym sprincie tego nie
blokuje.**

- **`BrainRuntime.partial_step()`**
  ([clos_brain/brain_runtime.py](../clos_brain/brain_runtime.py),
  `docs/spec_partial_step.md`) przyjmuje `skip: Iterable[PipelineStep]` z
  zamkniętego, ale **rozszerzalnego** enuma `PipelineStep`. Dodanie
  nowego, ósmego kroku pipeline'u (np. hipotetyczny krok "reencode" dla
  §1.1) nie wymagałoby przebudowy `partial_step()` — enum i mechanizm
  certyfikacji (`_CERTIFIED_SKIPPABLE`) są zaprojektowane tak, by rosnąć
  addytywnie. `partial_step()` NIE zakłada, że pipeline ma dokładnie 7
  kroków na stałe — zakłada tylko, że jakikolwiek krok można nazwać i
  opcjonalnie pominąć.
- **`CapabilityAnalyzer` (relacja N:M)**
  ([clos_scientist/capability_analyzer.py](../clos_scientist/capability_analyzer.py))
  mapuje pojęcie → lista lekcji. Nowe pojęcie poznawcze (np.
  "Representational Idiosyncrasy" dla §1.3, gdyby kiedyś powstała lekcja
  je mierząca) wymagałoby wyłącznie dopisania wpisu do
  `CONCEPT_METRIC_MAP` i odpowiadającej definicji w
  `cognitive_ontology.md` — dokładnie tak, jak dodano "Homeostatic
  Resilience" w tym sprincie. Architektura NIE zakłada stałej listy 14
  pojęć.
- Żadne z powyższych nie zostało zbudowane z myślą o IDIO-MORPH — to
  efekt uboczny wcześniejszych decyzji (addytywność `partial_step()` z
  P2, N:M z P6 Odkrycia #1). Nota potwierdza brak blokady, nie planuje
  przyszłej pracy.

## 3. Co jest jawnie POZA zakresem

- Implementacja jakiegokolwiek z czterech kierunków.
- Zmiana `_hash_stimulus()`, `update_memory()`, `regulate()` ani
  jakiegokolwiek innego pliku w `clos_brain/`.
- Nowe geny, neurony, struktury pamięci.
- Harmonogram/priorytetyzacja, który kierunek badać pierwszy — to decyzja
  poza tym dokumentem.
