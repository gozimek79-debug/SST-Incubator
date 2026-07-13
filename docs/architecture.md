# Architektura: Execution Pipeline / Observation Pipeline

**Status: zasada trwała, obowiązująca od v0.10 (SPRINT_v0.10.md, Warunek 6
CTO). Nie jest to propozycja do zatwierdzenia jak `docs/spec_partial_step.md`
— jest już wdrożona i zweryfikowana; ten dokument opisuje istniejący,
działający podział, żeby przyszłe zmiany miały jeden punkt odniesienia.**

---

## 1. Podział

Projekt dzieli się formalnie na dwie warstwy:

- **Execution Pipeline:** `clos_world/` (World) · `clos_brain/` (Brain,
  Core, behavior frozen) · `clos_kernel/` (Kernel, Core, behavior frozen) ·
  `clos_academy/` (Lesson — orkiestruje World+Brain, nie Core, ale
  eksperymentalnie krytyczna).
- **Observation Pipeline:** `clos_kernel/snapshot_engine.py` (Snapshot
  Engine) · `clos_scientist/` (Capability Analyzer, Competency Profile,
  metryki, telemetria) · CI (walidatory) · `clos_studio/panel/` (Dashboard).

> **Observation Pipeline NIGDY nie wpływa na Execution Pipeline.**

## 2. Test poprawności (falsyfikowalny, nie wybór API)

**Jeśli można całkowicie usunąć Snapshot Engine (lub dowolny inny element
Observation Pipeline) i WSZYSTKIE wyniki Execution Pipeline pozostają
bajtowo identyczne — architektura jest poprawna.**

Snapshot Engine jest **Read-Only Observer**: nie wpływa na Brain, World,
Kernel, RNG ani harmonogram wykonania. To rozszerza inwariant "Behavior
Frozen" z `BrainRuntime.step()` (v0.9, SPRINT_v0.9.md) na cały harness
eksperymentalny — nie tylko Core ma chronione zachowanie, cała ścieżka
Execution ma.

**Jak to sprawdzić w praktyce (przykład: L1.1, `docs/spec_snapshot_observer.md`):**

1. Dodaj addytywny przełącznik (`observe: bool`) kontrolujący WYŁĄCZNIE
   wywołanie obserwatora — nic więcej w kodzie się nie zmienia.
2. Uruchom identyczną macierz eksperymentu z `observe=True` i
   `observe=False`.
3. Podziel pola wyniku na dwie rozłączne kategorie:
   - **Execution** — liczone WYŁĄCZNIE z `world.step()`/`brain_rt.step()`/
     ich pochodnych, przed jakimkolwiek dostępem do danych obserwatora.
   - **Observation** — jawnie zdefiniowane jako `f(snapshots)` (np.
     `stability_score`, `adaptation_tick` — patrz `clos_scientist/analyzer.py`,
     `clos_scientist/metrics.py`).
4. Pola Execution MUSZĄ być bajtowo identyczne między `observe=True` i
   `observe=False`. Pola Observation MOGĄ (i zwykle będą) się różnić — to
   nie jest naruszenie zasady, to jest dokładnie to, co Observation
   Pipeline ma robić.
5. Sformalizuj to jako test regresyjny w CI (patrz
   `tests/test_observer_removability.py`) — dowód jednorazowy nie chroni
   przed przyszłą regresją.

## 3. Dlaczego nie wystarczy "wygląda na czyste"

Kandydat na Read-Only Observer, który WYGLĄDA nieszkodliwie, może naruszyć
zasadę na kilka sposobów, które test w §2 wyłapuje, a przegląd kodu
niekoniecznie:

- **Zmiana momentu poboru RNG.** Jeśli obserwator wywołuje cokolwiek, co
  konsumuje globalny stan losowości (`random.seed()`/`random.random()`)
  między krokami Execution, kolejne wywołania Execution dostają inny stan
  RNG niż bez obserwatora — w systemie deterministycznym to zmienia wynik
  liczbowy, nie tylko telemetrię.
- **Zmiana kolejności aktualizacji.** Przepięcie pętli eksperymentu na
  wspólną metodę sterującą (np. `Kernel.run_tick()`) zamiast dodania
  obserwacji OBOK istniejących wywołań tworzy nową, równoległą ścieżkę
  wykonania — nawet jeśli ma dawać "to samo", każda różnica w kolejności
  wywołań (Scheduler, EventBus, Lifecycle) jest realną zmianą zachowania,
  nie kosmetyką.
- **Propagacja błędu przez efekt uboczny.** Obserwator, który mutuje
  współdzielony obiekt (zamiast tylko go odczytywać i zapisywać do
  WŁASNEJ, odizolowanej struktury jak `SnapshotEngine._snapshots`), może
  wpłynąć na przyszłe odczyty tego obiektu przez Execution.

Konkretny przykład z tego projektu (SPRINT_v0.10.md P1): `Kernel.run_tick()`
tworzy snapshot, ale z **zaszytymi na sztywno wartościami**
(`entropy=0.0, energy=100.0`, [clos_kernel/kernel.py:98](../clos_kernel/kernel.py))
niezależnymi od faktycznego stanu `tissue` — architektonicznie nie ma
dostępu do obiektu używanego przez lekcję. Naiwne przepięcie lekcji na
`run_tick()` "żeby snapshoty wreszcie powstawały" dałoby ORAZ zmienioną
ścieżkę wykonania, ORAZ nadal bezwartościowe dane. Poprawne rozwiązanie:
obserwator woła bezpośrednio `SnapshotEngine.create_snapshot()` z
**realnych** wartości już obliczonych przez Execution (`tissue.entropy`,
`tissue.energy`), jedną dodatkową linią OBOK istniejących wywołań — nie
zamiast nich.

## 4. Co to NIE znaczy

- Nie znaczy, że Observation Pipeline nie może CZYTAĆ stanu Execution —
  musi, żeby cokolwiek zmierzyć. Granica jest jednokierunkowa: Observation
  czyta z Execution, nigdy nie pisze do niego ani nie zmienia jego
  sekwencji wywołań.
- Nie znaczy, że Observation Pipeline jest "mniej ważny" albo nie wymaga
  tego samego rygoru — `scripts/validate_observability.py` (v0.10 P5)
  blokuje scalenie przy uszkodzonej/niekompletnej telemetrii dokładnie
  tak samo, jak `validate_artifacts.py` blokuje przy niespójności z
  prerejestracją.
- Nie znaczy, że każda przyszła zmiana w `clos_scientist/`/`clos_studio/`
  wymaga dowodu usuwalności — tylko zmiany, które DOŁĄCZAJĄ się do pętli
  Execution (jak Snapshot Engine). Czysto downstream'owa analiza
  (Capability Analyzer czytający już-zapisane raporty) nie dotyka
  Execution i nie wymaga tego testu.

## 5. Powiązane dokumenty

- [docs/spec_snapshot_observer.md](spec_snapshot_observer.md) — projekt i
  dowód usuwalności dla konkretnej implementacji (L1.1/L1.2).
- [RAPORT_v0.10.md](../RAPORT_v0.10.md) — pełny raport sprintu, w tym
  dwuwarstwowa diagnoza długu i realne Adaptation/Stability z klasyfikacją
  A/B/C.
- `SPRINT_v0.9.md` — poprzedni inwariant ("Behavior Frozen" dla `step()`),
  którego to jest rozszerzeniem na cały harness.
